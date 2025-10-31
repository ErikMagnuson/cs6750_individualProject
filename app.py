import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
import logging
import json

app = Flask(__name__)

# --- Gemini API Configuration ---
try:
    # This is the recommended way to load an API key for deployment.
    # Set the GEMINI_API_KEY environment variable on your hosting platform.
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
except (ValueError, ImportError) as e:
    print(f"Error configuring Gemini API: {e}")
    print("Please set the GEMINI_API_KEY environment variable.")
    # The app can still run, but API calls will fail.

# Use a capable and fast model suitable for this task.
GEMINI_MODEL = "gemini-flash-latest"

def _call_gemini(prompt: str) -> str | None:
    """Helper function to call the Gemini API and return the response content."""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        # Configure safety settings to be less restrictive for this use case.
        safety_settings = {
            'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
            'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
        }
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def fetch_next_words(current_text):
    """Step 1: Fetches the 10 most likely next words."""
    prompt = f"""Predict the most likely next word for the following phrase: "{current_text}"

Generate 10 predictions. 
1. Provide only a numbered list of 10 single words.
2. Do not include punctuation unless it's part of the word (e.g., "don't").
3. Do not add any explanation or preamble.
"""
    try:
        text = _call_gemini(prompt)
        if not text:
            return []

        parsed_words = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Find the first period
            parts = line.split('.', 1)
            # Check if the part before the period is a number
            if len(parts) == 2 and parts[0].strip().isdigit():
                # Add the part after the period
                parsed_words.append(parts[1].strip())

        return [word for word in parsed_words if word and len(word.split(' ')) == 1]
    except Exception as e:
        print(f"Error in fetch_next_words: {e}")
        return []

def fetch_next_phrases(current_text, next_words):
    """Step 2: Fetches the completed phrases for the given words."""
    word_list = "\n".join([f"{i + 1}. {word}" for i, word in enumerate(next_words)])
    
    prompt = f"""You will be given a text phrase and a numbered list of 10 words.
Your task is to complete the phrase starting with each of the 10 words.

Text Phrase: "{current_text}"
Word List:
{word_list}

Provide your response as a numbered list of 3-7 words that complete the phrase, one list item for each word in the Word List. Do not include the entire phrase in your response. Do not provide any explanation or preamble. 

Example: 
Text Phrase: The quick brown fox
Word List:
1. jumps
2. is
3. leaps
4. goes
5. could

Response:
1. over the lazy dog
2. is red
3. leaps over the fence
4. goes around the barn
5. could have been a wolf
"""
    try:
        phrases_text = _call_gemini(prompt)
        if not phrases_text:
            return None
        return {
            "words_text": word_list,
            "phrases_text": phrases_text
        }
    except Exception as e:
        print(f"Error in fetch_next_phrases: {e}")
        return None

def parse_suggestions(words_text, phrases_text, next_words):
    """Step 3: Parses the raw text from the API into the state object."""
    
    # --- MODIFIED BLOCK ---
    # More robust parsing logic
    parsed_phrases = []
    for line in phrases_text.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        # Find the first period
        parts = line.split('.', 1)
        # Check if the part before the period is a number
        if len(parts) == 2 and parts[0].strip().isdigit():
            # Add the part after the period
            parsed_phrases.append(parts[1].strip())
    # --- END MODIFIED BLOCK ---
    
    suggestions = []
    for i, word in enumerate(next_words):
        if i >= len(parsed_phrases):
            phrase_text = "..." # Fallback
        else:
            phrase_text = parsed_phrases[i]

        # Remove the starting word and the ending period from the phrase
        if phrase_text.lower().startswith(word.lower() + " "):
            phrase_text = phrase_text[len(word):]
        if phrase_text.endswith('.'):
            phrase_text = phrase_text[:-1]
            
        suggestions.append({
            "word": word,
            "phrase": phrase_text.strip()
        })
    return suggestions[:10]

# Configure logging to output JSON
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
# Create a custom formatter to output JSON
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "jsonPayload": record.__dict__.get("json_payload", {}) # Custom field for your event data
        }
        return json.dumps(log_entry)

formatter = JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)


# --- Flask Routes ---

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/get_suggestions', methods=['POST'])
def get_suggestions_route():
    """API endpoint for the frontend to get suggestions."""
    data = request.get_json()
    typed_text = data.get('typedText', '')
    
    logger.info(
        "get_suggestions request received",
        extra={"json_payload": {"typedText": typed_text}}
    )

    try:
        # 1. Get 10 next words
        next_words = fetch_next_words(typed_text)
        if not next_words:
            logger.warning(
                "No next words found",
                extra={"json_payload": {"typedText": typed_text}}
            )
            return jsonify([]) # Return empty list if no words found

        # 2. Get completed phrases
        phrase_data = fetch_next_phrases(typed_text, next_words)
        if not phrase_data:
            logger.error(
                "Failed to fetch next phrases",
                extra={"json_payload": {"typedText": typed_text, "next_words": next_words}}
            )
            return jsonify([]) # Return empty list if phrases fail

        # 3. Parse and set state
        suggestions = parse_suggestions(phrase_data['words_text'], phrase_data['phrases_text'], next_words)
        
        logger.info("get_suggestions request successful", extra={"json_payload": {"typedText": typed_text, "suggestions": suggestions}})
        return jsonify(suggestions)

    except Exception as e:
        logger.error(f"Error in /get_suggestions: {e}", extra={"json_payload": {"typedText": typed_text, "error": str(e)}})
        return jsonify({"error": str(e)}), 500

@app.route('/log_event', methods=['POST'])
def log_event_route():
    event_data = request.get_json()
    # Log the event data using the configured logger
    logger.info("Client event occurred", extra={"json_payload": event_data})
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True)
