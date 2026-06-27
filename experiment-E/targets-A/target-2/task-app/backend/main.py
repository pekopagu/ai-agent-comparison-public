"""FastAPI アプリケーション本体。タスク CRUD と フィルタ・ソート を提供する。"""

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import case
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, engine, get_db

# テーブルを作成（存在しない場合のみ）
Base.metadata.create_all(bind=engine)

app = FastAPI(title="タスク管理API", version="1.0.0")

# CORS 設定: フロントエンド（http://localhost:3000）からのアクセスを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 優先度を数値に変換するためのマッピング（ソート用: low < medium < high）
PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}


@app.get("/tasks", response_model=List[schemas.TaskResponse])
def list_tasks(
    status: Optional[schemas.Status] = None,
    priority: Optional[schemas.Priority] = None,
    sort: Optional[str] = Query(default="created_at"),
    order: Optional[str] = Query(default="asc"),
    db: Session = Depends(get_db),
):
    """タスク一覧を取得する。status / priority でフィルタ、sort / order で並び替えが可能。"""
    query = db.query(models.Task)

    # フィルタ
    if status is not None:
        query = query.filter(models.Task.status == status.value)
    if priority is not None:
        query = query.filter(models.Task.priority == priority.value)

    # ソート対象カラムの決定
    allowed_sort = {"created_at", "due_date", "priority"}
    if sort not in allowed_sort:
        raise HTTPException(
            status_code=422,
            detail=f"sort は {sorted(allowed_sort)} のいずれかを指定してください",
        )
    if order not in {"asc", "desc"}:
        raise HTTPException(
            status_code=422,
            detail="order は asc / desc のいずれかを指定してください",
        )

    descending = order == "desc"

    if sort == "priority":
        # 優先度は文字列のため、明示的な順序（low<medium<high）で並べ替える
        sort_expr = case(PRIORITY_ORDER, value=models.Task.priority)
    elif sort == "due_date":
        sort_expr = models.Task.due_date
    else:
        sort_expr = models.Task.created_at

    sort_expr = sort_expr.desc() if descending else sort_expr.asc()
    query = query.order_by(sort_expr)

    return query.all()


@app.post("/tasks", response_model=schemas.TaskResponse, status_code=201)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """新規タスクを作成する。"""
    db_task = models.Task(
        title=task.title.strip(),
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
    """指定 ID のタスク詳細を取得する。"""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return db_task


@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int, task: schemas.TaskUpdate, db: Session = Depends(get_db)
):
    """指定 ID のタスクを更新する（部分更新に対応）。"""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    update_data = task.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Enum 値は文字列に変換して保存する
        if isinstance(value, schemas.Status) or isinstance(value, schemas.Priority):
            value = value.value
        if field == "title" and isinstance(value, str):
            value = value.strip()
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """指定 ID のタスクを削除する。"""
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    db.delete(db_task)
    db.commit()
    return None


@app.get("/")
def root():
    """ヘルスチェック用エンドポイント。"""
    return {"message": "タスク管理API は稼働中です"}
