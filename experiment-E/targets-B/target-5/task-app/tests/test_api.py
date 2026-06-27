from __future__ import annotations

import importlib

from fastapi.testclient import TestClient


def make_client(tmp_path, monkeypatch):
    monkeypatch.setenv("TASK_DB_PATH", str(tmp_path / "test.db"))
    database = importlib.import_module("app.database")
    database.init_db()
    main = importlib.import_module("app.main")
    return TestClient(main.app)


def test_health(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_list_task(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    payload = {
        "title": "見積書を作成",
        "description": "午前中にドラフトを作る",
        "priority": "high",
        "due_date": "2026-06-21",
    }

    created = client.post("/api/tasks", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["id"] == 1
    assert body["title"] == payload["title"]
    assert body["completed"] is False

    listed = client.get("/api/tasks")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_get_update_toggle_and_delete_task(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    created = client.post(
        "/api/tasks",
        json={"title": "レビュー", "description": "", "priority": "medium", "due_date": None},
    ).json()

    fetched = client.get(f"/api/tasks/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "レビュー"

    updated = client.put(
        f"/api/tasks/{created['id']}",
        json={
            "title": "レビュー完了確認",
            "description": "差分を再確認",
            "priority": "low",
            "due_date": "2026-06-22",
            "completed": False,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["priority"] == "low"

    toggled = client.patch(f"/api/tasks/{created['id']}/toggle")
    assert toggled.status_code == 200
    assert toggled.json()["completed"] is True

    deleted = client.delete(f"/api/tasks/{created['id']}")
    assert deleted.status_code == 204

    missing = client.get(f"/api/tasks/{created['id']}")
    assert missing.status_code == 404


def test_filters_and_validation(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    client.post("/api/tasks", json={"title": "高優先", "description": "", "priority": "high", "due_date": None})
    low = client.post("/api/tasks", json={"title": "低優先", "description": "検索対象", "priority": "low", "due_date": None}).json()
    client.patch(f"/api/tasks/{low['id']}/toggle")

    completed = client.get("/api/tasks?status=completed")
    assert completed.status_code == 200
    assert [task["title"] for task in completed.json()] == ["低優先"]

    priority = client.get("/api/tasks?priority=high")
    assert priority.status_code == 200
    assert [task["title"] for task in priority.json()] == ["高優先"]

    searched = client.get("/api/tasks?q=検索")
    assert searched.status_code == 200
    assert [task["title"] for task in searched.json()] == ["低優先"]

    invalid = client.post("/api/tasks", json={"title": "", "priority": "urgent"})
    assert invalid.status_code == 422
