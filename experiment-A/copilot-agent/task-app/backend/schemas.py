"""Pydanticスキーマ（リクエスト/レスポンスのバリデーション）"""
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StatusEnum(str, Enum):
    """ステータスの許容値"""

    todo = "todo"
    doing = "doing"
    done = "done"


class PriorityEnum(str, Enum):
    """優先度の許容値"""

    low = "low"
    medium = "medium"
    high = "high"


class TaskBase(BaseModel):
    """タスクの共通フィールド"""

    title: str = Field(..., min_length=1, max_length=255, description="タスク名")
    description: Optional[str] = Field(None, description="説明")
    status: StatusEnum = Field(default=StatusEnum.todo, description="ステータス")
    priority: PriorityEnum = Field(default=PriorityEnum.medium, description="優先度")
    due_date: Optional[date] = Field(None, description="期限")


class TaskCreate(TaskBase):
    """タスク作成用スキーマ"""


class TaskUpdate(BaseModel):
    """タスク更新用スキーマ（部分更新を許可）"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[StatusEnum] = None
    priority: Optional[PriorityEnum] = None
    due_date: Optional[date] = None


class TaskResponse(TaskBase):
    """タスクレスポンス用スキーマ"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
