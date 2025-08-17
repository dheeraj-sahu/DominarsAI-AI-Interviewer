from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app.routers import  auth, user, pages,services
# Import models to ensure tables are created
from app.models import user as user_model
from app.models.interview_history import InterviewHistory
import os

app = FastAPI(title="DominarsAI API")


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
# Serve user_data as static files
user_data_path = os.path.join(os.getcwd(), "user_data")
app.mount("/user_data", StaticFiles(directory=user_data_path), name="user_data")

Base.metadata.create_all(bind=engine)

from app.routers import pages
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(services.router)

# app.include_router(edit.router)

from app.config import settings
import os
print(f"DATABASE_URL from config: {settings.DATABASE_URL}")
print(f"Current working directory: {os.getcwd()}")