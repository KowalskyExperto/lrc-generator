import logging
import os
import shutil
import tempfile
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException

# --- Local Imports ---
from backend.forced_alignment import get_alignment_data
from backend.lyric_translate import get_translation_data

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
# --- End Logging Configuration ---

app = FastAPI()


@app.get("/")
def read_root():
    """Root endpoint to check if the server is running."""
    return {"message": "LRC Generator API is running."}


@app.post("/process-lyrics")
async def process_lyrics(
    audio_file: UploadFile = File(...),
    lyrics_text: str = Form(...)
):
    logger.debug(f"Received lyrics_text: {repr(lyrics_text)}")
    """
    Main endpoint to process an audio file and lyrics.
    1. Receives audio and lyrics.
    2. Runs forced alignment to get timestamps.
    3. Runs translation.
    4. Merges the results and returns them as JSON.
    """
    temp_dir = tempfile.mkdtemp()

    if not audio_file.filename:
        logger.error("Upload failed: The audio file is missing a filename.")
        raise HTTPException(status_code=400, detail="The uploaded file is missing a filename.")
    temp_audio_path = os.path.join(temp_dir, audio_file.filename)

    try:
        # Save the uploaded audio file to the temporary directory
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        logger.debug(f"Temporarily saved audio file to {temp_audio_path}")

        # Check for API key
        api_key_genai = os.getenv('API_KEY_GENAI')
        if not api_key_genai:
            logger.error("API_KEY_GENAI environment variable not set.")
            raise HTTPException(status_code=500, detail="Server is missing API key configuration.")

        # --- Run Processing Functions ---
        logger.info("Starting forced alignment...")
        alignment_data = get_alignment_data(audio_path=temp_audio_path, lyrics_text=lyrics_text)
        if not alignment_data:
            raise HTTPException(status_code=500, detail="Forced alignment failed to produce a result.")
        alignment_df = pd.DataFrame(alignment_data)

        logger.info("Starting translation...")
        translation_df = get_translation_data(full_lyrics=lyrics_text, api_key_genai=api_key_genai)

        # --- Merge and Return Results ---
        logger.info("Merging alignment and translation data...")
        # Ensure both dataframes have the same index to prevent misalignment
        alignment_df.reset_index(drop=True, inplace=True)
        translation_df.reset_index(drop=True, inplace=True)
        
        merged_df = pd.concat([alignment_df, translation_df], axis=1)

        # Convert DataFrame to a list of dictionaries for JSON response
        result_json = merged_df.to_dict(orient='records')
        
        logger.info("Successfully processed lyrics.")
        return result_json

    except Exception as e:
        logger.error(f"An error occurred during processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

    finally:
        # Clean up the temporary directory and its contents
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.debug(f"Successfully cleaned up temporary directory: {temp_dir}")
