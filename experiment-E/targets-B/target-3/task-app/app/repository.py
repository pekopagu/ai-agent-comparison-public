from datetime import UTC, datetime
import sqlite3

from app.schemas import Priority, SortOrder, StatusFilter, TaskCreate, TaskUpdate


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _row_to_task(row: sqlite3.Row) -> dict:
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


def create_task(connection: sqlite3.Connection, payload: TaskCreate) -> dict:
    timestamp = _now()
    cursor = connection.execute(
        """
        INSERT INTO tasks (title, description, priority, due_date, completed, created_at, updated_at)
        VALUES (?, ?, ?, ?, 0, ?, ?)
        """,
        (
            payload.title,
            payload.description,
            payload.priority.value,
            payload.due_date.isoformat() if payload.due_date else None,
            timestamp,
            timestamp,
        ),
    )
    connection.commit()
    return get_task(connection, cursor.lastrowid)


def get_task(connection: sqlite3.Connection, task_id: int) -> dict | None:
    row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return _row_to_task(row) if row else None


def list_tasks(
    connection: sqlite3.Connection,
    status: StatusFilter = StatusFilter.all,
    priority: Priority | None = None,
    q: str | None = None,
    sort: SortOrder = SortOrder.created_desc,
) -> dict:
    where: list[str] = []
    params: list[object] = []

    if status == StatusFilter.active:
        where.append("completed = 0")
    elif status == StatusFilter.completed:
        where.append("completed = 1")

    if priority is not None:
        where.append("priority = ?")
        params.append(priority.value)

    if q:
        where.append("(LOWER(title) LIKE ? OR LOWER(description) LIKE ?)")
        term = f"%{q.strip().lower()}%"
        params.extend([term, term])

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    order_sql = {
        SortOrder.created_desc: "created_at DESC, id DESC",
        SortOrder.created_asc: "created_at ASC, id ASC",
        SortOrder.due_asc: "due_date IS NULL, due_date ASC, created_at DESC",
        SortOrder.due_desc: "due_date IS NULL, due_date DESC, created_at DESC",
        SortOrder.priority: "CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC",
    }[sort]

    rows = connection.execute(
        f"SELECT * FROM tasks {where_sql} ORDER BY {order_sql}",
        params,
    ).fetchall()
    summary = connection.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN completed = 0 THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) AS completed
        FROM tasks
        """
    ).fetchone()

    return {
        "items": [_row_to_task(row) for row in rows],
        "total": summary["total"] or 0,
        "active": summary["active"] or 0,
        "completed": summary["completed"] or 0,
    }


def update_task(connection: sqlite3.Connection, task_id: int, payload: TaskUpdate) -> dict | None:
    current = get_task(connection, task_id)
    if current is None:
        return None

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return current

    columns: list[str] = []
    params: list[object] = []
    for key, value in updates.items():
        columns.append(f"{key} = ?")
        if key == "priority" and value is not None:
            params.append(value.value)
        elif key == "due_date" and value is not None:
            params.append(value.isoformat())
        elif key == "completed" and value is not None:
            params.append(1 if value else 0)
        else:
            params.append(value)

    columns.append("updated_at = ?")
    params.append(_now())
    params.append(task_id)

    connection.execute(f"UPDATE tasks SET {', '.join(columns)} WHERE id = ?", params)
    connection.commit()
    return get_task(connection, task_id)


def toggle_task(connection: sqlite3.Connection, task_id: int) -> dict | None:
    current = get_task(connection, task_id)
    if current is None:
        return None

    connection.execute(
        "UPDATE tasks SET completed = ?, updated_at = ? WHERE id = ?",
        (0 if current["completed"] else 1, _now(), task_id),
    )
    connection.commit()
    return get_task(connection, task_id)


def delete_task(connection: sqlite3.Connection, task_id: int) -> bool:
    cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    connection.commit()
    return cursor.rowcount > 0
