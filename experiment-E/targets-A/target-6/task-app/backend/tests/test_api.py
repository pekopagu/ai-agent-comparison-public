import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy.pool import StaticPool
from database import Base, get_db
import models
from main import app

# Test database settings (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    models.Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        models.Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_create_task(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Test Task",
            "description": "Test Description",
            "status": "todo",
            "priority": "high",
            "due_date": "2026-06-30"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"
    assert data["status"] == "todo"
    assert data["priority"] == "high"
    assert data["due_date"] == "2026-06-30"
    assert "id" in data
    assert "created_at" in data

def test_create_task_validation_error(client):
    # Title is empty
    response = client.post(
        "/tasks",
        json={
            "title": "",
            "status": "todo",
            "priority": "medium"
        }
    )
    assert response.status_code == 422

    # Invalid status
    response = client.post(
        "/tasks",
        json={
            "title": "Test Task",
            "status": "invalid_status",
            "priority": "medium"
        }
    )
    assert response.status_code == 422

    # Invalid priority
    response = client.post(
        "/tasks",
        json={
            "title": "Test Task",
            "status": "todo",
            "priority": "invalid_priority"
        }
    )
    assert response.status_code == 422

def test_get_tasks_filtering_and_sorting(client):
    # Populate test tasks
    client.post("/tasks", json={"title": "Task A", "status": "todo", "priority": "high", "due_date": "2026-07-01"})
    client.post("/tasks", json={"title": "Task B", "status": "doing", "priority": "medium", "due_date": "2026-06-25"})
    client.post("/tasks", json={"title": "Task C", "status": "done", "priority": "low", "due_date": "2026-08-01"})

    # 1. Status Filter
    response = client.get("/tasks?status=doing")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task B"

    # 2. Priority Filter
    response = client.get("/tasks?priority=high")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task A"

    # 3. Sorting (due_date asc)
    response = client.get("/tasks?sort=due_date&order=asc")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["title"] == "Task B"  # 06-25
    assert data[1]["title"] == "Task A"  # 07-01
    assert data[2]["title"] == "Task C"  # 08-01

    # 4. Sorting (priority asc: high -> medium -> low)
    response = client.get("/tasks?sort=priority&order=asc")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["title"] == "Task A"  # high
    assert data[1]["title"] == "Task B"  # medium
    assert data[2]["title"] == "Task C"  # low

    # 5. Sorting (priority desc: low -> medium -> high)
    response = client.get("/tasks?sort=priority&order=desc")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["title"] == "Task C"  # low
    assert data[1]["title"] == "Task B"  # medium
    assert data[2]["title"] == "Task A"  # high

def test_get_task_by_id(client):
    res_create = client.post("/tasks", json={"title": "Find Me"})
    task_id = res_create.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Find Me"

    response_not_found = client.get("/tasks/9999")
    assert response_not_found.status_code == 404

def test_update_task(client):
    res_create = client.post("/tasks", json={"title": "Old Title", "status": "todo"})
    task_id = res_create.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={
            "title": "New Title",
            "status": "doing",
            "priority": "high"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["status"] == "doing"
    assert data["priority"] == "high"

def test_delete_task(client):
    res_create = client.post("/tasks", json={"title": "To Delete"})
    task_id = res_create.json()["id"]

    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200

    response_get = client.get(f"/tasks/{task_id}")
    assert response_get.status_code == 404
