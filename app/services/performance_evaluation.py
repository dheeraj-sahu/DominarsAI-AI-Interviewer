import os
import requests
import json

# It is highly recommended to use an environment variable for your API key.
GEMINI_API_KEY = "AIzaSyA2rMfuyCrYhoeMYUXu7na4yCLKa-_7I2Q"

# Using a valid, fast model name
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

def evaluate_transcript(transcript_text: str, output_path: str):
    """
    Sends transcript text to Gemini API for performance evaluation,
    saves result as interview_report.json at output_path.
    """
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    # The prompt remains the same, instructing the model to return JSON.
    prompt = f"""
    You are an AI interview evaluator. Evaluate the following interview transcript based on these criteria:
    1. Confidence (1–10)
    2. Clarity (1–10)
    3. Technical Knowledge (1–10)
    
    For each question and answer, provide scores and concise feedback. At the end, provide an overall summary with average scores and actionable improvement suggestions.
    
    Return output in strict JSON format.

    Transcript:
    ---
    {transcript_text}
    ---
    """

    headers = { "Content-Type": "application/json" }
    params = { "key": GEMINI_API_KEY }
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        # Requesting JSON output directly increases reliability
        "generationConfig": {"response_mime_type": "application/json"},
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    }

    ai_text = ""
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        
        ai_text = data["candidates"][0]["content"]["parts"][0]["text"]
        
        # --- FIX APPLIED HERE: Clean the string before parsing ---
        # Find the start and end of the JSON object within the text
        start = ai_text.find('{')
        end = ai_text.rfind('}') + 1
        
        if start == -1 or end == 0:
            raise ValueError("Could not find a valid JSON object in the API response.")
            
        # Slice the string to get only the JSON part
        clean_json_str = ai_text[start:end]
        
        # Parse the cleaned string
        parsed_json = json.loads(clean_json_str)
        # --- END OF FIX ---

        with open(output_path, "w") as f:
            json.dump(parsed_json, f, indent=4)
            
        print(f"Successfully evaluated transcript and saved report to {output_path}")
        return parsed_json

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response body: {response.text}")
        raise
    except Exception as e:
        # The error message now includes the cleaned string for better debugging
        raise RuntimeError(f"Failed to parse Gemini output: {e}\nRAW: {ai_text}")