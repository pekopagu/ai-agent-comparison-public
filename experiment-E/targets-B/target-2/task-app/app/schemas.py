"""Pydantic スキーマ定義。

API の入出力データのバリデーションと整形を担当する。
ステータス・優先度は固定値に制限する。
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Status(str, Enum):
    """タスクの進捗ステータス。"""

    todo = "todo"
    doing = "doing"
    done = "done"


class Priority(str, Enum):
    """タスクの優先度。"""

    low = "low"
    medium = "medium"
    high = "high"


class TaskCreate(BaseModel):
    """タスク作成時の入力スキーマ。"""

    title: str = Field(..., min_length=1, max_length=200, description="タスクのタイトル")
    description: Optional[str] = Field(None, max_length=2000, description="詳細説明")
    status: Status = Field(Status.todo, description="進捗ステータス")
    priority: Priority = Field(Priority.medium, description="優先度")
    due_date: Optional[str] = Field(None, description="期限 (YYYY-MM-DD)")

    @field_validator("title")
    @classmethod
    def _strip_title(cls, v: str) -> str:
        """前後の空白を除去し、空文字を弾く。"""
        v = v.strip()
        if not v:
            raise ValueError("title は空にできません")
        return v

    @field_validator("due_date")
    @classmethod
    def _validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        """due_date が指定された場合は YYYY-MM-DD 形式か検証する。"""
        if v is None or v == "":
            return None
        from datetime import date

        try:
            date.fromisoformat(v)
        except ValueError as exc:
            raise ValueError("due_date は YYYY-MM-DD 形式で指定してください") from exc
        return v


class TaskUpdate(BaseModel):
    """タスク更新時の入力スキーマ（すべて任意 = 部分更新）。"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    due_date: Optional[str] = None

    @field_validator("title")
    @classmethod
    def _strip_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("title は空にできません")
        return v

    @field_validator("due_date")
    @classmethod
    def _validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        from datetime import date

        try:
            date.fromisoformat(v)
        except ValueError as exc:
            raise ValueError("due_date は YYYY-MM-DD 形式で指定してください") from exc
        return v


class Task(BaseModel):
    """タスクの出力スキーマ。"""

    id: int
    title: str
    description: Optional[str]
    status: Status
    priority: Priority
    due_date: Optional[str]
    created_at: str
    updated_at: str


class Stats(BaseModel):
    """件数統計の出力スキーマ。"""

    total: int
    todo: int
    doing: int
    done: int
