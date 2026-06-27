from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Task
from schemas import SortOrder, TaskCreate, TaskPriority, TaskRead, TaskSort, TaskStatus, TaskUpdate


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_task_or_404(task_id: int, db: Session) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@app.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = None,
    sort: TaskSort = TaskSort.created_at,
    order: SortOrder = SortOrder.desc,
    db: Session = Depends(get_db),
) -> list[Task]:
    stmt = select(Task)

    if status_filter is not None:
        stmt = stmt.where(Task.status == status_filter.value)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority.value)

    priority_rank = case(
        (Task.priority == "high", 3),
        (Task.priority == "medium", 2),
        (Task.priority == "low", 1),
        else_=0,
    )
    sort_columns = {
        TaskSort.created_at: Task.created_at,
        TaskSort.due_date: Task.due_date,
        TaskSort.priority: priority_rank,
    }
    sort_column = sort_columns[sort]
    stmt = stmt.order_by(sort_column.asc() if order == SortOrder.asc else sort_column.desc(), Task.id.asc())

    return list(db.scalars(stmt))


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> Task:
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)) -> Task:
    return get_task_or_404(task_id, db)


@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)) -> Task:
    task = get_task_or_404(task_id, db)
    for key, value in payload.model_dump().items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> None:
    task = get_task_or_404(task_id, db)
    db.delete(task)
    db.commit()
