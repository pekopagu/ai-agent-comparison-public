from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

# Many-to-many association table
task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String(50), nullable=False, default="todo") # 'todo', 'in_progress', 'done'
    priority = Column(String(50), nullable=False, default="medium") # 'low', 'medium', 'high'
    due_date = Column(String(50), nullable=True) # YYYY-MM-DD
    created_at = Column(String(50), nullable=False) # ISO 8601
    updated_at = Column(String(50), nullable=False) # ISO 8601

    # Relationship to tags
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(50), nullable=False) # Hex color string, e.g. '#6366f1'

    # Back-reference to tasks
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")
