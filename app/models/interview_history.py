from sqlalchemy import Column, Integer, String, DateTime
from app.database import Base
from datetime import datetime

class InterviewHistory(Base):
    __tablename__ = "interview_history"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    role = Column(String(100), nullable=False)
    date = Column(String(20), nullable=False)
    time = Column(String(20), nullable=False)
    datetime = Column(String(40), nullable=False)
    report_path = Column(String(255), nullable=False)

