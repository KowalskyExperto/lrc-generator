import argparse
import google.generativeai as genai
import os
import logging
import asyncio

from dotenv import load_dotenv
from itertools import zip_longest
from pandas import DataFrame
from pykakasi import kakasi

# --- Logger ---
logger = logging.getLogger(__name__)

load_dotenv()

# --- Constants ---
# The model name is now configurable via an environment variable
GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
MAX_RETRIES = 3

def convert_to_romaji(japanese_text: list, kks: kakasi) -> list:
    """Converts a list of Japanese strings to Romaji."""
    romaji_lines = []
    for line in japanese_text:
        converted_words = []
        for word_info in kks.convert(line):
            hepburn_word = word_info.get('hepburn')
            if hepburn_word and hepburn_word.strip(): # Ensure it's not None or empty after stripping
                converted_words.append(hepburn_word.strip())
        
        # Now, process converted_words to remove potential duplicates at the end
        # This is a heuristic for "last word added twice"
        if len(converted_words) >= 2 and converted_words[-1] == converted_words[-2]:
            converted_words.pop() # Remove the last word if it's a duplicate of the second to last

        romaji_lines.append(' '.join(converted_words))
    return romaji_lines


async def translate_lyrics(japanese_lyrics: str, model: genai.GenerativeModel) -> list:
    """Gets the English translation from Gemini."""
    prompt = f"""
**ROLE**: You are a precise, line-by-line translator.
**TASK**: Translate the following Japanese song lyrics into English.
**RULES**:
1. The output MUST have the exact same number of lines as the input.
2. Each line in the output MUST correspond directly to the same line in the input.
3. DO NOT add any extra text, introductory phrases, explanations, or comments.
4. Preserve all original line breaks.

**JAPANESE LYRICS TO TRANSLATE**:
---
{japanese_lyrics}
---
    """
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, model.generate_content, prompt)
    translated_text = response.text.strip()
    return translated_text.strip().split('\n')



async def review_and_improve_translation(lyrics_to_review: str, model: genai.GenerativeModel) -> list:
    """Reviews and improves a Japanese-to-English song translation."""
    prompt = f"""
**ROLE**: You are a precise, line-by-line translation reviewer.
**TASK**: Review the proposed English translation and provide a more natural, improved version.
**RULES**:
1. The output MUST have the exact same number of lines as the input Japanese lyrics.
2. Each line in the output MUST correspond directly to the same line in the input.
3. DO NOT add any extra text, introductory phrases, explanations, or comments.
4. Provide ONLY the improved English translation.

**LYRICS TO REVIEW (JAPANESE vs. ENGLISH)**:
---
{lyrics_to_review}
---
"""
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, model.generate_content, prompt)
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

async def get_translation_data(full_lyrics: str, api_key_genai: str) -> DataFrame:
    """
    Processes lyrics to generate translations and returns them as a DataFrame.
    Includes a retry mechanism for each translation step.
    """
    genai.configure(api_key=api_key_genai)
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    kks = kakasi()

    lyrics_jap = full_lyrics.strip().split('\n')
    logger.info('Converting to Romaji...')
    lyrics_rom = convert_to_romaji(lyrics_jap, kks)

    # --- Loop 1: Initial Translation ---
    lyrics_eng = []
    for attempt in range(MAX_RETRIES):
        logger.debug(f"Initial translation attempt {attempt + 1} of {MAX_RETRIES}...")
        lyrics_eng = await translate_lyrics(full_lyrics, model)
        if len(lyrics_jap) == len(lyrics_eng):
            logger.info("Initial translation line count matches.")
            break
        else:
            logger.warning(
                f"Attempt {attempt + 1} failed: Initial translation line count mismatch. "
                f"Japanese: {len(lyrics_jap)}, English: {len(lyrics_eng)}. Retrying..."
            )
    else: # This 'else' belongs to the 'for' loop, and runs if the loop completes without a 'break'
        raise ValueError("Initial translation failed due to persistent line count mismatch.")

    # --- Loop 2: Improved Translation ---
    lyrics_to_review = combine_jap_eng_for_prompt(lyrics_jap, lyrics_eng)
    lyrics_eng_improved = []
    for attempt in range(MAX_RETRIES):
        logger.debug(f"Improved translation attempt {attempt + 1} of {MAX_RETRIES}...")
        lyrics_eng_improved = await review_and_improve_translation(lyrics_to_review, model)
        if len(lyrics_jap) == len(lyrics_eng_improved):
            logger.info("Improved translation line count matches.")
            break
        else:
            logger.warning(
                f"Attempt {attempt + 1} failed: Improved translation line count mismatch. "
                f"Japanese: {len(lyrics_jap)}, Improved: {len(lyrics_eng_improved)}. Retrying..."
            )
    else:
        raise ValueError("Improved translation failed due to persistent line count mismatch.")

    # --- Final DataFrame Creation ---
    logger.info('Generating DataFrame...')
    return create_dataframe(lyrics_jap, lyrics_rom, lyrics_eng, lyrics_eng_improved)


def process_song(full_lyrics: str, output_filepath: str, api_key_genai: str):
    """Orchestrates the full lyric translation process and saves to CSV."""
    try:
        df_lyrics = get_translation_data(full_lyrics, api_key_genai)
        logger.info(f'Generating CSV: {output_filepath}')
        save_to_csv(df_lyrics, output_filepath)
        logger.info("Process complete and saved to CSV file.")
    except ValueError as e:
        logger.error(f"Could not process song: {e}")


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
