import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
import models

# テスト用のSQLiteインメモリデータベース
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    # テストごとにテーブルを新規作成
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    # get_db 依存関係をテスト用セッションで上書き
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# ----------------- テストケース -----------------

def test_create_task(client):
    response = client.post(
        "/api/tasks",
        json={
            "title": "テストタスク",
            "description": "テストの説明",
            "due_date": "2026-06-30",
            "priority": "high"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "テストタスク"
    assert data["description"] == "テストの説明"
    assert data["due_date"] == "2026-06-30"
    assert data["priority"] == "high"
    assert data["status"] == "todo"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_create_task_validation_error(client):
    # タイトルが空
    response = client.post(
        "/api/tasks",
        json={
            "title": "",
            "priority": "high"
        }
    )
    assert response.status_code == 422

    # 不正な優先度
    response = client.post(
        "/api/tasks",
        json={
            "title": "タスク",
            "priority": "invalid_priority"
        }
    )
    assert response.status_code == 422

    # 不正な日付形式
    response = client.post(
        "/api/tasks",
        json={
            "title": "タスク",
            "due_date": "2026/06/30"
        }
    )
    assert response.status_code == 422

def test_read_tasks(client, db):
    # テストデータを直接インサート
    task1 = models.Task(title="タスク1", priority="low", status="todo")
    task2 = models.Task(title="タスク2", priority="medium", status="in_progress")
    db.add(task1)
    db.add(task2)
    db.commit()

    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # フィルタテスト
    response = client.get("/api/tasks?status=in_progress")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "タスク2"

    # 検索テスト
    response = client.get("/api/tasks?q=タスク1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "タスク1"

def test_read_task_by_id(client, db):
    task = models.Task(title="詳細タスク", priority="medium", status="todo")
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.get(f"/api/tasks/{task.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "詳細タスク"

    # 存在しないタスク
    response = client.get("/api/tasks/999")
    assert response.status_code == 404

def test_update_task(client, db):
    task = models.Task(title="更新前タスク", priority="low", status="todo")
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.put(
        f"/api/tasks/{task.id}",
        json={
            "title": "更新後タスク",
            "status": "in_progress",
            "priority": "high"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "更新後タスク"
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"

def test_delete_task(client, db):
    task = models.Task(title="削除対象タスク", priority="low", status="todo")
    db.add(task)
    db.commit()
    db.refresh(task)

    response = client.delete(f"/api/tasks/{task.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # 再度取得して404になること
    response = client.get(f"/api/tasks/{task.id}")
    assert response.status_code == 404
