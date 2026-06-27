"""Pydantic スキーマ（リクエスト/レスポンスの検証・整形）。"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class Status(str, Enum):
    """タスクのステータス許容値。"""

    todo = "todo"
    doing = "doing"
    done = "done"


class Priority(str, Enum):
    """タスクの優先度許容値。"""

    low = "low"
    medium = "medium"
    high = "high"


class TaskBase(BaseModel):
    """タスクの共通フィールド。"""

    title: str
    description: Optional[str] = None
    status: Status = Status.todo
    priority: Priority = Priority.medium
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        """タイトルは空文字・空白のみを許可しない。"""
        if v is None or not v.strip():
            raise ValueError("title は必須です（空文字は不可）")
        if len(v) > 255:
            raise ValueError("title は255文字以内で入力してください")
        return v


class TaskCreate(TaskBase):
    """タスク作成リクエスト用スキーマ。"""


class TaskUpdate(BaseModel):
    """タスク更新リクエスト用スキーマ（部分更新に対応）。"""

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        """タイトルを指定する場合は空文字・空白のみを許可しない。"""
        if v is None:
            return v
        if not v.strip():
            raise ValueError("title は空文字にできません")
        if len(v) > 255:
            raise ValueError("title は255文字以内で入力してください")
        return v


class TaskResponse(TaskBase):
    """タスクレスポンス用スキーマ。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
