"""タスク管理APIのテスト（pytest）"""
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# backendディレクトリをパスに追加（テストを単体で実行できるように）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main  # noqa: E402
import models  # noqa: E402
from database import Base, get_db  # noqa: E402

# テスト専用のインメモリSQLite
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """テスト用DBセッションを払い出す"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[get_db] = override_get_db
client = TestClient(main.app)


@pytest.fixture(autouse=True)
def reset_database():
    """各テストの前後でテーブルを作り直し、状態を分離する"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ---------- 作成（POST /tasks） ----------

def test_create_task_minimal():
    """必須項目のみでタスクを作成できる（デフォルト値が入る）"""
    res = client.post("/tasks", json={"title": "買い物"})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "買い物"
    assert data["status"] == "todo"
    assert data["priority"] == "medium"
    assert data["description"] is None
    assert data["due_date"] is None
    assert "id" in data
    assert "created_at" in data


def test_create_task_full():
    """全項目を指定してタスクを作成できる"""
    payload = {
        "title": "レポート提出",
        "description": "第3章まで",
        "status": "doing",
        "priority": "high",
        "due_date": "2026-12-31",
    }
    res = client.post("/tasks", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "レポート提出"
    assert data["description"] == "第3章まで"
    assert data["status"] == "doing"
    assert data["priority"] == "high"
    assert data["due_date"] == "2026-12-31"


def test_create_task_title_required():
    """titleが無い場合は422エラー"""
    res = client.post("/tasks", json={"description": "説明のみ"})
    assert res.status_code == 422


def test_create_task_title_empty():
    """titleが空文字の場合は422エラー"""
    res = client.post("/tasks", json={"title": ""})
    assert res.status_code == 422


def test_create_task_invalid_status():
    """statusが許容値以外の場合は422エラー"""
    res = client.post("/tasks", json={"title": "x", "status": "unknown"})
    assert res.status_code == 422


def test_create_task_invalid_priority():
    """priorityが許容値以外の場合は422エラー"""
    res = client.post("/tasks", json={"title": "x", "priority": "urgent"})
    assert res.status_code == 422


# ---------- 一覧取得（GET /tasks） ----------

def test_list_tasks_empty():
    """初期状態は空配列"""
    res = client.get("/tasks")
    assert res.status_code == 200
    assert res.json() == []


def test_list_tasks_multiple():
    """複数件取得できる"""
    client.post("/tasks", json={"title": "A"})
    client.post("/tasks", json={"title": "B"})
    res = client.get("/tasks")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_filter_by_status():
    """statusでフィルタできる"""
    client.post("/tasks", json={"title": "A", "status": "todo"})
    client.post("/tasks", json={"title": "B", "status": "done"})
    client.post("/tasks", json={"title": "C", "status": "done"})
    res = client.get("/tasks", params={"status": "done"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert all(t["status"] == "done" for t in data)


def test_filter_by_priority():
    """priorityでフィルタできる"""
    client.post("/tasks", json={"title": "A", "priority": "high"})
    client.post("/tasks", json={"title": "B", "priority": "low"})
    res = client.get("/tasks", params={"priority": "high"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["priority"] == "high"


def test_sort_by_priority_desc():
    """priorityの降順（high→medium→low）でソートできる"""
    client.post("/tasks", json={"title": "low", "priority": "low"})
    client.post("/tasks", json={"title": "high", "priority": "high"})
    client.post("/tasks", json={"title": "medium", "priority": "medium"})
    res = client.get("/tasks", params={"sort": "priority", "order": "desc"})
    assert res.status_code == 200
    priorities = [t["priority"] for t in res.json()]
    assert priorities == ["high", "medium", "low"]


def test_sort_by_due_date_asc():
    """due_dateの昇順でソートできる"""
    client.post("/tasks", json={"title": "late", "due_date": "2026-12-31"})
    client.post("/tasks", json={"title": "early", "due_date": "2026-01-01"})
    res = client.get("/tasks", params={"sort": "due_date", "order": "asc"})
    assert res.status_code == 200
    titles = [t["title"] for t in res.json()]
    assert titles == ["early", "late"]


def test_invalid_sort_param():
    """不正なsortパラメータは422エラー"""
    res = client.get("/tasks", params={"sort": "unknown"})
    assert res.status_code == 422


def test_invalid_order_param():
    """不正なorderパラメータは422エラー"""
    res = client.get("/tasks", params={"order": "wrong"})
    assert res.status_code == 422


# ---------- 詳細取得（GET /tasks/{id}） ----------

def test_get_task_by_id():
    """IDでタスクを取得できる"""
    created = client.post("/tasks", json={"title": "詳細テスト"}).json()
    res = client.get(f"/tasks/{created['id']}")
    assert res.status_code == 200
    assert res.json()["title"] == "詳細テスト"


def test_get_task_not_found():
    """存在しないIDは404エラー"""
    res = client.get("/tasks/9999")
    assert res.status_code == 404


# ---------- 更新（PUT /tasks/{id}） ----------

def test_update_task():
    """タスクを更新できる"""
    created = client.post("/tasks", json={"title": "元のタイトル"}).json()
    res = client.put(
        f"/tasks/{created['id']}",
        json={"title": "新しいタイトル", "status": "done"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "新しいタイトル"
    assert data["status"] == "done"


def test_update_task_partial():
    """部分更新（一部フィールドのみ）ができる"""
    created = client.post(
        "/tasks", json={"title": "保持", "priority": "high"}
    ).json()
    res = client.put(f"/tasks/{created['id']}", json={"status": "doing"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "doing"
    assert data["title"] == "保持"
    assert data["priority"] == "high"


def test_update_task_not_found():
    """存在しないIDの更新は404エラー"""
    res = client.put("/tasks/9999", json={"title": "x"})
    assert res.status_code == 404


def test_update_task_invalid_status():
    """更新時の不正なstatusは422エラー"""
    created = client.post("/tasks", json={"title": "x"}).json()
    res = client.put(f"/tasks/{created['id']}", json={"status": "invalid"})
    assert res.status_code == 422


# ---------- 削除（DELETE /tasks/{id}） ----------

def test_delete_task():
    """タスクを削除できる"""
    created = client.post("/tasks", json={"title": "削除対象"}).json()
    res = client.delete(f"/tasks/{created['id']}")
    assert res.status_code == 204
    # 削除後は取得できない
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_delete_task_not_found():
    """存在しないIDの削除は404エラー"""
    res = client.delete("/tasks/9999")
    assert res.status_code == 404
