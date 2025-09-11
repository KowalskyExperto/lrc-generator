# Project Roadmap: From Scripts to an Interactive Web Application

This document outlines the strategic roadmap to evolve the Lyric Processing Toolkit from a set of command-line scripts to a full-featured, cloud-native web application on Google Cloud Platform (GCP). The application will allow users to upload a song, generate and edit synchronized translations, and download a final audio file with the lyrics embedded.

---

### Phase 1: Backend Refactoring & API Foundation

**Goal:** Transform the existing script logic into a reusable, callable API. This is the essential foundation for the web application.

1.  **Modularize Core Logic:**
    *   **Action:** Refactor `forced_alignment.py`, `lyric_translate.py`, and `lrc_generator.py`.
    *   **Details:** In each file, separate the core processing functions (e.g., `align_lyrics`, `translate_lyrics`, `generate_lrc_content`) from the command-line argument parsing (`argparse`) and file I/O. These functions should accept data as arguments and return data structures (like lists of dictionaries or DataFrames).

2.  **Set Up a Web Framework:**
    *   **Action:** Create a new Python file (e.g., `main.py`) and choose a web framework.
    *   **Recommendation:** **FastAPI** is an excellent choice. It's modern, fast, and automatically generates interactive API documentation, which is very helpful for development.

3.  **Create the Initial Processing Endpoint:**
    *   **Action:** Implement a `/process-lyrics` (POST) endpoint in your FastAPI application.
    *   **Details:** This endpoint will accept an uploaded audio file and a string of lyrics. It will then call the newly modularized functions from `forced_alignment` and `lyric_translate` to get the timestamps and translations. The endpoint will merge this data into a single JSON object (a list of lines, where each line is a dictionary) and return it to the user.
    *   **Example JSON response for one line:**
        ```json
        {
          "linea": "君が好きだと叫びたい",
          "minutes": "00",
          "seconds": "15",
          "milliseconds": "340",
          "romaji": "kimi ga suki da to sakebitai",
          "english": "I want to shout that I love you",
          "improved_english": "I just want to scream that I love you"
        }
        ```

---

### Phase 2: Frontend - The Interactive Lyric Editor

**Goal:** Build the user-facing web page where the magic happens.

1.  **Create the Basic UI:**
    *   **Action:** Develop a simple `index.html` file.
    *   **Details:** This file will contain a form with a file input for the song (`<input type="file">`), a textarea for the lyrics (`<textarea>`), and a "Generate" button.

2.  **Implement the Frontend Logic (JavaScript):**
    *   **Action:** Write the JavaScript code to power the page.
    *   **Details:**
        *   When the "Generate" button is clicked, use the `fetch` API to send the audio and lyrics to your `/process-lyrics` backend endpoint.
        *   When the backend responds with the JSON data, dynamically generate an editable HTML table. Each row will correspond to a lyric line, and each cell (`minutes`, `seconds`, `japanese`, `romaji`, etc.) will be an `<input type="text">` field, pre-filled with the data.
        *   For the English translation, add a mechanism (like a dropdown or radio buttons in each row) to select whether the "English" or "Improved English" version should be used in the final LRC.
        *   Add a "Save and Download" button below the table.

---

### Phase 3: Finalization & Audio Embedding

**Goal:** Process the user's edits and generate the final, lyric-embedded audio file.

1.  **Install an Audio Metadata Library:**
    *   **Action:** Add a new dependency to your project.
    *   **Recommendation:** **`mutagen`** is the standard and most powerful Python library for editing audio metadata (ID3 tags for MP3, etc.).

2.  **Create the Finalization Endpoint:**
    *   **Action:** Implement a `/generate-file` (POST) endpoint.
    *   **Details:** This endpoint will accept a JSON payload representing the (potentially edited) data from the frontend table.

3.  **Implement the Generation Logic:**
    *   **Action:** In the `/generate-file` endpoint, orchestrate the final steps.
    *   **Details:**
        1.  Call the modularized `generate_lrc_content` function, passing it the edited data to create the final LRC-formatted string.
        2.  Use the `mutagen` library to open the original audio file.
        3.  Embed the LRC string into the appropriate metadata tag (e.g., the `USLT` or `SYLT` tag for MP3 files).
        4.  Save the modified audio to a new file in a temporary location.
        5.  Send this new audio file back to the user, triggering a download in their browser.

---

### Phase 4: Deployment to Google Cloud Platform (GCP)

**Goal:** Make the application publicly accessible, scalable, and robust using cloud services.

1.  **Containerize the Application:**
    *   **Action:** Create a `Dockerfile`.
    *   **Details:** This file will define the steps to package your entire FastAPI application, Python dependencies (including `mutagen`), and static frontend files (`index.html`, etc.) into a portable Docker image.

2.  **Architect the GCP Services:**
    *   **Action:** Plan the integration of GCP services.
    *   **Details:**
        *   **Cloud Run:** Use as the primary service to deploy and run your containerized application. It's serverless, so it scales automatically (even to zero) and you only pay for what you use.
        *   **Cloud Storage (GCS):** Do not store uploaded files on the Cloud Run instance itself. Modify your endpoints to immediately upload user audio files to a GCS bucket. The processing functions will then read from this bucket. This is critical for a scalable, stateless application.
        *   **Artifact Registry:** Use to store your Docker images.
        *   **Secret Manager:** Store your `API_KEY_GENAI` and any other secrets here. Grant your Cloud Run service permission to access them securely at runtime.

3.  **Deploy:**
    *   **Action:** Execute the deployment.
    *   **Details:** Build the Docker image, push it to Artifact Registry, and then create a new Cloud Run service pointing to that image. Configure the service to allow public access and connect it to your secrets.
