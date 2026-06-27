"""FastAPIアプリケーション本体（タスク管理API）"""
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import asc, case, desc
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, engine, get_db

# データベースのテーブルを作成
Base.metadata.create_all(bind=engine)

app = FastAPI(title="タスク管理API", version="1.0.0")

# CORS設定: フロントエンド（http://localhost:3000）からのアクセスを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 優先度のソート順（high > medium > low）を定義するためのマッピング
_PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}


@app.get("/tasks", response_model=List[schemas.TaskResponse])
def list_tasks(
    status_filter: Optional[schemas.StatusEnum] = Query(None, alias="status"),
    priority: Optional[schemas.PriorityEnum] = Query(None),
    sort: Optional[str] = Query(None, description="created_at / due_date / priority"),
    order: str = Query("asc", description="asc / desc"),
    db: Session = Depends(get_db),
):
    """タスク一覧取得（フィルタ・ソート対応）"""
    query = db.query(models.Task)

    # フィルタ
    if status_filter is not None:
        query = query.filter(models.Task.status == status_filter.value)
    if priority is not None:
        query = query.filter(models.Task.priority == priority.value)

    # ソート方向のバリデーション
    if order not in ("asc", "desc"):
        raise HTTPException(status_code=422, detail="orderはasc / descのいずれかを指定してください")
    direction = desc if order == "desc" else asc

    # ソート対象
    if sort is not None:
        if sort == "created_at":
            query = query.order_by(direction(models.Task.created_at))
        elif sort == "due_date":
            query = query.order_by(direction(models.Task.due_date))
        elif sort == "priority":
            # 優先度は文字列なので、数値に変換してソート
            priority_case = case(_PRIORITY_ORDER, value=models.Task.priority)
            query = query.order_by(direction(priority_case))
        else:
            raise HTTPException(
                status_code=422,
                detail="sortはcreated_at / due_date / priorityのいずれかを指定してください",
            )
    else:
        # デフォルトはID昇順
        query = query.order_by(asc(models.Task.id))

    return query.all()


@app.post("/tasks", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """タスク新規作成"""
    db_task = models.Task(
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority.value,
        due_date=task.due_date,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """タスク詳細取得"""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return db_task


@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)):
    """タスク更新（部分更新対応）"""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    # 送信されたフィールドのみ更新
    update_data = task.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Enum型は文字列値に変換して保存
        if isinstance(value, (schemas.StatusEnum, schemas.PriorityEnum)):
            value = value.value
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """タスク削除"""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    db.delete(db_task)
    db.commit()
    return None
