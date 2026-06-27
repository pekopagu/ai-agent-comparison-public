from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.database import get_connection
from app.schemas import TaskCreate, TaskUpdate


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def row_to_task(row: Any) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "priority": row["priority"],
        "due_date": row["due_date"],
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_tasks(status: str | None = None, priority: str | None = None, q: str | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if status == "active":
        clauses.append("completed = 0")
    elif status == "completed":
        clauses.append("completed = 1")

    if priority in {"low", "medium", "high"}:
        clauses.append("priority = ?")
        params.append(priority)

    if q:
        clauses.append("(title LIKE ? OR description LIKE ?)")
        keyword = f"%{q}%"
        params.extend([keyword, keyword])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"""
        SELECT * FROM tasks
        {where}
        ORDER BY
            completed ASC,
            CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
            CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
            due_date ASC,
            created_at DESC
    """

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [row_to_task(row) for row in rows]


def get_task(task_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_task(row) if row else None


def create_task(payload: TaskCreate) -> dict[str, Any]:
    now = utc_now()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO tasks (title, description, priority, due_date, completed, created_at, updated_at)
            VALUES (?, ?, ?, ?, 0, ?, ?)
            """,
            (
                payload.title.strip(),
                payload.description.strip(),
                payload.priority,
                payload.due_date.isoformat() if payload.due_date else None,
                now,
                now,
            ),
        )
        connection.commit()
        task_id = int(cursor.lastrowid)
    task = get_task(task_id)
    if task is None:
        raise RuntimeError("Created task could not be loaded")
    return task


def update_task(task_id: int, payload: TaskUpdate) -> dict[str, Any] | None:
    if get_task(task_id) is None:
        return None

    now = utc_now()
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, priority = ?, due_date = ?, completed = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                payload.title.strip(),
                payload.description.strip(),
                payload.priority,
                payload.due_date.isoformat() if payload.due_date else None,
                int(payload.completed),
                now,
                task_id,
            ),
        )
        connection.commit()
    return get_task(task_id)


def toggle_task(task_id: int) -> dict[str, Any] | None:
    task = get_task(task_id)
    if task is None:
        return None

    now = utc_now()
    with get_connection() as connection:
        connection.execute(
            "UPDATE tasks SET completed = ?, updated_at = ? WHERE id = ?",
            (0 if task["completed"] else 1, now, task_id),
        )
        connection.commit()
    return get_task(task_id)


def delete_task(task_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()
    return cursor.rowcount > 0
