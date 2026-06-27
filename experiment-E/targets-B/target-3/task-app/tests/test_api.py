from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    original_path = app.state.database_path
    test_db = tmp_path / "test_tasks.db"
    app.state.database_path = test_db
    init_db(test_db)
    with TestClient(app) as test_client:
        yield test_client
    app.state.database_path = original_path


def create_task(client: TestClient, title: str = "テストタスク", priority: str = "medium") -> dict:
    response = client.post(
        "/api/tasks",
        json={
            "title": title,
            "description": "説明",
            "priority": priority,
            "due_date": "2026-06-30",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_and_get_task(client: TestClient) -> None:
    created = create_task(client)

    response = client.get(f"/api/tasks/{created['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "テストタスク"
    assert data["completed"] is False
    assert data["priority"] == "medium"


def test_list_tasks_with_summary(client: TestClient) -> None:
    create_task(client, "高優先", "high")
    create_task(client, "低優先", "low")

    response = client.get("/api/tasks")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["active"] == 2
    assert data["completed"] == 0
    assert len(data["items"]) == 2


def test_update_task(client: TestClient) -> None:
    created = create_task(client)

    response = client.put(
        f"/api/tasks/{created['id']}",
        json={
            "title": "更新済み",
            "description": "更新後の説明",
            "priority": "high",
            "due_date": None,
            "completed": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "更新済み"
    assert data["priority"] == "high"
    assert data["due_date"] is None
    assert data["completed"] is True


def test_toggle_task(client: TestClient) -> None:
    created = create_task(client)

    response = client.patch(f"/api/tasks/{created['id']}/toggle")

    assert response.status_code == 200
    assert response.json()["completed"] is True


def test_delete_task(client: TestClient) -> None:
    created = create_task(client)

    delete_response = client.delete(f"/api/tasks/{created['id']}")
    get_response = client.get(f"/api/tasks/{created['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_missing_task_returns_404(client: TestClient) -> None:
    response = client.get("/api/tasks/9999")

    assert response.status_code == 404


def test_invalid_priority_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/tasks",
        json={
            "title": "不正",
            "priority": "urgent",
        },
    )

    assert response.status_code == 422


def test_filters_and_search(client: TestClient) -> None:
    high = create_task(client, "請求書を送る", "high")
    create_task(client, "読書", "low")
    client.patch(f"/api/tasks/{high['id']}/toggle")

    completed_response = client.get("/api/tasks?status=completed")
    priority_response = client.get("/api/tasks?priority=low")
    search_response = client.get("/api/tasks?q=請求")

    assert completed_response.status_code == 200
    assert completed_response.json()["items"][0]["title"] == "請求書を送る"
    assert priority_response.json()["items"][0]["priority"] == "low"
    assert search_response.json()["items"][0]["title"] == "請求書を送る"
