import argparse
import google.generativeai as genai
import os

from dotenv import load_dotenv
from itertools import zip_longest
from pandas import DataFrame
from pykakasi import kakasi


load_dotenv()

# --- Constants ---
GEMINI_MODEL_NAME = 'gemini-1.5-flash'


def convert_to_romaji(japanese_text: list, kks: kakasi) -> list:
    """Converts a list of Japanese strings to Romaji."""
    # Convert each line in the list more cleanly
    return [' '.join(word['hepburn'] for word in kks.convert(line)) for line in japanese_text]


def translate_lyrics(japanese_lyrics: str, model: genai.GenerativeModel) -> list:
    """
    Gets the English translation from Gemini.
    """
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


def review_and_improve_translation(lyrics_to_review: str, model: genai.GenerativeModel) -> list:
    """
    Reviews and improves a Japanese-to-English song translation.
    """
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
    # Use zip_longest to handle lists of unequal length gracefully
    zipped_data = zip_longest(lyrics_jap, lyrics_rom,
                              lyrics_eng, lyrics_eng_improved, fillvalue="")

    # Strip whitespace from each item in each row
    data = [[item.strip() for item in row] for row in zipped_data]
    df = DataFrame(data, columns=['Japanese',
                   'Romaji', 'English', 'Improved English'])
    return df


def save_to_csv(dataframe: DataFrame, filename: str):
    """
    Saves a pandas DataFrame to a CSV file.
    """
    dataframe.to_csv(filename, index=False, header=True, encoding='utf-8')
    print(f"The translation has been successfully saved to '{filename}'.")


def combine_jap_eng_for_prompt(lyrics_jap: list, lyrics_eng: list) -> str:
    """Combines the Japanese and English lyrics line-by-line for the review prompt."""
    # Use zip_longest to ensure all Japanese lines are included, even if a translation is missing.
    combined_lines = [f"{jap.strip()}\t{eng.strip()}" for jap, eng in zip_longest(
        lyrics_jap, lyrics_eng, fillvalue="")]
    return "\n".join(combined_lines)

# Main workflow function


def process_song(full_lyrics: str, output_filepath: str, api_key_genai: str):
    # Step 1: Configure APIs and initialize objects once for efficiency
    genai.configure(api_key=api_key_genai)
    model = genai.GenerativeModel(GEMINI_MODEL_NAME)
    kks = kakasi()

    # Step 2: Get Japanese and Romaji
    lyrics_jap = full_lyrics.strip().split('\n')
    print('Converting to Romaji...')
    lyrics_rom = convert_to_romaji(lyrics_jap, kks)

    # Step 3: Get initial translation
    print('Translating song to English...')
    lyrics_eng = translate_lyrics(full_lyrics, model)

    # Step 4: Combine Japanese and English for the improvement prompt
    lyrics_to_review = combine_jap_eng_for_prompt(lyrics_jap, lyrics_eng)

    # Step 5: Get improved translation
    print('Improving translation...')
    lyrics_eng_improved = review_and_improve_translation(
        lyrics_to_review, model)

    # Step 6: Generate and save the DataFrame
    print('Generating DataFrame...')
    df_lyrics = create_dataframe(
        lyrics_jap, lyrics_rom, lyrics_eng, lyrics_eng_improved)
    print('Generating CSV...')
    save_to_csv(df_lyrics, output_filepath)
    print("Process complete and saved to CSV file.")


def read_lyrics_file(filepath: str) -> str:
    """Reads the content of a text file."""
    print(f"Reading lyrics from '{filepath}'...")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def main():
    """Main function to run the lyric translation workflow."""
    parser = argparse.ArgumentParser(
        description="Translate and process Japanese song lyrics.")
    parser.add_argument(
        "lyrics_file", help="Path to the text file with the Japanese lyrics.")
    parser.add_argument(
        "song_name", help="Name of the song to use for the output file.")
    parser.add_argument("-o", "--output", default=None,
                        help="Base name for the output file (without extension). Defaults to the song name.")
    args = parser.parse_args()

    output_filename_base = args.output if args.output else args.song_name
    csv_filename = f'{output_filename_base}.csv'

    # Read the lyrics from the provided file
    lyrics_jap_full = read_lyrics_file(args.lyrics_file)
    api_key_genai = os.getenv('API_KEY_GENAI')

    # Process the song
    process_song(lyrics_jap_full, csv_filename, api_key_genai)


if __name__ == "__main__":
    main()
