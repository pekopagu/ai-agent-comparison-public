from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field("#6366f1", max_length=50) # hex code default to indigo

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field("todo", max_length=50)
    priority: str = Field("medium", max_length=50)
    due_date: Optional[str] = None

class TaskCreate(TaskBase):
    tags: Optional[List[str]] = [] # Tag names

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=50)
    priority: Optional[str] = Field(None, max_length=50)
    due_date: Optional[str] = None
    tags: Optional[List[str]] = None # List of tag names to replace current ones

class Task(TaskBase):
    id: int
    created_at: str
    updated_at: str
    tags: List[Tag] = []

    model_config = ConfigDict(from_attributes=True)

class AnalyticsSummary(BaseModel):
    total_tasks: int
    todo_tasks: int
    in_progress_tasks: int
    done_tasks: int
    completion_rate: float # Percentage
    high_priority_tasks: int
    overdue_tasks: int
