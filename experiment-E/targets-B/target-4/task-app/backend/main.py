"""FastAPI アプリケーション本体。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import Database
from .schemas import (
    StatsResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)

# 静的ファイル（フロントエンド）のディレクトリ
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app = FastAPI(
    title="タスク管理API",
    description="シンプルなタスク管理WebアプリのバックエンドAPI",
    version="1.0.0",
)

# シングルトンのDBインスタンス
_db = Database()


def get_db() -> Database:
    """DB依存性。テスト時にオーバーライドできるようにする。"""
    return _db


# ----------------------------------------------------------------------
# API エンドポイント
# ----------------------------------------------------------------------
@app.get("/api/health")
def health_check() -> dict[str, str]:
    """ヘルスチェック。"""
    return {"status": "ok"}


@app.get("/api/tasks", response_model=list[TaskResponse])
def list_tasks(
    filter: str = Query("all", pattern="^(all|active|completed)$"),
    search: Optional[str] = Query(None),
    db: Database = Depends(get_db),
) -> list[dict]:
    """タスク一覧を取得する。"""
    return db.list_tasks(status_filter=filter, search=search)


@app.post("/api/tasks", response_model=TaskResponse, status_code=201)
def create_task(payload: TaskCreate, db: Database = Depends(get_db)) -> dict:
    """新しいタスクを作成する。"""
    return db.create_task(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        due_date=payload.due_date,
    )


@app.get("/api/stats", response_model=StatsResponse)
def get_stats(db: Database = Depends(get_db)) -> dict:
    """統計情報を取得する。"""
    return db.get_stats()


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Database = Depends(get_db)) -> dict:
    """タスク単体を取得する。"""
    task = db.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return task


@app.put("/api/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int, payload: TaskUpdate, db: Database = Depends(get_db)
) -> dict:
    """タスクを更新する。"""
    # due_date を明示的に空にするケースを扱う
    update_fields = payload.model_dump(exclude_unset=True)
    clear_due_date = "due_date" in update_fields and update_fields["due_date"] is None

    updated = db.update_task(
        task_id,
        title=payload.title,
        description=payload.description,
        completed=payload.completed,
        priority=payload.priority,
        due_date=payload.due_date,
        clear_due_date=clear_due_date,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return updated


@app.patch("/api/tasks/{task_id}/toggle", response_model=TaskResponse)
def toggle_task(task_id: int, db: Database = Depends(get_db)) -> dict:
    """完了状態を切り替える。"""
    toggled = db.toggle_task(task_id)
    if toggled is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return toggled


@app.delete("/api/tasks/{task_id}", status_code=204, response_class=Response)
def delete_task(task_id: int, db: Database = Depends(get_db)) -> Response:
    """タスクを削除する。"""
    deleted = db.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return Response(status_code=204)


# ----------------------------------------------------------------------
# フロントエンド（静的ファイル）の配信
# ----------------------------------------------------------------------
@app.get("/")
def serve_index() -> FileResponse:
    """トップページ（index.html）を返す。"""
    return FileResponse(FRONTEND_DIR / "index.html")


# その他の静的アセット（CSS/JS）を配信
if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="static",
    )
