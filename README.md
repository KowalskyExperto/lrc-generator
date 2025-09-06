
# Lyric Processing Toolkit

This project provides a powerful suite of command-line tools designed to automate the creation of synchronized and translated song lyrics.

## Project Vision

The ultimate goal of this repository is to build a complete, cloud-native application on Google Cloud Platform (GCP). This application will provide a user-friendly interface to:

1.  **Upload** a song file.
2.  **Provide** the corresponding lyrics.
3.  **Automate** the translation and timestamp generation.
4.  **Review and Edit** the generated lyrics or timestamps if corrections are needed.
5.  **Generate** a final file with the synchronized lyrics embedded.

This repository represents the foundational first steps toward that goal, currently existing as a set of powerful command-line scripts.

## Current Features

-   **Forced Alignment:** Uses `stable-whisper` to accurately synchronize an audio file with its corresponding lyric text, generating precise start times for each line.
-   **AI-Powered Translation:** Leverages the Google Gemini API to translate Japanese lyrics into Romaji and then into English.
-   **Two-Step Translation Refinement:** Implements a sophisticated workflow that first translates the lyrics and then uses a second AI pass to review and improve the translation for a more natural and contextual feel.
-   **LRC-Ready Output:** The alignment script generates a CSV with pre-formatted `minutes`, `seconds`, and `milliseconds` components, ready for easy conversion into a standard `.lrc` file.
-   **Cloud Integration:** Automatically uploads the multi-language translation results (Japanese, Romaji, English, Improved English) to Google Drive as a Google Sheet for easy access and collaboration.
-   **Flexible CLI:** Both scripts are built with command-line interfaces, allowing you to easily process different songs without modifying the source code.

## Technologies Used

-   stable-whisper for accurate word-level audio alignment.
-   Google Gemini API for high-quality translation and refinement.
-   Pandas for data manipulation and CSV handling.
-   PyDrive2 for seamless Google Drive integration.
-   PyKakasi for Japanese to Romaji conversion.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/lrc-generator.git
    cd lrc-generator
    ```

2.  **Install dependencies:**
    It's recommended to use a virtual environment.
    ```bash
    # You will need to create this file based on your project's libraries
    pip install -r requirements.txt
    ```

3.  **Enable Google Drive API and Download Credentials:**
    To allow the script to upload files to your Google Drive, you need to configure API access.
    - Go to the Google Cloud Console and create a new project (or select an existing one).
    - In the navigation menu, go to **APIs & Services > Library** and enable the **Google Drive API**.
    - Go to **APIs & Services > Credentials**. Click **Create Credentials** and select **OAuth client ID**.
    - Choose **Desktop app** as the application type and give it a name.
    - After creation, click the **Download JSON** icon for the new client ID.
    - Rename the downloaded file to `client_secrets.json` and place it in the root directory of this project.

    > **Note on Permissions:** When you run `lyric_translate.py` for the first time, your browser will open and ask you to grant permission. The script requires the `https://www.googleapis.com/auth/drive` scope, which allows it to create and manage files in your Google Drive.

4.  **Configure Environment Variables:**
    Create a `.env` file in the root of the project and add your API keys:
    ```env
    API_KEY_GENAI="your_gemini_api_key_here"
    ID_FOLDER="your_google_drive_folder_id_here"
    ```

## Usage

### 1. Generating Timestamps (`forced_alignment.py`)

This script takes an audio file and a plain text lyrics file and outputs a CSV with synchronized timestamps.

```bash
python forced_alignment.py path/to/song.mp3 path/to/lyrics.txt -o song_timestamps.csv
```

### 2. Translating Lyrics (`lyric_translate.py`)

This script takes a Japanese lyrics file, translates it, and uploads the result to Google Drive. The song name should be wrapped in quotes if it contains spaces.

```bash
python lyric_translate.py path/to/japanese_lyrics.txt "Artist - Song Title"
```
