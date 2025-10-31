# Gemini Predictive Text Web App

This is a simple web application built with Flask and Python that uses the Google Gemini API to provide real-time predictive text suggestions. As a user types into a text area, the application suggests the most likely next words and completes phrases for them.

## Features

- **Next Word Prediction:** Fetches the 10 most likely next words for the current text.
- **Phrase Completion:** Generates complete phrases based on the predicted next words.
- **Dynamic UI:** Presents suggestions to the user in an interactive interface.
- **Event Logging:** Captures user interactions and other client-side events for analytics, outputting them as structured JSON logs.

## How It Works

The suggestion generation is a multi-step process designed to provide rich, contextual predictions:

1.  **Fetch Next Words:** When the user types, the current text is sent to the Gemini API to predict the 10 most likely single words that could come next.
2.  **Fetch Next Phrases:** The application then takes the original text and the list of 10 predicted words and makes a second call to the Gemini API. It asks the model to complete the original phrase starting with each of the 10 predicted words.
3.  **Parse and Display:** The raw text responses from the API are parsed, cleaned, and structured into a list of suggestions, each containing the predicted word and its corresponding phrase completion. These are then sent to the frontend to be displayed to the user.

## Technology Stack

- **Backend:** Python, Flask
- **AI Model:** Google Gemini (`gemini-flash-latest`) via the `google-generativeai` library
- **Frontend:** HTML, CSS, JavaScript

## Setup and Installation

Follow these steps to get the application running locally.

### 1. Prerequisites

- Python 3.8+
- A Google Gemini API Key.

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd finalPrototype
```

### 3. Create and Activate a Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```powershell
# If you get an error, you may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

Install the required Python packages.

```bash
pip install Flask google-generativeai
```

### 5. Configure Environment Variables

The application requires a Gemini API key. Set it as an environment variable named `GEMINI_API_KEY`.

**On macOS/Linux:**
```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

**On Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY="YOUR_API_KEY"
```

**On Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

### 6. Run the Application

Start the Flask development server:

```bash
flask run
```

The application will be available at `http://127.0.0.1:5000`.

## API Endpoints

The Flask backend provides the following endpoints:

### `POST /get_suggestions`

This is the main endpoint for fetching text predictions.

- **Request Body:** A JSON object containing the user's current text.
  ```json
  {"typedText": "The quick brown fox"}
  ```
- **Response:** A JSON array of suggestion objects.
  ```json
  [
    {"word": "jumps", "phrase": "over the lazy dog"},
    {"word": "is", "phrase": "a mammal"}
  ]
  ```

### `POST /log_event`

This endpoint is used by the frontend to send client-side event data to the backend for logging. The backend logs the received JSON payload with a severity level of `INFO`.

- **Request Body:** Any valid JSON object representing the event to be logged.
  ```json
  {"event": "suggestion_clicked", "word": "jumps"}
  ```
