import os
import google.generativeai as genai
from dotenv import load_dotenv
from pandas import DataFrame
from pykakasi import kakasi


load_dotenv()
api_key_genai=os.getenv('API_KEY_GENAI')
id_folder=os.getenv('ID_FOLDER')

# Configura tu clave de API de Gemini
genai.configure(api_key=api_key_genai)

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()

drive = GoogleDrive(gauth)

def convertir_a_romaji(texto_japones: list) -> list:
    kks = kakasi()
    # Se puede convertir cada línea de la lista de forma más limpia
    return [' '.join(word['hepburn'] for word in kks.convert(linea)) for linea in texto_japones]


def traducir_letra(letra_japones) -> list:
    """
    Obtiene la traducción en inglés de Gemini y la combina con el romaji generado.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
A continuación, se presenta una letra de canción en japonés.
Tu tarea es hacer la traducción en inglés y determinar si es precisa y, sobre todo, si captura el sentimiento y el contexto de la letra original.
Mantén el formato de cada línea y los saltos de línea originales. 
Proporciona solo la traducción, sin ningún texto adicional o explicaciones.

Letra en japonés:
---
{letra_japones}
---
    """

    response = model.generate_content(prompt)
    texto_traducido = response.text.strip()
    # 3. Combinar los resultados en un DataFrame
    lineas_ingles = texto_traducido.strip().split('\n')
    return lineas_ingles


def revisar_y_mejorar_traduccion(letra) -> list:
    """
    Revisa y mejora una traducción de canción de japonés a inglés.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
A continuación, se presenta una letra de canción en japonés, y una traducción al inglés.
Tu tarea es analizar la traducción en inglés y determinar si es precisa y, sobre todo, si captura el sentimiento y el contexto de la letra original.

Si la traducción es literal, propón una versión mejorada que suene más natural para un hablante de inglés y que transmita la emoción de la canción.


Mantén el formato de cada línea y los saltos de línea originales. 
Solo se requiere la traduccion mejorada, el japones omitelo.
Proporciona solo la mejora, sin ningún texto adicional o explicaciones.
Se debe de mantener la misma cantidad de lineas
Letra a revisar:
---
{letra}
---
"""
    response = model.generate_content(prompt)
    texto_traducido = response.text.strip()
    # 3. Combinar los resultados en un DataFrame
    lineas_ingles = texto_traducido.strip().split('\n')
    return lineas_ingles


def generate_df(lyrics_jap: list, lyrics_rom: list, lyrics_eng: list, lyrics_eng_improved: list) -> DataFrame:
    datos = []
    # Asegurarse de que las listas tengan la misma longitud
    for i in range(len(lyrics_jap)):
        japones = lyrics_jap[i].strip()
        romaji = lyrics_rom[i].strip()
        ingles = lyrics_eng[i].strip() if i < len(lyrics_eng) else ""
        english_impr = lyrics_eng_improved[i].strip() if i < len(lyrics_eng) else ""
        datos.append([japones, romaji, ingles, english_impr])

    df = DataFrame(datos, columns=['Japonés', 'Romaji', 'Inglés', 'Ingles Mejorado'])
    return df


def guardar_en_csv(dataframe: DataFrame, nombre_archivo: str):
    """
    Guarda un DataFrame de pandas en un archivo de Excel.
    """
    dataframe.to_csv(nombre_archivo, index=False, header=True, sep='|')
    print(f"La traducción ha sido guardada en '{nombre_archivo}' con éxito.")

def guardar_en_xlsx(dataframe: DataFrame, nombre_archivo: str):
    """
    Guarda un DataFrame de pandas en un archivo de Excel.
    """
    dataframe.to_excel(nombre_archivo, index=False, header=True)
    print(f"La traducción ha sido guardada en '{nombre_archivo}' con éxito.")

def join_jap_eng(lyr_jap: list, lyr_eng: list) -> str:
    lyrics_jap_eng: str = ''
    for i in range(len(lyr_jap)):
        combined_line: str = lyr_jap[i] + '\t' + lyr_eng[i]
        lyrics_jap_eng = lyrics_jap_eng + '\n' + combined_line
    return lyrics_jap_eng

# Crea una función principal para el flujo de trabajo
def procesar_cancion(letra_completa, file_output):
    # Paso 1: Obtener japonés y romaji
    lyrics_jap = letra_completa.strip().split('\n')
    print('Convirtiendo a Romaji')
    lyrics_rom = convertir_a_romaji(lyrics_jap)

    # Paso 2: Obtener traducción inicial
    print('Traduciendo cancion al ingles')
    lyrics_eng = traducir_letra(letra_completa)
    print(lyrics_eng)
    
    # Paso 3: Combinar japonés e inglés para la mejora
    pre_lyrics_jap_eng = join_jap_eng(lyrics_jap, lyrics_eng)

    # Paso 4: Obtener traducción mejorada
    print('Mejorando traduccion')
    lyrics_eng_improved = revisar_y_mejorar_traduccion(pre_lyrics_jap_eng)
    print(lyrics_eng_improved)

    # Paso 5: Generar y guardar el DataFrame
    print('Generando parquet')
    df_lyrics = generate_df(lyrics_jap, lyrics_rom, lyrics_eng, lyrics_eng_improved)
    print('Generando CSV')
    # guardar_en_csv(df_lyrics, f'{file_output}.csv')
    # print("Proceso completo y guardado en archivo CSV.")
    guardar_en_xlsx(df_lyrics,f'{file_output}.xlsx')

def subir_a_google_sheets_oficial(file_name,file,id_folder):
    print("Creando Archivo Google")
    file_drive = drive.CreateFile({
        'title':file,
        # 'mimeType': 'application/vnd.google-apps.spreadsheet',
        'parents': [{"id": id_folder}]
    })
    print("Cargando informacion")
    file_drive.SetContentFile(file_name)
    print("Subiendo archivo")
    file_drive.Upload({"convert": True})
    print(f'Link: {file_drive['alternateLink']}')

# Llama a la función principal
lyrics_jap_full = """
あなたが生まれた
事について僕は言う
犠牲と後悔泣き声に
かき消されてるの？
遠くなる
心へと
吐き捨てた

形は無い答えは無い
僕は知ったこっちゃ無い
繊細な絹糸に
黒い雫落ちる
泣き顔に突きつけた
皮肉と優しさが
ただ零れ落ちた
此処にあった
喪失感

あなたが選んだ
世界について僕は言う
暗くて霞んだ目の前の
景色はどう見える？
帰りたい
それだけは許されない

言葉からあふれ出た
偽りの幸せ
泣き出した幸福感
赤く染まる涙
粉々に砕かれる
方がまだ美しい
ただ求め合った
そこにあった
喪失感

僕は泣いた
泣き疲れた
何か消えた

形は無い答えは無い
僕は知ったこっちゃ無い
繊細な絹糸に
黒い雫落ちる
泣き顔に突きつけた
皮肉と優しさが
ただ零れ落ちた
ここにあった
喪失感
"""

song_name:str = 'Yuyoyuppe - For a Dead Girl+'
file_name = f'{song_name}'
procesar_cancion(lyrics_jap_full, file_name)
subir_a_google_sheets_oficial(f'{file_name}.xlsx',song_name,id_folder)

