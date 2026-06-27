# -*- coding: utf-8 -*-
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os
# 親ディレクトリをパスに追加してモジュールをインポートできるようにする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db
from main import app
from models import Task

# インメモリSQLiteエンジンをプール方式で使用して同一接続を維持する
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db_session")
def fixture_db_session():
    # テーブル作成
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # テーブル削除
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="client")
def fixture_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

def test_create_task(client):
    response = client.post(
        "/tasks",
        json={"title": "テストタスク", "description": "テスト説明", "priority": "high", "due_date": "2026-06-30"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "テストタスク"
    assert data["status"] == "todo"
    assert data["priority"] == "high"
    assert data["due_date"] == "2026-06-30"
    assert "id" in data

def test_create_task_validation_error(client):
    # タイトルが空
    response = client.post(
        "/tasks",
        json={"title": "", "description": "テスト説明"}
    )
    assert response.status_code == 422

    # 不正なステータス
    response = client.post(
        "/tasks",
        json={"title": "テストタスク", "status": "invalid"}
    )
    assert response.status_code == 422

def test_get_tasks_filtering_and_sorting(client):
    # テストデータを挿入
    client.post("/tasks", json={"title": "Task 1", "status": "todo", "priority": "high", "due_date": "2026-06-25"})
    client.post("/tasks", json={"title": "Task 2", "status": "doing", "priority": "medium", "due_date": "2026-06-20"})
    client.post("/tasks", json={"title": "Task 3", "status": "done", "priority": "low", "due_date": "2026-06-30"})

    # ステータスでフィルタ
    response = client.get("/tasks?status=doing")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task 2"

    # 優先度でフィルタ
    response = client.get("/tasks?priority=high")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task 1"

    # 優先度でソート (asc)
    # low (1), medium (2), high (3) なので、昇順なら Task 3 (low) -> Task 2 (medium) -> Task 1 (high)
    response = client.get("/tasks?sort=priority&order=asc")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["title"] == "Task 3"
    assert data[1]["title"] == "Task 2"
    assert data[2]["title"] == "Task 1"

    # 期限日でソート (desc)
    # 2026-06-30 (Task 3) -> 2026-06-25 (Task 1) -> 2026-06-20 (Task 2)
    response = client.get("/tasks?sort=due_date&order=desc")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["title"] == "Task 3"
    assert data[1]["title"] == "Task 1"
    assert data[2]["title"] == "Task 2"

def test_get_task_by_id(client):
    response = client.post("/tasks", json={"title": "詳細テスト"})
    task_id = response.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "詳細テスト"

    response = client.get("/tasks/9999")
    assert response.status_code == 404

def test_update_task(client):
    response = client.post("/tasks", json={"title": "初期タイトル", "status": "todo"})
    task_id = response.json()["id"]

    response = client.put(f"/tasks/{task_id}", json={"title": "更新タイトル", "status": "doing"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "更新タイトル"
    assert data["status"] == "doing"

    response = client.put("/tasks/9999", json={"title": "更新タイトル"})
    assert response.status_code == 404

def test_delete_task(client):
    response = client.post("/tasks", json={"title": "削除用タスク"})
    task_id = response.json()["id"]

    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404

    response = client.delete("/tasks/9999")
    assert response.status_code == 404
