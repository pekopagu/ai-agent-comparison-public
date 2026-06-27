from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.repository import create_task, delete_task, get_task, list_tasks, toggle_task, update_task
from app.schemas import Task, TaskCreate, TaskUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Task Manager", version="1.0.0", lifespan=lifespan)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/tasks", response_model=list[Task])
def api_list_tasks(
    status: str | None = Query(default=None, pattern="^(active|completed)$"),
    priority: str | None = Query(default=None, pattern="^(low|medium|high)$"),
    q: str | None = Query(default=None, max_length=120),
) -> list[dict]:
    return list_tasks(status=status, priority=priority, q=q)


@app.post("/api/tasks", response_model=Task, status_code=201)
def api_create_task(payload: TaskCreate) -> dict:
    return create_task(payload)


@app.get("/api/tasks/{task_id}", response_model=Task)
def api_get_task(task_id: int) -> dict:
    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/api/tasks/{task_id}", response_model=Task)
def api_update_task(task_id: int, payload: TaskUpdate) -> dict:
    task = update_task(task_id, payload)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/api/tasks/{task_id}/toggle", response_model=Task)
def api_toggle_task(task_id: int) -> dict:
    task = toggle_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/api/tasks/{task_id}", status_code=204, response_class=Response, response_model=None)
def api_delete_task(task_id: int) -> None:
    if not delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
