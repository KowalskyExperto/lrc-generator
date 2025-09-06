import stable_whisper
from typing import List, Dict, Any
from pandas import DataFrame
import argparse

# --- Constantes ---
DEFAULT_MODEL_NAME = "base"

# --- Funciones ---


def load_model(model_name: str) -> Any:
    """Carga un modelo de Stable Whisper."""
    print(f"Cargando el modelo '{model_name}'...")
    model = stable_whisper.load_model(model_name)
    print("Modelo cargado.")
    return model


def align_lyrics(
    model: Any,
    audio_path: str,
    lyrics: str,
    language: str
) -> stable_whisper.WhisperResult:
    """
    Alinea el audio con la letra proporcionada usando Stable Whisper.
    Realiza un paso de refinamiento para mejorar la precisión.
    """
    print(f"Alineando el audio '{audio_path}' con la letra...")
    # Primera pasada de alineación
    result = model.align(audio_path, lyrics,
                         language=language, suppress_silence=True)
    # Segunda pasada para refinar los timestamps
    result = model.align(audio_path, result,
                         language=language, suppress_silence=True)
    print("Alineación completada.")
    return result


def generate_line_timestamps(
    lyrics_lines: List[str],
    word_timestamps: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Genera timestamps de inicio y fin para cada línea de la letra, basándose en los
    timestamps de las palabras individuales.
    """
    print("Generando timestamps por línea...")
    final_result: List[Dict[str, Any]] = []
    word_idx = 0
    previous_end_time = 0.0

    for original_line in lyrics_lines:
        line = original_line.strip()
        if not line:
            # Para líneas vacías, usamos el tiempo final de la línea anterior.
            final_result.append({
                'linea': '', # Keep empty lines for structure
                'start': previous_end_time,
                'end': previous_end_time
            })
            continue

        try:
            line_words = []
            reconstructed_line = ""
            
            # Consume words from the list until the reconstructed line matches the original line
            temp_word_idx = word_idx
            clean_line = line.replace(" ", "")

            while temp_word_idx < len(word_timestamps):
                word_obj = word_timestamps[temp_word_idx]
                word_text = word_obj['word'].strip()
                
                # Check if adding the next word still forms a prefix of the clean line
                if clean_line.startswith(reconstructed_line + word_text):
                    reconstructed_line += word_text
                    line_words.append(word_obj)
                    temp_word_idx += 1
                    if reconstructed_line == clean_line:
                        break # Found all words for this line
                else:
                    break # Word doesn't match, move to next line

            final_result.append({
                'linea': original_line,
                'start': line_words[0]['start'],
                'end': line_words[-1]['end']
            })
            previous_end_time = line_words[-1]['end']
            word_idx = temp_word_idx # Update main index
        except (IndexError, KeyError):
            print(
                f"Error: La lista de tiempos de palabras no coincide con la letra. Fallo en la línea: '{line}'")
            print(f"Se procesaron {len(final_result)} líneas exitosamente.")
            break

    print("Timestamps por línea generados.")
    return final_result


def add_detailed_timestamps(
    line_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Agrega minutos, segundos y milisegundos desglosados a cada
    diccionario de línea basado en el tiempo 'start' y elimina las claves
    'start' y 'end' originales. Los valores de tiempo se formatean como
    strings con ceros a la izquierda para cumplir con el formato LRC. Devuelve
    una nueva lista.
    """
    processed_data = []
    for item in line_data:
        new_item = item.copy()
        start_time = new_item.get('start')

        if start_time is not None:
            minutes = int(start_time / 60)
            remaining_seconds = start_time % 60
            seconds = int(remaining_seconds)
            milliseconds = int(round((remaining_seconds - seconds) * 1000))

            # Formatear como strings con ceros a la izquierda (ej: 01, 07, 050)
            new_item.update({'minutes': f"{minutes:02d}", 'seconds': f"{seconds:02d}", 'milliseconds': f"{milliseconds:03d}"})

        # Eliminar las claves originales de tiempo en segundos
        if 'start' in new_item:
            del new_item['start']
        if 'end' in new_item:
            del new_item['end']

        processed_data.append(new_item)
    return processed_data


def save_to_csv(data: List[Dict[str, Any]], file_path: str) -> None:
    """Guarda una lista de diccionarios en un archivo CSV usando pandas."""
    if not data:
        print("No hay datos para guardar.")
        return
    print(f"Guardando resultado en '{file_path}'...")
    df = DataFrame(data)
    df.to_csv(file_path, index=False, encoding='utf-8')

def read_lyrics_file(filepath: str) -> str:
    """Lee el contenido de un archivo de texto."""
    print(f"Leyendo letra desde '{filepath}'...")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def main() -> None:
    """
    Función principal que orquesta el proceso de alineación de letras y audio.
    """
    parser = argparse.ArgumentParser(description="Alinear audio con letra usando stable-whisper.")
    parser.add_argument("audio", help="Ruta al archivo de audio.")
    parser.add_argument("lyrics", help="Ruta al archivo de texto con la letra.")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL_NAME, help=f"Nombre del modelo de Whisper (default: {DEFAULT_MODEL_NAME}).")
    parser.add_argument("-o", "--output", default="final.csv", help="Ruta para el archivo CSV de salida (default: final.csv).")
    parser.add_argument("--lang", default="ja", help="Código de idioma de la letra (default: ja).")
    args = parser.parse_args()

    # Leer la letra desde el archivo
    lyrics_text = read_lyrics_file(args.lyrics)

    # Paso 1: Cargar el modelo
    model = load_model(args.model)

    # Paso 2: Alinear audio y letra
    alignment_result = align_lyrics(model, args.audio, lyrics_text, language=args.lang)

    # Opcional: Guardar el resultado de alineación crudo
    # alignment_result.save_as_json('raw_alignment.json')

    # Paso 3: Extraer todas las palabras
    all_words: List[Dict[str, Any]] = []
    for segment in alignment_result.segments:
        for word in segment.words:
            all_words.append({
                'word': word.word,
                'start': word.start,
                'end': word.end
            })

    if not all_words:
        print("No se encontraron palabras en el resultado de la alineación. Abortando.")
        return

    # Paso 4: Generar timestamps por cada línea de la letra original
    lyrics_lines = lyrics_text.strip().split('\n')
    line_timestamps = generate_line_timestamps(lyrics_lines, all_words)

    # Paso 5: Agregar tiempos desglosados para cada línea
    processed_list = add_detailed_timestamps(line_timestamps)

    # Paso 6: Guardar el resultado final
    save_to_csv(processed_list, args.output)

    print("\nEl proceso ha terminado con éxito.")


if __name__ == "__main__":
    main()
