import os
import google.generativeai as genai
from dotenv import load_dotenv
from pandas import DataFrame
from pykakasi import kakasi
import argparse


load_dotenv()
api_key_genai=os.getenv('API_KEY_GENAI')
id_folder=os.getenv('ID_FOLDER')

# Configure your Gemini API key
genai.configure(api_key=api_key_genai)

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

gauth = GoogleAuth()
# This will open a web browser for authentication the first time.
# It will save credentials to a file for subsequent runs.
gauth.LocalWebserverAuth()

drive = GoogleDrive(gauth)

def convert_to_romaji(japanese_text: list) -> list:
    """Converts a list of Japanese strings to Romaji."""
    kks = kakasi()
    # Convert each line in the list more cleanly
    return [' '.join(word['hepburn'] for word in kks.convert(line)) for line in japanese_text]


def translate_lyrics(japanese_lyrics: str) -> list:
    """
    Gets the English translation from Gemini.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
Below are song lyrics in Japanese.
Your task is to provide an English translation. Ensure it is accurate and, most importantly, captures the feeling and context of the original lyrics.
Maintain the original line-by-line format and line breaks.
Provide only the translation, without any additional text or explanations.

Japanese Lyrics:
---
{japanese_lyrics}
---
    """

    response = model.generate_content(prompt)
    translated_text = response.text.strip()
    english_lines = translated_text.strip().split('\n')
    return english_lines


def review_and_improve_translation(lyrics_to_review: str) -> list:
    """
    Reviews and improves a Japanese-to-English song translation.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
Below are song lyrics in Japanese, along with an English translation.
Your task is to analyze the English translation to determine if it is accurate and, most importantly, if it captures the feeling and context of the original lyrics.

If the translation is too literal, propose an improved version that sounds more natural to an English speaker and conveys the song's emotion.

Maintain the original line-by-line format and line breaks.
Only the improved translation is required; omit the Japanese.
Provide only the improvement, without any additional text or explanations.
The same number of lines must be maintained.

Lyrics to review:
---
{lyrics_to_review}
---
"""
    response = model.generate_content(prompt)
    translated_text = response.text.strip()
    english_lines = translated_text.strip().split('\n')
    return english_lines


def create_dataframe(lyrics_jap: list, lyrics_rom: list, lyrics_eng: list, lyrics_eng_improved: list) -> DataFrame:
    """Creates a pandas DataFrame from the lyric lists."""
    data = []
    # Ensure all lists have the same length for zipping
    max_len = len(lyrics_jap)
    for i in range(max_len):
        japanese = lyrics_jap[i].strip()
        romaji = lyrics_rom[i].strip() if i < len(lyrics_rom) else ""
        english = lyrics_eng[i].strip() if i < len(lyrics_eng) else ""
        english_improved = lyrics_eng_improved[i].strip() if i < len(lyrics_eng_improved) else ""
        data.append([japanese, romaji, english, english_improved])

    df = DataFrame(data, columns=['Japanese', 'Romaji', 'English', 'Improved English'])
    return df


def save_to_csv(dataframe: DataFrame, filename: str):
    """
    Saves a pandas DataFrame to a CSV file.
    """
    dataframe.to_csv(filename, index=False, header=True, encoding='utf-8')
    print(f"The translation has been successfully saved to '{filename}'.")

def combine_jap_eng_for_prompt(lyrics_jap: list, lyrics_eng: list) -> str:
    """Combines the Japanese and English lyrics line-by-line for the review prompt."""
    # Using zip and a list comprehension is more efficient and Pythonic.
    combined_lines = [f"{jap}\t{eng}" for jap, eng in zip(lyrics_jap, lyrics_eng)]
    return "\n".join(combined_lines)

# Main workflow function
def process_song(full_lyrics: str, output_filepath: str):
    # Step 1: Get Japanese and Romaji
    lyrics_jap = full_lyrics.strip().split('\n')
    print('Converting to Romaji...')
    lyrics_rom = convert_to_romaji(lyrics_jap)

    # Step 2: Get initial translation
    print('Translating song to English...')
    lyrics_eng = translate_lyrics(full_lyrics)
    
    # Step 3: Combine Japanese and English for the improvement prompt
    lyrics_to_review = combine_jap_eng_for_prompt(lyrics_jap, lyrics_eng)

    # Step 4: Get improved translation
    print('Improving translation...')
    lyrics_eng_improved = review_and_improve_translation(lyrics_to_review)

    # Step 5: Generate and save the DataFrame
    print('Generating DataFrame...')
    df_lyrics = create_dataframe(lyrics_jap, lyrics_rom, lyrics_eng, lyrics_eng_improved)
    print('Generating CSV...')
    save_to_csv(df_lyrics, output_filepath)
    print("Process complete and saved to CSV file.")

def upload_to_google_drive(local_filepath: str, drive_filename: str, folder_id: str):
    """Uploads a file to a specific Google Drive folder and converts it."""
    print("Creating Google Drive file...")
    file_drive = drive.CreateFile({
        'title': drive_filename,
        'parents': [{"id": folder_id}]
    })
    print("Setting content...")
    file_drive.SetContentFile(local_filepath)
    print("Uploading file...")
    file_drive.Upload({"convert": True}) # convert=True will turn CSV into a Google Sheet
    print(f"Upload complete. Link: {file_drive['alternateLink']}")

def read_lyrics_file(filepath: str) -> str:
    """Reads the content of a text file."""
    print(f"Reading lyrics from '{filepath}'...")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def main():
    """Main function to run the lyric translation workflow."""
    parser = argparse.ArgumentParser(description="Translate and process Japanese song lyrics.")
    parser.add_argument("lyrics_file", help="Path to the text file with the Japanese lyrics.")
    parser.add_argument("song_name", help="Name of the song to use for the output file.")
    parser.add_argument("-o", "--output", default=None, help="Base name for the output file (without extension). Defaults to the song name.")
    args = parser.parse_args()

    output_filename_base = args.output if args.output else args.song_name
    csv_filename = f'{output_filename_base}.csv'

    # Read the lyrics from the provided file
    lyrics_jap_full = read_lyrics_file(args.lyrics_file)

    # Process the song
    process_song(lyrics_jap_full, csv_filename)

    # Upload the resulting file to Google Drive
    upload_to_google_drive(csv_filename, args.song_name, id_folder)

if __name__ == "__main__":
    main()
