import stable_whisper
from typing import List, Dict, Any
from pandas import DataFrame
import argparse

# --- Constants ---
DEFAULT_MODEL_NAME = "base"

# --- Functions ---


def load_model(model_name: str) -> Any:
    """Loads a Stable Whisper model."""
    print(f"Loading model '{model_name}'...")
    model = stable_whisper.load_model(model_name)
    print("Model loaded.")
    return model


def align_lyrics(
    model: Any,
    audio_path: str,
    lyrics: str,
    language: str
) -> stable_whisper.WhisperResult:
    """
    Aligns audio with the provided lyrics using Stable Whisper.
    Performs a refinement step to improve accuracy.
    """
    print(f"Aligning audio '{audio_path}' with lyrics...")
    # First alignment pass
    result = model.align(audio_path, lyrics,
                         language=language, suppress_silence=True)
    # Second pass to refine timestamps
    result = model.align(audio_path, result,
                         language=language, suppress_silence=True)
    print("Alignment complete.")
    return result


def generate_line_timestamps(
    lyrics_lines: List[str],
    word_timestamps: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generates start and end timestamps for each line of the lyrics, based on
    the timestamps of individual words.
    """
    print("Generating line timestamps...")
    final_result: List[Dict[str, Any]] = []
    word_idx = 0
    previous_end_time = 0.0

    for original_line in lyrics_lines:
        line = original_line.strip()
        if not line:
            # For empty lines, use the end time of the previous line.
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
                f"Error: The word timestamps list does not match the lyrics. Failed at line: '{line}'")
            print(f"Successfully processed {len(final_result)} lines.")
            break

    print("Line timestamps generated.")
    return final_result


def add_detailed_timestamps(
    line_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Adds detailed minutes, seconds, and milliseconds to each line dictionary
    based on the 'start' time and removes the original 'start' and 'end' keys.
    The time values are formatted as zero-padded strings to comply with the LRC
    format. Returns a new list.
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

            # Format as zero-padded strings (e.g., 01, 07, 050)
            new_item.update({'minutes': f"{minutes:02d}", 'seconds': f"{seconds:02d}", 'milliseconds': f"{milliseconds:03d}"})

        # Remove the original time keys in seconds
        if 'start' in new_item:
            del new_item['start']
        if 'end' in new_item:
            del new_item['end']

        processed_data.append(new_item)
    return processed_data


def run_alignment_workflow(
    audio_path: str,
    lyrics_text: str,
    output_path: str,
    model_name: str = DEFAULT_MODEL_NAME,
    language: str = "ja"
) -> None:
    """
    Orchestrates the full audio and lyric alignment process.
    """
    # Step 1: Load the model
    model = load_model(model_name)

    # Step 2: Align audio and lyrics
    alignment_result = align_lyrics(model, audio_path, lyrics_text, language=language)

    # Optional: Save the raw alignment result
    # alignment_result.save_as_json('raw_alignment.json')

    # Step 3: Extract all words
    all_words: List[Dict[str, Any]] = []
    for segment in alignment_result.segments:
        for word in segment.words:
            all_words.append({
                'word': word.word,
                'start': word.start,
                'end': word.end
            })

    if not all_words:
        print("No words found in the alignment result. Aborting.")
        return

    # Step 4: Generate timestamps for each original lyric line
    lyrics_lines = lyrics_text.strip().split('\n')
    line_timestamps = generate_line_timestamps(lyrics_lines, all_words)

    # Step 5: Add detailed timestamps for each line
    processed_list = add_detailed_timestamps(line_timestamps)

    # Step 6: Save the final result
    save_to_csv(processed_list, output_path)

    print("\nThe process has finished successfully.")


def save_to_csv(data: List[Dict[str, Any]], file_path: str) -> None:
    """Saves a list of dictionaries to a CSV file using pandas."""
    if not data:
        print("No data to save.")
        return
    print(f"Saving result to '{file_path}'...")
    df = DataFrame(data)
    df.to_csv(file_path, index=False, encoding='utf-8')

def read_lyrics_file(filepath: str) -> str:
    """Reads the content of a text file."""
    print(f"Reading lyrics from '{filepath}'...")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def main() -> None:
    """
    Main function to handle command-line arguments and run the alignment workflow.
    """
    parser = argparse.ArgumentParser(description="Align audio with lyrics using stable-whisper.")
    parser.add_argument("audio", help="Path to the audio file.")
    parser.add_argument("lyrics", help="Path to the text file with the lyrics.")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL_NAME, help=f"Name of the Whisper model (default: {DEFAULT_MODEL_NAME}).")
    parser.add_argument("-o", "--output", default="final.csv", help="Path for the output CSV file (default: final.csv).")
    parser.add_argument("--lang", default="ja",
                        help="Language code of the lyrics (default: ja).")
    args = parser.parse_args()

    # Read lyrics from the file
    lyrics_text = read_lyrics_file(args.lyrics)

    # Run the main workflow
    run_alignment_workflow(
        audio_path=args.audio,
        lyrics_text=lyrics_text,
        output_path=args.output,
        model_name=args.model,
        language=args.lang
    )


if __name__ == "__main__":
    main()
