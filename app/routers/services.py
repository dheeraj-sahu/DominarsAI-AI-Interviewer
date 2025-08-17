from fastapi import APIRouter, Request, Form, UploadFile, File,BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.utils import get_current_user, require_login
from app.services import question_generation
import PyPDF2
import io
import os
from datetime import datetime
from app.services.performance_evaluation import evaluate_transcript  

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")




# NEW: Helper function to run the analysis in the background
def run_video_analysis(video_path: str, output_dir: str):
    """
    Initializes and runs the video integrity analysis in the background.
    """
    from app.services.video_analysis import VideoIntegrityAnalyzer
    try:
        print(f"[{datetime.now()}] Starting background analysis for: {video_path}")
        analyzer = VideoIntegrityAnalyzer()
        analyzer.analyze_video(video_path, output_dir)
        print(f"[{datetime.now()}] Finished background analysis for: {video_path}")
    except Exception as e:
        # Log any errors that occur during the background task
        error_log_path = os.path.join(output_dir, "analysis_error.log")
        with open(error_log_path, "w") as f:
            f.write(f"Error during video analysis: {e}")
        print(f"[{datetime.now()}] ERROR in background analysis for {video_path}: {e}")


        

@router.get("/services", response_class=HTMLResponse)
async def services(request: Request):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    return templates.TemplateResponse("services.html", {"request": request, "user": get_current_user(request)})

@router.get("/services/start-interview", response_class=HTMLResponse)
async def start_interview_form(request: Request):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    return templates.TemplateResponse("interview_form.html", {"request": request, "user": get_current_user(request)})


@router.post("/services/start-interview", response_class=HTMLResponse)
async def submit_interview_form(request: Request, resume: UploadFile = File(...), job_role: str = Form(...)):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    # Extract text from PDF resume
    resume_bytes = await resume.read()
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(resume_bytes))
        resume_text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
        print("[DEBUG] Extracted Resume Text:\n", resume_text[:1000])  # Print first 1000 chars
    except Exception as e:
        print("[ERROR] PDF Extraction Failed:", e)
        return templates.TemplateResponse(
            "interview_form.html",
            {"request": request, "user": get_current_user(request), "error": f"Failed to extract text from PDF: {e}"}
        )
    # Generate questions using Gemini API
    raw_gemini_response = None
    try:
        # Patch question_generation to return both questions and raw response for debugging
        questions, raw_gemini_response = question_generation.generate_interview_questions(resume_text, job_role, return_raw=True)
        print("[DEBUG] Gemini Questions Response:", questions)
        print("[DEBUG] Gemini Raw Response:", raw_gemini_response)
    except Exception as e:
        print("[ERROR] Gemini API Call Failed:", e)
        return templates.TemplateResponse(
            "interview_form.html",
            {"request": request, "user": get_current_user(request), "error": str(e)}
        )
    # Show questions to user
    return templates.TemplateResponse(
        "interview_questions.html",
        {"request": request, "user": get_current_user(request), "questions": questions, "job_role": job_role, "raw_gemini_response": raw_gemini_response}
    )




from app.models.interview_history import InterviewHistory
from app.database import get_db
from fastapi import Depends


@router.post("/services/save-interview")
async def save_interview(
    request: Request,
    background_tasks: BackgroundTasks, # FastAPI injects this automatically
    video_file: UploadFile = File(...),
    transcript: UploadFile = File(...),
    job_role: str = Form(...),
    db=Depends(get_db)
):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect

    username = get_current_user(request)
    user_dir = f"user_data/{username}"
    os.makedirs(user_dir, exist_ok=True)

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(user_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)

    video_path = os.path.join(session_dir, "interview.mp4")
    transcript_path = os.path.join(session_dir, "transcript.txt")

    # Save files immediately
    with open(video_path, "wb") as f:
        f.write(await video_file.read())
    with open(transcript_path, "wb") as f:
        f.write(await transcript.read())

    # Save interview history to DB
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    dt_str = now.strftime("%Y-%m-%d %H:%M")
    report_path = os.path.join(session_dir, "proctoring_log.json")

    interview = InterviewHistory(
        username=username,
        role=job_role,
        date=date_str,
        time=time_str,
        datetime=dt_str,
        report_path=report_path
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    # MODIFIED: Schedule the heavy analysis to run in the background
    background_tasks.add_task(run_video_analysis, video_path, session_dir)
    background_tasks.add_task(run_performance_evaluation, transcript_path, session_dir)

    print(f"Interview {session_id} saved. Analysis scheduled in background.")
    # Return response to the user immediately
    return {"status": "success", "session_id": session_id, "message": "Upload successful! Analysis is processing in the background."}




def run_performance_evaluation(transcript_path: str, output_dir: str):
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_text = f.read()
        report_path = os.path.join(output_dir, "interview_report.json")
        evaluate_transcript(transcript_text, report_path)
        print(f"[{datetime.now()}] Performance evaluation saved to {report_path}")
    except Exception as e:
        err_path = os.path.join(output_dir, "evaluation_error.log")
        with open(err_path, "w") as ef:
            ef.write(f"Error during evaluation: {e}")
        print(f"[{datetime.now()}] ERROR during performance evaluation: {e}")