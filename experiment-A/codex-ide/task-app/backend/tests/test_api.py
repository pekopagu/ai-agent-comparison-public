from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_task(client: TestClient, **overrides: object) -> dict[str, object]:
    payload = {
        "title": "テストタスク",
        "description": "説明",
        "status": "todo",
        "priority": "medium",
        "due_date": "2026-06-30",
    }
    payload.update(overrides)
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_and_get_task(client: TestClient) -> None:
    created = create_task(client, title="買い物", priority="high")

    assert created["id"] == 1
    assert created["title"] == "買い物"
    assert created["priority"] == "high"
    assert created["status"] == "todo"

    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "買い物"


def test_validation_errors(client: TestClient) -> None:
    blank_title = client.post("/tasks", json={"title": "   "})
    assert blank_title.status_code == 422

    invalid_status = client.post("/tasks", json={"title": "x", "status": "blocked"})
    assert invalid_status.status_code == 422


def test_update_task(client: TestClient) -> None:
    created = create_task(client)

    response = client.put(
        f"/tasks/{created['id']}",
        json={
            "title": "更新済み",
            "description": "",
            "status": "doing",
            "priority": "low",
            "due_date": None,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "更新済み"
    assert data["description"] is None
    assert data["status"] == "doing"
    assert data["priority"] == "low"
    assert data["due_date"] is None


def test_delete_task(client: TestClient) -> None:
    created = create_task(client)

    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204

    missing = client.get(f"/tasks/{created['id']}")
    assert missing.status_code == 404


def test_filter_and_sort_tasks(client: TestClient) -> None:
    create_task(client, title="低", status="todo", priority="low", due_date="2026-07-10")
    create_task(client, title="高", status="doing", priority="high", due_date="2026-06-21")
    create_task(client, title="中", status="doing", priority="medium", due_date="2026-07-01")

    filtered = client.get("/tasks", params={"status": "doing"})
    assert filtered.status_code == 200
    assert [task["title"] for task in filtered.json()] == ["中", "高"]

    by_due_date = client.get("/tasks", params={"sort": "due_date", "order": "asc"})
    assert [task["title"] for task in by_due_date.json()] == ["高", "中", "低"]

    by_priority = client.get("/tasks", params={"sort": "priority", "order": "desc"})
    assert [task["title"] for task in by_priority.json()] == ["高", "中", "低"]


def test_missing_task_returns_404(client: TestClient) -> None:
    response = client.get("/tasks/999")
    assert response.status_code == 404
