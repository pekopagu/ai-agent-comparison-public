from typing import Optional
from pydantic import BaseModel, Field

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="タスクのタイトル")
    description: Optional[str] = Field(None, description="タスクの詳細説明")
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="期限日 (YYYY-MM-DD)")
    priority: str = Field("medium", pattern="^(low|medium|high)$", description="優先度")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="タスクのタイトル")
    description: Optional[str] = Field(None, description="タスクの詳細説明")
    due_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="期限日 (YYYY-MM-DD)")
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$", description="優先度")
    status: Optional[str] = Field(None, pattern="^(todo|in_progress|done)$", description="ステータス")

class TaskResponse(TaskBase):
    id: int
    status: str
    created_at: str
    updated_at: str

    model_config = {
        "from_attributes": True
    }
