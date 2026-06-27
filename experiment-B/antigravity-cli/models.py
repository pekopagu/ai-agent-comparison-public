from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text
from database import Base

def get_utc_now_iso():
    return datetime.now(timezone.utc).isoformat()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high
    status = Column(String(20), nullable=False, default="todo")  # todo, in_progress, done
    created_at = Column(String(30), nullable=False, default=get_utc_now_iso)
    updated_at = Column(String(30), nullable=False, default=get_utc_now_iso, onupdate=get_utc_now_iso)
