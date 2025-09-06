import stable_whisper
import json
from typing import List, Dict, Any

# --- Constantes ---
MODEL_NAME = "base"
AUDIO_FILE = "leia.flac"
OUTPUT_JSON_RAW = 'demo.json'
OUTPUT_JSON_FINAL = 'final.json'

# Copia y pega la letra de tu canción aquí
LYRICS = """
君の声を聞かせて 澱む心を祓って
偽りのキャンバスを 塗りつぶしてくんだ
今日も

終末のない幻想に 触れた気がした
「なんて呼べばいいんだろう」 変わらない温度
微笑が内臓を 食いつぶす前に
今日を閉じ込めたよ 馳せる未来は灰色

望むなら空想 寂れた嘘
叶うならもっと 聞かせて

心から溢れてた 愛しさをちりばめて
君の声に重ねた 恍惚は遥か
形あるものならば 崩れゆくものならば
この両目は要らない 僕を包んで
Leia...

終末のない幻想は 悲しく笑った
「なんて呼べばいいんだろう」 響く言葉は灰色

永遠はそっと 息をとめて
僕を置いてった 絶望へと

針の音が止まれば この世界は終わるよ
願うだけの言葉は 意味をもたなかった
もう少しだけ笑って もう少しだけ祈って
聞こえないならもういっそ 僕を殺してよ

君の声を聞かせて 澱む心を祓って
偽りのキャンバスを 君と葬るんだ
君と僕の証を 残す術がないなら
温もりを焼きつけて 僕を殺して

Leia...

Leia...
"""

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

    for line in lyrics_lines:
        line = line.strip()
        if not line:
            # Para líneas vacías, usamos el tiempo final de la línea anterior.
            final_result.append({
                'linea': '',
                'start': previous_end_time,
                'end': previous_end_time
            })
            continue

        try:
            start_time = word_timestamps[word_idx]['start']
            chars_in_line = len(line.replace(' ', ''))
            chars_consumed = 0

            while chars_consumed < chars_in_line and word_idx < len(word_timestamps):
                word = word_timestamps[word_idx]['word'].replace(' ', '')
                chars_consumed += len(word)
                word_idx += 1

            # El tiempo de fin es el de la última palabra que forma parte de la línea.
            end_time = word_timestamps[word_idx - 1]['end']

            final_result.append({
                'linea': line,
                'start': start_time,
                'end': end_time
            })
            previous_end_time = end_time

        except IndexError:
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
    diccionario de línea basado en el tiempo 'start'. Modifica la lista in-place.
    """
    for item in line_data:
        start_time = item.get('start')

        if start_time is None:
            item['minutes'] = None
            item['seconds'] = None
            item['milliseconds'] = None
            continue

        minutes = int(start_time / 60)
        remaining_seconds = start_time % 60
        seconds = int(remaining_seconds)
        milliseconds = int(round((remaining_seconds - seconds) * 1000))

        item['minutes'] = minutes
        item['seconds'] = seconds
        item['milliseconds'] = milliseconds

    return line_data


def save_to_json(data: List[Dict[str, Any]], file_path: str) -> None:
    """Guarda una lista de diccionarios en un archivo JSON."""
    print(f"Guardando resultado en '{file_path}'...")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def main() -> None:
    """
    Función principal que orquesta el proceso de alineación de letras y audio.
    """
    # Paso 1: Cargar el modelo
    model = load_model(MODEL_NAME)

    # Paso 2: Alinear audio y letra
    alignment_result = align_lyrics(model, AUDIO_FILE, LYRICS, language='ja')

    # Opcional: Guardar el resultado de alineación crudo
    alignment_result.save_as_json(OUTPUT_JSON_RAW)

    # Paso 3: Extraer todas las palabras de todos los segmentos
    alignment_dict = alignment_result.to_dict()
    all_words: List[Dict[str, Any]] = []
    if 'segments' in alignment_dict['ori_dict']:
        for segment in alignment_dict['ori_dict']['segments']:
            all_words.extend(segment.get('words', []))

    if not all_words:
        print("No se encontraron palabras en el resultado de la alineación. Abortando.")
        return

    # Paso 4: Generar timestamps por cada línea de la letra original
    lyrics_lines = LYRICS.strip().split('\n')
    line_timestamps = generate_line_timestamps(lyrics_lines, all_words)

    # Paso 5: Agregar tiempos desglosados para cada línea
    processed_list = add_detailed_timestamps(line_timestamps)

    # Paso 6: Guardar el resultado final
    save_to_json(processed_list, OUTPUT_JSON_FINAL)

    print("\nEl proceso ha terminado con éxito.")


if __name__ == "__main__":
    main()
