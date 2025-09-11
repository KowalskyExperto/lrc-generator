import logging
import os
import shutil
import tempfile
import time
import glob
import pandas as pd
import mutagen
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from apscheduler.schedulers.background import BackgroundScheduler

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

# --- Temp File Cleanup --- 

TEMP_DIR_LIFESPAN_SECONDS = 24 * 60 * 60 # 24 hours

def cleanup_old_temp_dirs():
    """Finds and deletes temporary directories created by this app that are older than a threshold."""
    logger.info("Running scheduled cleanup of old temporary directories...")
    temp_dir_root = tempfile.gettempdir()
    # tempfile.mkdtemp() creates directories with a specific pattern (e.g., 'tmp<random>')
    search_pattern = os.path.join(temp_dir_root, 'tmp*')
    
    for dir_path in glob.glob(search_pattern):
        if not os.path.isdir(dir_path):
            continue
        try:
            dir_age_seconds = time.time() - os.path.getmtime(dir_path)
            if dir_age_seconds > TEMP_DIR_LIFESPAN_SECONDS:
                logger.info(f"Deleting old temporary directory: {dir_path} (Age: {dir_age_seconds / 3600:.2f} hours)")
                shutil.rmtree(dir_path)
        except FileNotFoundError:
            # Directory might have been deleted by another process, safe to ignore
            continue
        except Exception as e:
            logger.error(f"Error deleting temporary directory {dir_path}: {e}")
    logger.info("Finished temporary directory cleanup.")

# --- Scheduler and Lifespan Management ---

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    logger.info("Application startup: Initializing background scheduler...")
    # Run once on startup
    cleanup_old_temp_dirs()
    # Schedule to run every hour
    scheduler.add_job(cleanup_old_temp_dirs, 'interval', hours=1)
    scheduler.start()
    yield
    # On shutdown
    logger.info("Application shutdown: Stopping background scheduler...")
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

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


def cleanup_temp_dir(directory: str):
    """Removes the specified directory and its contents."""
    try:
        shutil.rmtree(directory)
        logger.debug(f"Successfully cleaned up temporary directory: {directory}")
    except Exception as e:
        logger.error(f"Error cleaning up temporary directory {directory}: {e}")

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
        # Clean up the directory on failure before raising the exception
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")

@app.post("/generate-and-embed")
async def generate_and_embed(
    audio_file: UploadFile = File(...),
    lyrics_data: str = Form(...),
    metadata: str = Form(...)
):
    logger.info("Received request to generate final file.")
    temp_dir = tempfile.mkdtemp()
    
    if not audio_file.filename:
        logger.error("Finalize failed: The audio file is missing a filename.")
        raise HTTPException(status_code=400, detail="The uploaded file is missing a filename.")
    temp_audio_path = os.path.join(temp_dir, audio_file.filename)

    try:
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        logger.debug(f"Temporarily saved audio file for final processing to {temp_audio_path}")

        lyrics_list = json.loads(lyrics_data)
        metadata_dict = json.loads(metadata)

        # --- Generate LRC Content ---
        logger.info("Generating final LRC content string.")
        headers = [
            f"[ar: {metadata_dict.get('artist')}]",
            f"[al: {metadata_dict.get('album')}]",
            f"[ti: {metadata_dict.get('title')}]",
            f"[length: {metadata_dict.get('length')}]",
            f"[tool: KowalskyExperto]"
        ]
        lrc_body = []
        for row in lyrics_list:
            centiseconds = row['milliseconds'][:2]
            line = f"[{row['minutes']}:{row['seconds']}.{centiseconds}]{row['Japanese']} {row['Romaji']} {row['selectedLyric']}"
            lrc_body.append(line)
        
        final_lrc_content = "\n".join(headers + lrc_body)

        # --- Embed LRC into Audio File ---
        logger.info("Embedding LRC content into audio file.")
        audio_meta = mutagen.File(temp_audio_path)
        audio_meta["LYRICS"] = final_lrc_content
        audio_meta.save()
        logger.info("Embedding complete.")

        return FileResponse(
            path=temp_audio_path,
            media_type='application/octet-stream',
            filename=f"{metadata_dict.get('title', 'final_song')}.flac",
            background=BackgroundTask(cleanup_temp_dir, temp_dir)
        )

    except Exception as e:
        logger.error(f"An error occurred during final generation: {e}", exc_info=True)
        # Clean up the directory on failure before raising the exception
        cleanup_temp_dir(temp_dir)
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {e}")