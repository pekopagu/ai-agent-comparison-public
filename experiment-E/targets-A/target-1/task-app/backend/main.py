# -*- coding: utf-8 -*-
from datetime import datetime
from typing import List, Optional, Literal
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import case

import models
import schemas
from database import engine, get_db

# データベースのテーブルを作成
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Management API")

# CORS 設定 (http://localhost:3000 からのアクセスを許可)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/tasks", response_model=List[schemas.TaskResponse])
def get_tasks(
    status_filter: Optional[Literal["todo", "doing", "done"]] = Query(None, alias="status"),
    priority_filter: Optional[Literal["low", "medium", "high"]] = Query(None, alias="priority"),
    sort: Optional[Literal["created_at", "due_date", "priority"]] = Query("created_at"),
    order: Optional[Literal["asc", "desc"]] = Query("asc"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Task)

    # フィルタ適用
    if status_filter:
        query = query.filter(models.Task.status == status_filter)
    if priority_filter:
        query = query.filter(models.Task.priority == priority_filter)

    # ソート適用
    if sort == "priority":
        # 優先度のカスタムソート (low -> medium -> high)
        priority_order = case(
            {
                "low": 1,
                "medium": 2,
                "high": 3
            },
            value=models.Task.priority
        )
        order_by_col = priority_order
    elif sort == "due_date":
        # due_dateがNULLのものをどう扱うか？
        # 一般的には、期限があるものを優先してソートし、期限なしを末尾にするか、デフォルトのSQLiteのNULLソート挙動に従う。
        # ここでは単純にSQLiteのデフォルト挙動に従う（SQLiteではNULLは最小値として扱われる）
        order_by_col = models.Task.due_date
    else:
        order_by_col = models.Task.created_at

    # 昇順・降順の適用
    if order == "desc":
        # NULLが最後にくるように考慮 (due_dateの降順ソートなど)
        if sort == "due_date":
            # SQLiteでNULLを最後に配置するテクニック
            query = query.order_by(models.Task.due_date.is_(None), models.Task.due_date.desc())
        else:
            query = query.order_by(order_by_col.desc())
    else:
        if sort == "due_date":
            # 昇順でもNULLは最後に配置する方が親切
            query = query.order_by(models.Task.due_date.is_(None), models.Task.due_date.asc())
        else:
            query = query.order_by(order_by_col.asc())

    return query.all()

@app.post("/tasks", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task_in: schemas.TaskCreate, db: Session = Depends(get_db)):
    db_task = models.Task(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        priority=task_in.priority,
        due_date=task_in.due_date,
        created_at=datetime.now()
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task_in: schemas.TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return {"detail": "Task deleted successfully", "id": task_id}
