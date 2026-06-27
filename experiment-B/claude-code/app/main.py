"""FastAPI アプリ本体。

タスクの CRUD・統計・ヘルスチェック API と、静的フロントエンドの配信を行う。
"""

from __future__ import annotations

import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import get_connection, init_db
from .schemas import Stats, Status, Task, TaskCreate, TaskUpdate

# 静的ファイル（フロントエンド）ディレクトリ
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時に DB を初期化する（lifespan イベント）。"""
    init_db()
    yield


app = FastAPI(
    title="タスク管理API",
    description="シンプルなタスク管理アプリのバックエンド API",
    version="1.0.0",
    lifespan=lifespan,
)


def _now_iso() -> str:
    """現在時刻を UTC の ISO 8601 文字列で返す。"""
    return datetime.now(timezone.utc).isoformat()


def _row_to_task(row: sqlite3.Row) -> dict:
    """SQLite の行を dict に変換する。"""
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "priority": row["priority"],
        "due_date": row["due_date"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# ---------------------------------------------------------------------------
# API エンドポイント
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health() -> dict:
    """ヘルスチェック。"""
    return {"status": "ok"}


@app.get("/api/tasks", response_model=list[Task])
def list_tasks(
    status: Optional[Status] = Query(None, description="ステータスで絞り込み"),
    q: Optional[str] = Query(None, description="タイトル・説明のキーワード検索"),
    sort: str = Query("created_at", description="並び替えキー"),
    order: str = Query("desc", description="asc / desc"),
) -> list[dict]:
    """タスク一覧を取得する（絞り込み・検索・並び替え対応）。"""
    # SQL インジェクション防止のため、ソートキー・順序はホワイトリストで検証
    allowed_sort = {"created_at", "updated_at", "due_date", "priority", "title", "id"}
    if sort not in allowed_sort:
        raise HTTPException(status_code=400, detail=f"sort は {sorted(allowed_sort)} のいずれか")
    order_norm = order.lower()
    if order_norm not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="order は asc / desc のいずれか")

    clauses: list[str] = []
    params: list = []
    if status is not None:
        clauses.append("status = ?")
        params.append(status.value)
    if q:
        clauses.append("(title LIKE ? OR IFNULL(description, '') LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    # priority は文字列なので、優先度順に意味のある並びにするための CASE を用意
    if sort == "priority":
        order_expr = (
            "CASE priority WHEN 'high' THEN 3 WHEN 'medium' THEN 2 "
            "WHEN 'low' THEN 1 ELSE 0 END"
        )
    else:
        order_expr = sort

    sql = f"SELECT * FROM tasks {where} ORDER BY {order_expr} {order_norm.upper()}"

    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [_row_to_task(r) for r in rows]


@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate) -> dict:
    """タスクを新規作成する。"""
    now = _now_iso()
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO tasks (title, description, status, priority, due_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.title,
                payload.description,
                payload.status.value,
                payload.priority.value,
                payload.due_date,
                now,
                now,
            ),
        )
        conn.commit()
        new_id = cur.lastrowid
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,)).fetchone()
    finally:
        conn.close()
    return _row_to_task(row)


@app.get("/api/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> dict:
    """タスクを1件取得する。"""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    return _row_to_task(row)


@app.put("/api/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate) -> dict:
    """タスクを更新する（部分更新）。"""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="タスクが見つかりません")

        # 指定されたフィールドのみ更新する
        data = payload.model_dump(exclude_unset=True)
        fields: list[str] = []
        params: list = []
        for key in ("title", "description", "status", "priority", "due_date"):
            if key in data:
                value = data[key]
                # Enum は .value を保存
                if hasattr(value, "value"):
                    value = value.value
                fields.append(f"{key} = ?")
                params.append(value)

        if fields:
            fields.append("updated_at = ?")
            params.append(_now_iso())
            params.append(task_id)
            conn.execute(
                f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", params
            )
            conn.commit()

        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    finally:
        conn.close()
    return _row_to_task(row)


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int) -> Response:
    """タスクを削除する。"""
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="タスクが見つかりません")
    finally:
        conn.close()
    return Response(status_code=204)


@app.get("/api/stats", response_model=Stats)
def stats() -> dict:
    """ステータス別の件数統計を返す。"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS cnt FROM tasks GROUP BY status"
        ).fetchall()
    finally:
        conn.close()
    counts = {r["status"]: r["cnt"] for r in rows}
    todo = counts.get("todo", 0)
    doing = counts.get("doing", 0)
    done = counts.get("done", 0)
    return {"total": todo + doing + done, "todo": todo, "doing": doing, "done": done}


# ---------------------------------------------------------------------------
# 静的フロントエンドの配信
# ---------------------------------------------------------------------------


@app.get("/")
def index() -> FileResponse:
    """フロントエンド（index.html）を返す。"""
    return FileResponse(_STATIC_DIR / "index.html")


# /static 以下の配信（CSS/JS を増やした場合に備える）
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
