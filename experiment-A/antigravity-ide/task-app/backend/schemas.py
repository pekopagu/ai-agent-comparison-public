# -*- coding: utf-8 -*-
from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="タスクのタイトル")
    description: Optional[str] = Field(None, description="タスクの詳細説明")
    status: Literal["todo", "doing", "done"] = Field("todo", description="タスクのステータス")
    priority: Literal["low", "medium", "high"] = Field("medium", description="タスクの優先度")
    due_date: Optional[date] = Field(None, description="タスクの期限日")

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[Literal["todo", "doing", "done"]] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    due_date: Optional[date] = None

class TaskResponse(TaskBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
