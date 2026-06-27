"""Pydantic スキーマ定義（リクエスト/レスポンスのバリデーション）。"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Priority = Literal["low", "medium", "high"]


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="タスク名")
    description: Optional[str] = Field(None, max_length=2000, description="詳細説明")
    priority: Priority = Field("medium", description="優先度")
    due_date: Optional[str] = Field(None, description="期限日 (YYYY-MM-DD)")

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        """due_date が指定された場合は YYYY-MM-DD 形式か検証する。"""
        if v is None or v == "":
            return None
        try:
            date.fromisoformat(v)
        except ValueError as exc:
            raise ValueError("due_date は YYYY-MM-DD 形式で指定してください") from exc
        return v

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("title は空にできません")
        return stripped


class TaskCreate(TaskBase):
    """タスク作成リクエスト。"""


class TaskUpdate(BaseModel):
    """タスク更新リクエスト（全項目任意）。"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    completed: Optional[bool] = None
    priority: Optional[Priority] = None
    due_date: Optional[str] = None

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        try:
            date.fromisoformat(v)
        except ValueError as exc:
            raise ValueError("due_date は YYYY-MM-DD 形式で指定してください") from exc
        return v

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("title は空にできません")
        return stripped


class TaskResponse(BaseModel):
    """タスクレスポンス。"""

    id: int
    title: str
    description: Optional[str]
    completed: bool
    priority: str
    due_date: Optional[str]
    created_at: str
    updated_at: str


class StatsResponse(BaseModel):
    total: int
    completed: int
    active: int
