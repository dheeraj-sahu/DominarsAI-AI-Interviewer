
from fastapi import APIRouter, Request, Depends, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.utils import get_current_user, require_login
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


from app.models.interview_history import InterviewHistory
import os

# Load proctoring_log.json for the selected report
def get_report_by_id(report_id, db):
    report = db.query(InterviewHistory).filter(InterviewHistory.id == report_id).first()
    if not report:
        return None
    # Try to load proctoring_log.json
    proctoring_data = None
    interview_report_data = None
    session_dir = None
    video_url = None
    if report.report_path and os.path.exists(report.report_path):
        try:
            with open(report.report_path, "r", encoding="utf-8") as f:
                proctoring_data = json.load(f)
            session_dir = os.path.dirname(report.report_path)
            interview_report_path = os.path.join(session_dir, "interview_report.json")
            interview_video_path = os.path.join(session_dir, "interview.mp4")
            if os.path.exists(interview_report_path):
                with open(interview_report_path, "r", encoding="utf-8") as f2:
                    interview_report_data = json.load(f2)
            if os.path.exists(interview_video_path):
                base_dir = os.path.abspath(os.getcwd())
                rel_path = os.path.relpath(interview_video_path, base_dir)
                video_url = '/' + rel_path.replace('\\', '/').replace(' ', '%20')
        except Exception as e:
            proctoring_data = {"error": f"Could not load report: {e}"}
    else:
        proctoring_data = {"error": "Report file not found."}
    return {
        'id': report.id,
        'role': report.role,
        'date': report.date,
        'time': report.time,
        'datetime': report.datetime,
        'proctoring_log': proctoring_data,
        'interview_report': interview_report_data,
        'video_url': video_url
    }


from fastapi import Depends
from sqlalchemy.orm import Session

@router.get("/report/{report_id}", response_class=HTMLResponse, name="view_report")
async def view_report(request: Request, report_id: int = Path(...), db: Session = Depends(get_db)):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    report = get_report_by_id(report_id, db)
    if not report:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Report not found."})
    # Load performance evaluation (interview_report.json)
    performance_evaluation = None
    session_dir = None
    if 'proctoring_log' in report and report['proctoring_log']:
        # Try to infer session_dir from report_path if available
        # But since report_path is not in the dict, infer from proctoring_log path if possible
        # Otherwise, try to reconstruct from user_data
        # For now, try to find the session_dir from the proctoring_log path
        pass
    # If you have report_path/session_dir, use it:
    # session_dir = os.path.dirname(report['report_path'])
    # For now, try to reconstruct from user and date/time
    # (You may want to store report_path in InterviewHistory for reliability)
    # Try to find the session_dir by searching user_data
    # For now, try to use the proctoring_log path if available
    # (Assume proctoring_log.json is at .../user_data/<user>/<session>/proctoring_log.json)
    # and interview_report.json is at .../user_data/<user>/<session>/interview_report.json
    # If proctoring_log is a dict, skip
    proctoring_path = None
    if isinstance(report.get('proctoring_log'), dict) and 'error' not in report['proctoring_log']:
        # No path info, skip
        pass
    elif isinstance(report.get('proctoring_log'), str):
        proctoring_path = report['proctoring_log']
    # If you have the path, try to load interview_report.json
    if proctoring_path and os.path.exists(proctoring_path):
        session_dir = os.path.dirname(proctoring_path)
        perf_path = os.path.join(session_dir, "interview_report.json")
        if os.path.exists(perf_path):
            try:
                with open(perf_path, "r", encoding="utf-8") as f:
                    performance_evaluation = json.load(f)
            except Exception as e:
                performance_evaluation = {"error": f"Could not load performance evaluation: {e}"}
    username = get_current_user(request)
    return templates.TemplateResponse(
        "report_detail.html",
        {"request": request, "report": report, "user": username, "performance_evaluation": performance_evaluation}
    )

# Add custom filter for parsing JSON
def parse_json(text):
    if not text:
        return {}
    try:
        return json.loads(text)
    except:
        return {}

templates.env.filters["from_json"] = parse_json

@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "user": get_current_user(request)})

@router.get("/features", response_class=HTMLResponse)
async def features(request: Request):
    return templates.TemplateResponse("features.html", {"request": request, "user": get_current_user(request)})

@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    # Check if user is logged in, redirect to login if not
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect
    
    return templates.TemplateResponse("contact.html", {"request": request, "user": get_current_user(request)})

from app.models.interview_history import InterviewHistory

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    login_redirect = require_login(request)
    if login_redirect:
        return login_redirect

    username = get_current_user(request)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return RedirectResponse(url="/login")

    # Fetch interview history from DB
    reports = db.query(InterviewHistory).filter(InterviewHistory.username == username).all()
    reports_data = [
        {
            "id": r.id,
            "role": r.role,
            "date": r.date,
            "time": r.time,
            "datetime": r.datetime,
            "report_path": r.report_path
        } for r in reports
    ]

    return templates.TemplateResponse(
        "dashboard.html", 
        {
            "request": request, 
            "user": username, 
            "dashboard": True,
            "reports": reports_data
        }
    )