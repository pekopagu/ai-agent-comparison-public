from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["TASK_APP_DB"] = str(Path(__file__).parent / "test_tasks.db")

from database import get_db_path, init_db  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    db_path = get_db_path()
    if db_path.exists():
        db_path.unlink()
    init_db()
    yield
    if db_path.exists():
        db_path.unlink()


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def create_task(client: TestClient, **overrides):
    payload = {
        "title": "Write tests",
        "description": "Cover API behavior",
        "status": "todo",
        "priority": "medium",
        "due_date": "2026-07-01",
    }
    payload.update(overrides)
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_and_get_task(client: TestClient):
    task = create_task(client, title="Plan release", priority="high")

    response = client.get(f"/tasks/{task['id']}")

    assert response.status_code == 200
    assert response.json()["title"] == "Plan release"
    assert response.json()["priority"] == "high"


def test_update_task(client: TestClient):
    task = create_task(client)

    response = client.put(
        f"/tasks/{task['id']}",
        json={"title": "Ship release", "status": "doing", "due_date": None},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Ship release"
    assert body["status"] == "doing"
    assert body["due_date"] is None


def test_delete_task(client: TestClient):
    task = create_task(client)

    response = client.delete(f"/tasks/{task['id']}")

    assert response.status_code == 204
    assert client.get(f"/tasks/{task['id']}").status_code == 404


def test_filter_and_sort_tasks(client: TestClient):
    create_task(client, title="Low item", status="todo", priority="low", due_date="2026-08-01")
    create_task(client, title="High item", status="todo", priority="high", due_date="2026-06-01")
    create_task(client, title="Done item", status="done", priority="medium", due_date="2026-07-01")

    response = client.get("/tasks?status=todo&sort=priority&order=desc")

    assert response.status_code == 200
    tasks = response.json()
    assert [task["title"] for task in tasks] == ["High item", "Low item"]


def test_validation_errors(client: TestClient):
    response = client.post("/tasks", json={"title": " ", "status": "blocked"})

    assert response.status_code == 422


def test_missing_task_returns_404(client: TestClient):
    assert client.get("/tasks/999").status_code == 404
    assert client.delete("/tasks/999").status_code == 404
