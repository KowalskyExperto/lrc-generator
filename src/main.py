import logging
from fastapi import FastAPI

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
# --- End Logging Configuration ---

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}