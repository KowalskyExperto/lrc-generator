import logging
import os
import shutil
import tempfile
import pandas as pd
import mutagen
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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

# --- CORS Middleware Configuration ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    temp_dir = tempfile.mkdtemp()

    if not audio_file.filename:
        logger.error("Upload failed: The audio file is missing a filename.")
        raise HTTPException(status_code=400, detail="The uploaded file is missing a filename.")
    temp_audio_path = os.path.join(temp_dir, audio_file.filename)

    try:
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        logger.debug(f"Temporarily saved audio file to {temp_audio_path}")

        # --- Read Audio Metadata ---
        try:
            audio_meta = mutagen.File(temp_audio_path, easy=True)
            length_seconds = audio_meta.info.length
            minutes = int(length_seconds // 60)
            seconds = length_seconds % 60
            metadata = {
                'title': audio_meta.get('title', [audio_file.filename])[0],
                'artist': audio_meta.get('artist', ['Unknown Artist'])[0],
                'album': audio_meta.get('album', ['Unknown Album'])[0],
                'length': f"{minutes:02}:{seconds:06.3f}"
            }
        except Exception as meta_e:
            logger.warning(f"Could not read metadata from audio file: {meta_e}")
            metadata = {
                'title': audio_file.filename,
                'artist': 'Unknown Artist',
                'album': 'Unknown Album',
                'length': '00:00.000'
            }
        logger.info(f"Read metadata: {metadata}")

        # --- Check for API key ---
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
        alignment_df.reset_index(drop=True, inplace=True)
        translation_df.reset_index(drop=True, inplace=True)
        merged_df = pd.concat([alignment_df, translation_df], axis=1)
        lyrics_json = merged_df.to_dict(orient='records')
        
        logger.info("Successfully processed lyrics.")
        return {
            "lyrics": lyrics_json,
            "metadata": metadata
        }

    except Exception as e:
        logger.error(f"An error occurred during processing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.debug(f"Successfully cleaned up temporary directory: {temp_dir}")