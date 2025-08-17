import os
import requests

GEMINI_API_KEY = ""
GEMINI_API_URL = ""


def generate_interview_questions(resume_text: str, job_role: str, num_questions: int = 8, return_raw: bool = False):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    prompt = f"""
    You are an expert interviewer. Generate {num_questions} technical and behavioral interview questions 
    for the job role '{job_role}', based on the following candidate resume:
    Name "Daksh Verma"

    ---
    {resume_text}
    ---

    Return only the questions as a numbered list.
    """

    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    response = requests.post(GEMINI_API_URL, headers=headers, params=params, json=payload)
    response.raise_for_status()

    result = response.json()

    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        questions = [q.strip() for q in text.split("\n") if q.strip()]
        return (questions, result) if return_raw else questions
    except Exception as e:
        if return_raw:
            return [], result
        raise RuntimeError(f"Failed to parse Gemini API response: {e}\nRaw response: {result}")
