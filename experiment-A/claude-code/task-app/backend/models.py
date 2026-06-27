"""SQLAlchemy のデータモデル定義。"""

from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Integer, String, Text

from database import Base


class Task(Base):
    """タスクテーブルのモデル。"""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(10), nullable=False, default="todo")
    priority = Column(String(10), nullable=False, default="medium")
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
