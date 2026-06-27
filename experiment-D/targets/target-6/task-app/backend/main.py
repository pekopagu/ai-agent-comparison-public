import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import case

import models, schemas, database
from database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Management API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/tasks", response_model=List[schemas.TaskResponse])
def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sort: Optional[str] = "created_at",
    order: Optional[str] = "asc",
    db: Session = Depends(get_db)
):
    query = db.query(models.Task)
    
    # Filtering
    if status:
        if status not in ["todo", "doing", "done"]:
            raise HTTPException(status_code=400, detail="Invalid status filter")
        query = query.filter(models.Task.status == status)
    
    if priority:
        if priority not in ["low", "medium", "high"]:
            raise HTTPException(status_code=400, detail="Invalid priority filter")
        query = query.filter(models.Task.priority == priority)
        
    # Sorting
    if sort == "priority":
        # high (1) -> medium (2) -> low (3) for asc
        priority_order = case(
            {
                "high": 1,
                "medium": 2,
                "low": 3
            },
            value=models.Task.priority,
            else_=4
        )
        if order == "desc":
            query = query.order_by(priority_order.desc())
        else:
            query = query.order_by(priority_order.asc())
    elif sort == "due_date":
        if order == "desc":
            query = query.order_by(models.Task.due_date.desc())
        else:
            query = query.order_by(models.Task.due_date.asc())
    elif sort == "created_at":
        if order == "desc":
            query = query.order_by(models.Task.created_at.desc())
        else:
            query = query.order_by(models.Task.created_at.asc())
    else:
        # Fallback to created_at desc if invalid sort
        query = query.order_by(models.Task.created_at.desc())
            
    return query.all()

@app.post("/tasks", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = models.Task(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/tasks/{id}", response_model=schemas.TaskResponse)
def get_task(id: int, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.put("/tasks/{id}", response_model=schemas.TaskResponse)
def update_task(id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update fields with provided values
    update_data = task.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
        
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{id}")
def delete_task(id: int, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    db.delete(db_task)
    db.commit()
    return {"detail": "Task deleted"}
