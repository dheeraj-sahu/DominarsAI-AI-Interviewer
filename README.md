# DominarsAI AI Interviewer

## Overview
DominarsAI AI Interviewer is a FastAPI-based web application for conducting AI-powered interviews. It supports resume upload, question generation, video recording, proctoring, performance evaluation, and secure report management.

---

## Features
- Resume upload and parsing
- AI-generated interview questions
- Video recording and proctoring (eye movement, extra faces, device monitoring)
- Performance evaluation and detailed report
- Interview history dashboard
- Secure user authentication
- Privacy-focused: No sensitive data tracked by git

---

## Folder Structure
```
app/
  config.py         # Configuration (loads secrets from .env)
  database.py       # Database setup
  main.py           # FastAPI entrypoint
  models/           # ORM models
  routers/          # API and page routers
  schemas/          # Pydantic schemas
  static/           # CSS, JS, images
  templates/        # Jinja2 HTML templates
myenv/              # Python virtual environment
user_data/          # Interview videos, reports, logs (excluded from git)
requirements.txt    # Python dependencies
.gitignore          # Excludes secrets, user data, DB
```

---

## Setup Instructions

### 1. Clone the Repository
```powershell
git clone https://github.com/dheeraj-sahu/DominarsAI-AI-Interviewer.git
cd DominarsAI-AI-Interviewer
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv myenv
myenv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
- Create a `.env` file in the project root.
- Add your secrets and credentials:
```
SECRET_KEY=your-secret-key
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
DATABASE_URL=sqlite:///./dominarsai.db
```

### 5. Run the Application
```powershell
python app/main.py
```
- The app will be available at `http://127.0.0.1:8000`

---

## Usage
- Sign up and log in.
- Upload your resume.
- Start the interview (video recording and proctoring enabled).
- View performance evaluation and proctoring logs in the report detail view.
- Access interview history and dashboard.

---

## Privacy & Security
- All secrets, credentials, and user data are excluded from git via `.gitignore`.
- Never commit `.env`, `user_data/`, or `dominarsai.db`.
- Sensitive config is loaded from environment variables only.

---

## Troubleshooting
- If you see `error: src refspec main does not match any`, use `git push -u origin master`.
- For missing dependencies, run `pip install -r requirements.txt`.
- For video or report issues, ensure `user_data/` is present and not tracked by git.

---

## License
MIT

---

## Authors
- Dheeraj Kumar
- Daksh Verma
