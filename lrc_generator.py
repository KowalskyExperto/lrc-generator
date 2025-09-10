import argparse
import pandas as pd


def generate_lrc_content(df: pd.DataFrame) -> str:
    """
    Generates LRC formatted content from a DataFrame.
    The DataFrame is a result of merging alignment and translation data.
    """
    lrc_lines = []
    # Ensure translation columns exist and fill any missing values with empty strings
    for col in ['Romaji', 'English', 'Improved English']:
        if col not in df.columns:
            df[col] = ''
    df.fillna('', inplace=True)

    for _, row in df.iterrows():
        # Skip rows where the line is empty or just whitespace
        japanese_text = str(row['linea']).strip()
        if not japanese_text:
            continue

        # Convert milliseconds to centiseconds (2 digits for LRC format)
        try:
            # The values from the alignment CSV are already zero-padded strings.
            minutes = str(row['minutes']).zfill(2)
            seconds = str(row['seconds']).zfill(2)

            # Milliseconds is a 3-digit string; LRC format uses 2-digit centiseconds.
            # We can get this by simply taking the first two characters.
            centiseconds = str(row['milliseconds']).zfill(3)[:2]

            # Format the timestamp [mm:ss.xx]
            timestamp = f"[{minutes}:{seconds}.{centiseconds}]"

            # Prepare the multi-language lyric line
            romaji_text = str(row['Romaji']).strip()
            # Prioritize the improved translation, fall back to the initial one
            english_text = str(row['Improved English']).strip() or str(row['English']).strip()

            # Combine with tabs, as requested
            combined_lyrics = f"{japanese_text}\t{romaji_text}\t{english_text}"

            lrc_lines.append(f"{timestamp}{combined_lyrics}")
        except (ValueError, TypeError) as e:
            print(
                f"Skipping row due to invalid data: {row.to_dict()} - Error: {e}")
            continue

    return "\n".join(lrc_lines)


def save_lrc_file(content: str, filepath: str):
    """Saves the LRC content to a file."""
    print(f"Saving LRC file to '{filepath}'...")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("LRC file saved successfully.")


def main():
    """Main function to generate an LRC file from a CSV."""
    parser = argparse.ArgumentParser(
        description="Generate a multi-language .lrc file from alignment and translation CSVs.")
    parser.add_argument(
        "alignment_csv", help="Path to the CSV file from forced_alignment.py (contains timestamps).")
    parser.add_argument(
        "translation_csv", help="Path to the CSV file from lyric_translate.py (contains translations).")
    parser.add_argument("output_file", help="Path for the output .lrc file.")
    args = parser.parse_args()

    try:
        alignment_df = pd.read_csv(args.alignment_csv)
        translation_df = pd.read_csv(args.translation_csv)
    except FileNotFoundError as e:
        print(f"Error: Could not find an input file. Details: {e}")
        return

    # Merge the two dataframes by row index (side-by-side).
    # This is more robust than merging on text columns, as it assumes
    # both files have the same line-by-line structure.
    if len(alignment_df) != len(translation_df):
        print(f"Warning: The number of lines in the alignment file ({len(alignment_df)}) "
              f"does not match the translation file ({len(translation_df)}). "
              "The output may be misaligned.")

    # The 'linea' column from alignment_df will be used for the Japanese text.
    merged_df = pd.concat([alignment_df, translation_df], axis=1)

    lrc_content = generate_lrc_content(merged_df)
    save_lrc_file(lrc_content, args.output_file)


if __name__ == "__main__":
    main()
