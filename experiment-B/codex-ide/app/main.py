from pathlib import Path
import sqlite3
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import DEFAULT_DATABASE_PATH, get_db, init_db
from app import repository
from app.schemas import (
    HealthResponse,
    Priority,
    SortOrder,
    StatusFilter,
    Task,
    TaskCreate,
    TaskList,
    TaskUpdate,
)


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncIterator[None]:
    init_db(fastapi_app.state.database_path)
    yield


app = FastAPI(title="Task Flow API", version="1.0.0", lifespan=lifespan)
app.state.database_path = DEFAULT_DATABASE_PATH


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", database=str(app.state.database_path))


@app.get("/api/tasks", response_model=TaskList)
def list_tasks(
    status: StatusFilter = StatusFilter.all,
    priority: Priority | None = Query(default=None),
    q: str | None = Query(default=None, max_length=120),
    sort: SortOrder = SortOrder.created_desc,
    connection: sqlite3.Connection = Depends(get_db),
) -> dict:
    return repository.list_tasks(connection, status=status, priority=priority, q=q, sort=sort)


@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate, connection: sqlite3.Connection = Depends(get_db)) -> dict:
    return repository.create_task(connection, payload)


@app.get("/api/tasks/{task_id}", response_model=Task)
def get_task(task_id: int, connection: sqlite3.Connection = Depends(get_db)) -> dict:
    task = repository.get_task(connection, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/api/tasks/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    connection: sqlite3.Connection = Depends(get_db),
) -> dict:
    task = repository.update_task(connection, task_id, payload)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/api/tasks/{task_id}/toggle", response_model=Task)
def toggle_task(task_id: int, connection: sqlite3.Connection = Depends(get_db)) -> dict:
    task = repository.toggle_task(connection, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, connection: sqlite3.Connection = Depends(get_db)) -> Response:
    deleted = repository.delete_task(connection, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)
