import os
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import engine, Base, get_db
from backend import crud, schemas

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Task Management API",
    description="Backend API for the Task Management Web Application",
    version="1.0.0"
)

# CORS middleware config to allow development server connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Task API Endpoints ---

@app.get("/api/tasks", response_model=List[schemas.Task])
def read_tasks(
    status: Optional[str] = Query(None, description="Filter by status (todo, in_progress, done)"),
    priority: Optional[str] = Query(None, description="Filter by priority (low, medium, high)"),
    tag: Optional[str] = Query(None, description="Filter by tag name"),
    search: Optional[str] = Query(None, description="Search term in title or description"),
    db: Session = Depends(get_db)
):
    try:
        tasks = crud.get_tasks(db, status=status, priority=priority, tag=tag, search=search)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasks", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_task(db=db, task_in=task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tasks/{task_id}", response_model=schemas.Task)
def read_task(task_id: int, db: Session = Depends(get_db)):
    db_task = crud.get_task_by_id(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.put("/api/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = crud.update_task(db=db, task_id=task_id, task_in=task)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    success = crud.delete_task(db=db, task_id=task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return None

# --- Tag API Endpoints ---

@app.get("/api/tags", response_model=List[schemas.Tag])
def read_tags(db: Session = Depends(get_db)):
    try:
        return crud.get_tags(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tags", response_model=schemas.Tag, status_code=status.HTTP_201_CREATED)
def create_tag(tag: schemas.TagCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_tag(db=db, tag_in=tag)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    success = crud.delete_tag(db=db, tag_id=tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return None

# --- Analytics API Endpoint ---

@app.get("/api/analytics", response_model=schemas.AnalyticsSummary)
def get_analytics(db: Session = Depends(get_db)):
    try:
        return crud.get_analytics(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Serve Static Frontend Files ---
# Create the frontend directory if it doesn't exist
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
os.makedirs(frontend_dir, exist_ok=True)

# Mount the static files directory at "/" root.
# NOTE: This must be mounted last so that API routes are evaluated first!
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
