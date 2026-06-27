"""タスク管理 API の pytest テスト。

テスト用に環境変数で独立した一時 SQLite DB を割り当て、本番 DB を汚さない。
このファイルが import される前に ``TASKS_DB_PATH`` を設定する必要があるため、
conftest 相当の処理をモジュール先頭で行う。
"""

from __future__ import annotations

import os
import tempfile

import pytest

# app の import より前にテスト用 DB パスを設定する
_TMP_DB = os.path.join(tempfile.gettempdir(), "tasks_test.db")
os.environ["TASKS_DB_PATH"] = _TMP_DB

from fastapi.testclient import TestClient  # noqa: E402

from app.database import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    """各テスト前に DB を作り直してクリーンな状態にする。"""
    if os.path.exists(_TMP_DB):
        os.remove(_TMP_DB)
    init_db()
    yield
    if os.path.exists(_TMP_DB):
        os.remove(_TMP_DB)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# ヘルパ
# ---------------------------------------------------------------------------

def _create(client, **overrides):
    payload = {"title": "テストタスク", "priority": "medium", "status": "todo"}
    payload.update(overrides)
    return client.post("/api/tasks", json=payload)


# ---------------------------------------------------------------------------
# health / stats
# ---------------------------------------------------------------------------

def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_stats_empty(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    assert res.json() == {"total": 0, "todo": 0, "doing": 0, "done": 0}


def test_stats_counts(client):
    _create(client, status="todo")
    _create(client, status="doing")
    _create(client, status="done")
    _create(client, status="done")
    res = client.get("/api/stats")
    assert res.json() == {"total": 4, "todo": 1, "doing": 1, "done": 2}


# ---------------------------------------------------------------------------
# CRUD 正常系
# ---------------------------------------------------------------------------

def test_create_task(client):
    res = _create(client, title="買い物に行く", description="牛乳と卵", priority="high", due_date="2026-07-01")
    assert res.status_code == 201
    body = res.json()
    assert body["id"] > 0
    assert body["title"] == "買い物に行く"
    assert body["description"] == "牛乳と卵"
    assert body["priority"] == "high"
    assert body["status"] == "todo"
    assert body["due_date"] == "2026-07-01"
    assert body["created_at"]
    assert body["updated_at"]


def test_get_task(client):
    created = _create(client, title="単体取得").json()
    res = client.get(f"/api/tasks/{created['id']}")
    assert res.status_code == 200
    assert res.json()["title"] == "単体取得"


def test_list_tasks(client):
    _create(client, title="A")
    _create(client, title="B")
    res = client.get("/api/tasks")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_update_task(client):
    created = _create(client, title="更新前").json()
    res = client.put(
        f"/api/tasks/{created['id']}",
        json={"title": "更新後", "status": "doing"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "更新後"
    assert body["status"] == "doing"
    # 指定していない priority は維持される
    assert body["priority"] == "medium"


def test_partial_update_keeps_other_fields(client):
    created = _create(client, title="保持テスト", description="残る説明", priority="high").json()
    res = client.put(f"/api/tasks/{created['id']}", json={"status": "done"})
    body = res.json()
    assert body["status"] == "done"
    assert body["description"] == "残る説明"
    assert body["priority"] == "high"


def test_delete_task(client):
    created = _create(client).json()
    res = client.delete(f"/api/tasks/{created['id']}")
    assert res.status_code == 204
    # 削除後は取得できない
    assert client.get(f"/api/tasks/{created['id']}").status_code == 404


# ---------------------------------------------------------------------------
# 異常系
# ---------------------------------------------------------------------------

def test_create_empty_title(client):
    res = _create(client, title="   ")
    assert res.status_code == 422


def test_create_invalid_status(client):
    res = _create(client, status="unknown")
    assert res.status_code == 422


def test_create_invalid_priority(client):
    res = _create(client, priority="urgent")
    assert res.status_code == 422


def test_create_invalid_due_date(client):
    res = _create(client, due_date="2026/07/01")
    assert res.status_code == 422


def test_get_nonexistent(client):
    assert client.get("/api/tasks/9999").status_code == 404


def test_update_nonexistent(client):
    assert client.put("/api/tasks/9999", json={"title": "x"}).status_code == 404


def test_delete_nonexistent(client):
    assert client.delete("/api/tasks/9999").status_code == 404


# ---------------------------------------------------------------------------
# フィルタ・検索・ソート
# ---------------------------------------------------------------------------

def test_filter_by_status(client):
    _create(client, title="todo1", status="todo")
    _create(client, title="done1", status="done")
    res = client.get("/api/tasks?status=done")
    bodies = res.json()
    assert len(bodies) == 1
    assert bodies[0]["title"] == "done1"


def test_search_by_keyword(client):
    _create(client, title="りんごを買う")
    _create(client, title="みかんを買う", description="特売")
    res = client.get("/api/tasks?q=りんご")
    assert len(res.json()) == 1
    # 説明にマッチ
    res2 = client.get("/api/tasks?q=特売")
    assert len(res2.json()) == 1


def test_sort_by_title_asc(client):
    _create(client, title="C")
    _create(client, title="A")
    _create(client, title="B")
    res = client.get("/api/tasks?sort=title&order=asc")
    titles = [t["title"] for t in res.json()]
    assert titles == ["A", "B", "C"]


def test_invalid_sort_key(client):
    res = client.get("/api/tasks?sort=evil")
    assert res.status_code == 400


def test_invalid_order(client):
    res = client.get("/api/tasks?order=sideways")
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# 静的フロントエンド
# ---------------------------------------------------------------------------

def test_index_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "タスク管理アプリ" in res.text
