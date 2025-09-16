# Lyric Processing Toolkit

This project has evolved from a set of command-line scripts into a full-featured web application designed to automate the creation of synchronized and translated song lyrics.

## Project Vision

The ultimate goal of this repository is to build a complete, cloud-native application on Google Cloud Platform (GCP). This application provides a user-friendly interface to:

1.  **Upload** a song file and provide the corresponding lyrics.
2.  **Automate** timestamp generation and multi-language translation.
3.  **Review and Edit** the generated lyrics, translations, and timestamps in an intuitive interface.
4.  **Generate and Download** the final audio file with the synchronized lyrics embedded.

## Features

-   **Web-Based UI:** A modern React frontend for a seamless user experience.
-   **Forced Alignment:** Uses `stable-whisper` to accurately synchronize an audio file with its corresponding lyric text.
-   **AI-Powered Translation:** Leverages the Google Gemini API to translate Japanese lyrics into Romaji and English, including a refinement pass for more natural-sounding translations.
-   **Interactive Editing:** A full-featured table editor to modify timestamps, lyrics, and translations.
-   **LRC Preview:** See a real-time preview of the final `.lrc` file as you make changes.
-   **Lyric Embedding:** Embeds the final, synchronized lyrics directly into the audio file's metadata.

## Technology Stack

The application is containerized using Docker for easy setup and deployment.

-   **Frontend:**
    -   React
    -   TypeScript
    -   Vite
-   **Backend:**
    -   Python 3
    -   FastAPI
    -   `stable-whisper` for audio alignment.
    -   `google-generativeai` for translation.
    -   `mutagen` for embedding lyrics.
-   **Orchestration:**
    -   Docker Compose

## Project Structure

```
lrc-generator/
├── backend/         # FastAPI application and processing logic
├── frontend/        # React user interface
├── docker-compose.yml # Orchestrates the frontend and backend services
└── ...
```

## Setup and Usage

### Prerequisites

-   Docker
-   Docker Compose

### Configuration

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/lrc-generator.git
    cd lrc-generator
    ```

2.  **Configure Environment Variables:**
    Create a `.env` file in the root of the project. This file will be used by the backend service inside the Docker container.
    ```env
    # .env
    API_KEY_GENAI="your_gemini_api_key_here"
    ```
    Replace `"your_gemini_api_key_here"` with your actual Google Gemini API key.

### Running the Application

1.  **Start the services:**
    Use Docker Compose to build and start the frontend and backend containers.
    ```bash
    docker-compose up --build
    ```

2.  **Access the application:**
    Open your web browser and navigate to:
    [http://localhost:5173](http://localhost:5173)

## Standalone CLI Scripts

The core logic of the backend is also available as standalone Python scripts. These were the original foundation of the project.

### Setup (for scripts only)

1.  **Install dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    # You will need to create this file based on your project's libraries
    pip install -r requirements.txt
    ```

2.  **Configure Environment Variables:**
    The scripts also use the `.env` file for the Gemini API key. The translation script previously used a `client_secrets.json` for Google Drive integration, but that feature is not used in the main web application.

### Usage

-   **Generating Timestamps (`forced_alignment.py`):**
    ```bash
    python backend/forced_alignment.py path/to/song.mp3 path/to/lyrics.txt -o song_timestamps.csv
    ```

-   **Translating Lyrics (`lyric_translate.py`):**
    ```bash
    python backend/lyric_translate.py path/to/japanese_lyrics.txt "Artist - Song Title"
    ```