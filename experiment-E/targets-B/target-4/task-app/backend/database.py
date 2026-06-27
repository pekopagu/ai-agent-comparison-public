"""データベース操作レイヤ（標準ライブラリ sqlite3 を使用）。"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# デフォルトのDBファイルパス（このファイルと同じディレクトリに配置）
DEFAULT_DB_PATH = Path(__file__).parent / "tasks.db"


def _now_iso() -> str:
    """現在時刻を ISO8601 文字列で返す。"""
    return datetime.now(timezone.utc).isoformat()


class Database:
    """SQLite データベースへの薄いラッパー。"""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        # ":memory:" を含む文字列やパスを許容する
        self.db_path = str(db_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # 外部キー制約を有効化（将来の拡張に備える）
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        """tasks テーブルが無ければ作成する。"""
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    completed INTEGER NOT NULL DEFAULT 0,
                    priority TEXT NOT NULL DEFAULT 'medium',
                    due_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # ------------------------------------------------------------------
    # CRUD 操作
    # ------------------------------------------------------------------
    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        due_date: Optional[str] = None,
    ) -> dict[str, Any]:
        now = _now_iso()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks
                    (title, description, completed, priority, due_date, created_at, updated_at)
                VALUES (?, ?, 0, ?, ?, ?, ?)
                """,
                (title, description, priority, due_date, now, now),
            )
            conn.commit()
            task_id = cursor.lastrowid
        return self.get_task(task_id)  # type: ignore[return-value]

    def list_tasks(
        self,
        status_filter: str = "all",
        search: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """タスク一覧を取得する。

        status_filter: "all" | "active"(未完了) | "completed"(完了)
        search: タイトル・説明文の部分一致検索キーワード
        """
        query = "SELECT * FROM tasks"
        conditions: list[str] = []
        params: list[Any] = []

        if status_filter == "active":
            conditions.append("completed = 0")
        elif status_filter == "completed":
            conditions.append("completed = 1")

        if search:
            conditions.append("(title LIKE ? OR description LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # 未完了を上に、その後は作成日時の新しい順
        query += " ORDER BY completed ASC, created_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def get_task(self, task_id: int) -> Optional[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        completed: Optional[bool] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        clear_due_date: bool = False,
    ) -> Optional[dict[str, Any]]:
        """タスクを部分更新する。指定された項目のみ更新する。"""
        existing = self.get_task(task_id)
        if existing is None:
            return None

        fields: list[str] = []
        params: list[Any] = []

        if title is not None:
            fields.append("title = ?")
            params.append(title)
        if description is not None:
            fields.append("description = ?")
            params.append(description)
        if completed is not None:
            fields.append("completed = ?")
            params.append(1 if completed else 0)
        if priority is not None:
            fields.append("priority = ?")
            params.append(priority)
        if clear_due_date:
            fields.append("due_date = ?")
            params.append(None)
        elif due_date is not None:
            fields.append("due_date = ?")
            params.append(due_date)

        # 更新項目が無ければ updated_at だけ更新する
        fields.append("updated_at = ?")
        params.append(_now_iso())

        params.append(task_id)
        with self._connect() as conn:
            conn.execute(
                f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params
            )
            conn.commit()
        return self.get_task(task_id)

    def toggle_task(self, task_id: int) -> Optional[dict[str, Any]]:
        """完了状態を反転する。"""
        existing = self.get_task(task_id)
        if existing is None:
            return None
        return self.update_task(task_id, completed=not existing["completed"])

    def delete_task(self, task_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
        return cursor.rowcount > 0

    def get_stats(self) -> dict[str, int]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            completed = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE completed = 1"
            ).fetchone()[0]
        return {
            "total": total,
            "completed": completed,
            "active": total - completed,
        }

    # ------------------------------------------------------------------
    # ヘルパー
    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        # SQLite は boolean を整数で保持するため変換する
        data["completed"] = bool(data["completed"])
        return data
