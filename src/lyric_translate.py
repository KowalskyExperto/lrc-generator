import argparse
import google.generativeai as genai
import os
import logging

from dotenv import load_dotenv
from itertools import zip_longest
from pandas import DataFrame
from pykakasi import kakasi

# --- Logger ---
logger = logging.getLogger(__name__)

load_dotenv()

# --- Constants ---
GEMINI_MODEL_NAME = 'gemini-1.5-flash'


def convert_to_romaji(japanese_text: list, kks: kakasi) -> list:
    """Converts a list of Japanese strings to Romaji."""
    return [' '.join(word['hepburn'] for word in kks.convert(line)) for line in japanese_text]


def translate_lyrics(japanese_lyrics: str, model: genai.GenerativeModel) -> list:
    """Gets the English translation from Gemini."""
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
    return translated_text.strip().split('\n')


def review_and_improve_translation(lyrics_to_review: str, model: genai.GenerativeModel) -> list:
    """Reviews and improves a Japanese-to-English song translation."""
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
    return translated_text.strip().split('\n')


def create_dataframe(lyrics_jap: list, lyrics_rom: list, lyrics_eng: list, lyrics_eng_improved: list) -> DataFrame:
    """Creates a pandas DataFrame from the lyric lists."""
    zipped_data = zip_longest(lyrics_jap, lyrics_rom, lyrics_eng, lyrics_eng_improved, fillvalue="")
    data = [[item.strip() for item in row] for row in zipped_data]
    return DataFrame(data, columns=['Japanese', 'Romaji', 'English', 'Improved English'])


def save_to_csv(dataframe: DataFrame, filename: str):
    """Saves a pandas DataFrame to a CSV file."""
    dataframe.to_csv(filename, index=False, header=True, encoding='utf-8')
    logger.info(f"Translation successfully saved to '{filename}'.")


def combine_jap_eng_for_prompt(lyrics_jap: list, lyrics_eng: list) -> str:
    """Combines Japanese and English lyrics line-by-line for the review prompt."""
    return "\n".join([f"{jap.strip()}\t{eng.strip()}" for jap, eng in zip_longest(lyrics_jap, lyrics_eng, fillvalue="")])

# Main workflow functions

def get_translation_data(full_lyrics: str, api_key_genai: str) -> DataFrame:
    """Processes lyrics to generate translations and returns them as a DataFrame."""
    genai.configure(api_key=api_key_genai)
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    kks = kakasi()

    lyrics_jap = full_lyrics.strip().split('\n')
    logger.info('Converting to Romaji...')
    lyrics_rom = convert_to_romaji(lyrics_jap, kks)

    logger.info('Translating song to English...')
    lyrics_eng = translate_lyrics(full_lyrics, model)

    lyrics_to_review = combine_jap_eng_for_prompt(lyrics_jap, lyrics_eng)

    logger.info('Improving translation...')
    lyrics_eng_improved = review_and_improve_translation(lyrics_to_review, model)

    logger.info('Generating DataFrame...')
    return create_dataframe(lyrics_jap, lyrics_rom, lyrics_eng, lyrics_eng_improved)


def process_song(full_lyrics: str, output_filepath: str, api_key_genai: str):
    """Orchestrates the full lyric translation process and saves to CSV."""
    df_lyrics = get_translation_data(full_lyrics, api_key_genai)
    logger.info(f'Generating CSV: {output_filepath}')
    save_to_csv(df_lyrics, output_filepath)
    logger.info("Process complete and saved to CSV file.")


def read_lyrics_file(filepath: str) -> str:
    """Reads the content of a text file."""
    logger.info(f"Reading lyrics from '{filepath}'...")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    """Main function to run the lyric translation workflow."""
    parser = argparse.ArgumentParser(description="Translate and process Japanese song lyrics.")
    parser.add_argument("lyrics_file", help="Path to the text file with the Japanese lyrics.")
    parser.add_argument("song_name", help="Name of the song to use for the output file.")
    parser.add_argument("-o", "--output", default=None, help="Base name for the output file (without extension). Defaults to the song name.")
    args = parser.parse_args()

    output_base = args.output if args.output else args.song_name
    csv_filename = f"{os.path.splitext(output_base)[0]}.csv"

    try:
        lyrics_jap_full = read_lyrics_file(args.lyrics_file)
    except FileNotFoundError:
        logger.error(f"The lyrics file was not found at '{args.lyrics_file}'")
        return

    api_key_genai = os.getenv('API_KEY_GENAI')
    if not api_key_genai:
        logger.error("The 'API_KEY_GENAI' environment variable is not set.")
        logger.error("Please create a .env file and add: API_KEY_GENAI=\"your_key_here\"")
        return

    process_song(lyrics_jap_full, csv_filename, api_key_genai)


if __name__ == "__main__":
    main()