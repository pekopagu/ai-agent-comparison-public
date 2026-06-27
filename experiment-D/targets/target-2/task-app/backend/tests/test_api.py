"""タスク管理 API の pytest テスト。"""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# backend ディレクトリをインポートパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import Base, get_db  # noqa: E402
import main  # noqa: E402

# テスト専用のインメモリ SQLite を使用（本番DBに影響を与えない）
TEST_DATABASE_URL = "sqlite:///./test_tasks.db"
test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[get_db] = override_get_db
client = TestClient(main.app)


@pytest.fixture(autouse=True)
def setup_database():
    """各テストの前後でテーブルを作り直し、独立性を保つ。"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ---------- 作成（Create） ----------

def test_create_task_minimal():
    """必須項目のみでタスクを作成できる（デフォルト値が適用される）。"""
    res = client.post("/tasks", json={"title": "買い物に行く"})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "買い物に行く"
    assert data["status"] == "todo"
    assert data["priority"] == "medium"
    assert data["description"] is None
    assert data["due_date"] is None
    assert "id" in data
    assert "created_at" in data


def test_create_task_full():
    """全項目を指定してタスクを作成できる。"""
    payload = {
        "title": "レポート作成",
        "description": "月次レポートを書く",
        "status": "doing",
        "priority": "high",
        "due_date": "2026-12-31",
    }
    res = client.post("/tasks", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["description"] == "月次レポートを書く"
    assert data["status"] == "doing"
    assert data["priority"] == "high"
    assert data["due_date"] == "2026-12-31"


def test_create_task_blank_title():
    """空白のみのタイトルはバリデーションエラー（422）。"""
    res = client.post("/tasks", json={"title": "   "})
    assert res.status_code == 422


def test_create_task_missing_title():
    """タイトル未指定はバリデーションエラー（422）。"""
    res = client.post("/tasks", json={"description": "タイトルなし"})
    assert res.status_code == 422


def test_create_task_invalid_status():
    """許容外のステータスはバリデーションエラー（422）。"""
    res = client.post("/tasks", json={"title": "テスト", "status": "unknown"})
    assert res.status_code == 422


def test_create_task_invalid_priority():
    """許容外の優先度はバリデーションエラー（422）。"""
    res = client.post("/tasks", json={"title": "テスト", "priority": "urgent"})
    assert res.status_code == 422


# ---------- 取得（Read） ----------

def test_get_task():
    """作成したタスクを ID で取得できる。"""
    created = client.post("/tasks", json={"title": "詳細取得テスト"}).json()
    res = client.get(f"/tasks/{created['id']}")
    assert res.status_code == 200
    assert res.json()["title"] == "詳細取得テスト"


def test_get_task_not_found():
    """存在しない ID は 404。"""
    res = client.get("/tasks/9999")
    assert res.status_code == 404


def test_list_tasks_empty():
    """タスクが無い場合は空配列を返す。"""
    res = client.get("/tasks")
    assert res.status_code == 200
    assert res.json() == []


def test_list_tasks_multiple():
    """複数タスクの一覧を取得できる。"""
    client.post("/tasks", json={"title": "タスク1"})
    client.post("/tasks", json={"title": "タスク2"})
    res = client.get("/tasks")
    assert res.status_code == 200
    assert len(res.json()) == 2


# ---------- フィルタ ----------

def test_filter_by_status():
    """status でフィルタできる。"""
    client.post("/tasks", json={"title": "A", "status": "todo"})
    client.post("/tasks", json={"title": "B", "status": "done"})
    res = client.get("/tasks", params={"status": "done"})
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "B"


def test_filter_by_priority():
    """priority でフィルタできる。"""
    client.post("/tasks", json={"title": "A", "priority": "low"})
    client.post("/tasks", json={"title": "B", "priority": "high"})
    res = client.get("/tasks", params={"priority": "high"})
    data = res.json()
    assert len(data) == 1
    assert data[0]["title"] == "B"


# ---------- ソート ----------

def test_sort_by_priority_asc():
    """優先度の昇順（low < medium < high）でソートできる。"""
    client.post("/tasks", json={"title": "H", "priority": "high"})
    client.post("/tasks", json={"title": "L", "priority": "low"})
    client.post("/tasks", json={"title": "M", "priority": "medium"})
    res = client.get("/tasks", params={"sort": "priority", "order": "asc"})
    titles = [t["title"] for t in res.json()]
    assert titles == ["L", "M", "H"]


def test_sort_by_priority_desc():
    """優先度の降順（high > medium > low）でソートできる。"""
    client.post("/tasks", json={"title": "H", "priority": "high"})
    client.post("/tasks", json={"title": "L", "priority": "low"})
    client.post("/tasks", json={"title": "M", "priority": "medium"})
    res = client.get("/tasks", params={"sort": "priority", "order": "desc"})
    titles = [t["title"] for t in res.json()]
    assert titles == ["H", "M", "L"]


def test_sort_by_due_date():
    """due_date の昇順でソートできる。"""
    client.post("/tasks", json={"title": "後", "due_date": "2026-12-31"})
    client.post("/tasks", json={"title": "先", "due_date": "2026-01-01"})
    res = client.get("/tasks", params={"sort": "due_date", "order": "asc"})
    titles = [t["title"] for t in res.json()]
    assert titles == ["先", "後"]


def test_invalid_sort_param():
    """許容外の sort パラメータは 422。"""
    res = client.get("/tasks", params={"sort": "title"})
    assert res.status_code == 422


def test_invalid_order_param():
    """許容外の order パラメータは 422。"""
    res = client.get("/tasks", params={"order": "ascending"})
    assert res.status_code == 422


# ---------- 更新（Update） ----------

def test_update_task():
    """タスクを更新できる。"""
    created = client.post("/tasks", json={"title": "更新前"}).json()
    res = client.put(
        f"/tasks/{created['id']}",
        json={"title": "更新後", "status": "done"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "更新後"
    assert data["status"] == "done"


def test_update_task_partial():
    """部分更新（優先度のみ）ができ、他項目は維持される。"""
    created = client.post(
        "/tasks", json={"title": "元タイトル", "priority": "low"}
    ).json()
    res = client.put(f"/tasks/{created['id']}", json={"priority": "high"})
    data = res.json()
    assert data["title"] == "元タイトル"
    assert data["priority"] == "high"


def test_update_task_not_found():
    """存在しない ID の更新は 404。"""
    res = client.put("/tasks/9999", json={"title": "x"})
    assert res.status_code == 404


def test_update_task_invalid_status():
    """更新時の許容外ステータスは 422。"""
    created = client.post("/tasks", json={"title": "x"}).json()
    res = client.put(f"/tasks/{created['id']}", json={"status": "invalid"})
    assert res.status_code == 422


# ---------- 削除（Delete） ----------

def test_delete_task():
    """タスクを削除でき、その後取得すると 404。"""
    created = client.post("/tasks", json={"title": "削除対象"}).json()
    res = client.delete(f"/tasks/{created['id']}")
    assert res.status_code == 204
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_delete_task_not_found():
    """存在しない ID の削除は 404。"""
    res = client.delete("/tasks/9999")
    assert res.status_code == 404
