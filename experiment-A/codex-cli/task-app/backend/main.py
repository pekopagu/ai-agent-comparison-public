from __future__ import annotations

from contextlib import asynccontextmanager, closing
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware

from database import get_connection, init_db
from models import ORDERS, PRIORITIES, SORT_FIELDS, STATUSES
from schemas import Task, TaskCreate, TaskUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Task Management API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def row_to_task(row) -> Task:
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    data = dict(row)
    if data["due_date"] is not None:
        data["due_date"] = date.fromisoformat(data["due_date"])
    return Task(**data)


def fetch_task(task_id: int) -> Task:
    with closing(get_connection()) as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_task(row)


@app.get("/tasks", response_model=list[Task])
def list_tasks(
    status_filter: Literal["todo", "doing", "done"] | None = Query(default=None, alias="status"),
    priority: Literal["low", "medium", "high"] | None = None,
    sort: Literal["created_at", "due_date", "priority"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> list[Task]:
    where_clauses: list[str] = []
    params: list[str] = []

    if status_filter is not None:
        where_clauses.append("status = ?")
        params.append(status_filter)
    if priority is not None:
        where_clauses.append("priority = ?")
        params.append(priority)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    direction = "ASC" if order == "asc" else "DESC"
    if sort == "priority":
        sort_sql = (
            "CASE priority WHEN 'high' THEN 3 WHEN 'medium' THEN 2 WHEN 'low' THEN 1 END"
        )
    else:
        sort_sql = sort

    sql = f"SELECT * FROM tasks {where_sql} ORDER BY {sort_sql} {direction}, id {direction}"
    with closing(get_connection()) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [row_to_task(row) for row in rows]


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate) -> Task:
    with closing(get_connection()) as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, status, priority, due_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                task.title,
                task.description,
                task.status,
                task.priority,
                task.due_date.isoformat() if task.due_date else None,
            ),
        )
        conn.commit()
        task_id = cursor.lastrowid
    return fetch_task(task_id)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> Task:
    return fetch_task(task_id)


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskUpdate) -> Task:
    fetch_task(task_id)
    updates = task.model_dump(exclude_unset=True)
    if not updates:
        return fetch_task(task_id)

    assignments: list[str] = []
    params: list[str | None] = []
    for key, value in updates.items():
        assignments.append(f"{key} = ?")
        if key == "due_date" and value is not None:
            params.append(value.isoformat())
        else:
            params.append(value)
    params.append(str(task_id))

    with closing(get_connection()) as conn:
        conn.execute(f"UPDATE tasks SET {', '.join(assignments)} WHERE id = ?", params)
        conn.commit()
    return fetch_task(task_id)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_task(task_id: int) -> Response:
    with closing(get_connection()) as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


init_db()
