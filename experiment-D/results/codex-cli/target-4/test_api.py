"""
target-4 API に合わせた pytest 18本。
"""

import pytest
import requests
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"
TASKS_URL = f"{BASE_URL}/tasks"
DELETE_SUCCESS_STATUS = 204
PRIORITY_SORT_ORDER = "desc"


@pytest.fixture(autouse=True)
def cleanup():
    yield
    response = requests.get(TASKS_URL)
    if response.status_code == 200:
        for task in response.json():
            requests.delete(f"{TASKS_URL}/{task['id']}")


@pytest.fixture
def sample_task():
    payload = {
        "title": "テストタスク",
        "description": "テスト用の説明",
        "status": "todo",
        "priority": "medium",
        "due_date": str(date.today() + timedelta(days=7)),
    }
    response = requests.post(TASKS_URL, json=payload)
    assert response.status_code == 201
    return response.json()


class TestNormalCases:
    def test_01_create_task(self):
        payload = {
            "title": "新しいタスク",
            "description": "説明文",
            "status": "todo",
            "priority": "high",
            "due_date": str(date.today() + timedelta(days=3)),
        }
        response = requests.post(TASKS_URL, json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["status"] == "todo"
        assert data["priority"] == "high"
        assert "id" in data
        assert "created_at" in data

    def test_02_get_task_list(self):
        for i in range(2):
            requests.post(TASKS_URL, json={"title": f"タスク{i+1}", "status": "todo", "priority": "medium"})
        response = requests.get(TASKS_URL)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_03_get_task_detail(self, sample_task):
        task_id = sample_task["id"]
        response = requests.get(f"{TASKS_URL}/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == sample_task["title"]

    def test_04_update_task(self, sample_task):
        task_id = sample_task["id"]
        response = requests.put(f"{TASKS_URL}/{task_id}", json={"title": "更新後タイトル", "status": "doing"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "更新後タイトル"
        assert data["status"] == "doing"

    def test_05_delete_task(self, sample_task):
        task_id = sample_task["id"]
        response = requests.delete(f"{TASKS_URL}/{task_id}")
        assert response.status_code == DELETE_SUCCESS_STATUS
        response = requests.get(f"{TASKS_URL}/{task_id}")
        assert response.status_code == 404

    def test_06_filter_by_status(self):
        requests.post(TASKS_URL, json={"title": "todo1", "status": "todo", "priority": "medium"})
        requests.post(TASKS_URL, json={"title": "doing1", "status": "doing", "priority": "medium"})
        requests.post(TASKS_URL, json={"title": "done1", "status": "done", "priority": "medium"})
        response = requests.get(TASKS_URL, params={"status": "todo"})
        assert response.status_code == 200
        data = response.json()
        assert all(task["status"] == "todo" for task in data)

    def test_07_filter_by_priority(self):
        requests.post(TASKS_URL, json={"title": "high1", "status": "todo", "priority": "high"})
        requests.post(TASKS_URL, json={"title": "low1", "status": "todo", "priority": "low"})
        response = requests.get(TASKS_URL, params={"priority": "high"})
        assert response.status_code == 200
        data = response.json()
        assert all(task["priority"] == "high" for task in data)

    def test_08_sort_by_created_at(self):
        for i in range(3):
            requests.post(TASKS_URL, json={"title": f"task{i}", "status": "todo", "priority": "medium"})
        response = requests.get(TASKS_URL, params={"sort": "created_at", "order": "asc"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        created_ats = [task["created_at"] for task in data]
        assert created_ats == sorted(created_ats)

    def test_09_sort_by_due_date(self):
        today = date.today()
        requests.post(TASKS_URL, json={"title": "task_late", "status": "todo", "priority": "medium", "due_date": str(today + timedelta(days=10))})
        requests.post(TASKS_URL, json={"title": "task_soon", "status": "todo", "priority": "medium", "due_date": str(today + timedelta(days=1))})
        response = requests.get(TASKS_URL, params={"sort": "due_date", "order": "asc"})
        assert response.status_code == 200
        data = response.json()
        due_dates = [task["due_date"] for task in data if task.get("due_date")]
        assert due_dates == sorted(due_dates)

    def test_10_sort_by_priority(self):
        requests.post(TASKS_URL, json={"title": "low_task", "status": "todo", "priority": "low"})
        requests.post(TASKS_URL, json={"title": "high_task", "status": "todo", "priority": "high"})
        requests.post(TASKS_URL, json={"title": "medium_task", "status": "todo", "priority": "medium"})
        response = requests.get(TASKS_URL, params={"sort": "priority", "order": PRIORITY_SORT_ORDER})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        priority_order = {"high": 0, "medium": 1, "low": 2}
        priorities = [priority_order[task["priority"]] for task in data]
        assert priorities == sorted(priorities)


class TestErrorCases:
    def test_11_get_nonexistent_task(self):
        response = requests.get(f"{TASKS_URL}/99999")
        assert response.status_code == 404

    def test_12_update_nonexistent_task(self):
        response = requests.put(f"{TASKS_URL}/99999", json={"title": "updated"})
        assert response.status_code == 404

    def test_13_delete_nonexistent_task(self):
        response = requests.delete(f"{TASKS_URL}/99999")
        assert response.status_code == 404

    def test_14_create_without_title(self):
        response = requests.post(TASKS_URL, json={"description": "説明のみ", "status": "todo", "priority": "medium"})
        assert response.status_code == 422

    def test_15_create_with_title_too_long(self):
        response = requests.post(TASKS_URL, json={"title": "a" * 256, "status": "todo", "priority": "medium"})
        assert response.status_code == 422

    def test_16_create_with_invalid_status(self):
        response = requests.post(TASKS_URL, json={"title": "テスト", "status": "invalid_status", "priority": "medium"})
        assert response.status_code == 422

    def test_17_create_with_invalid_priority(self):
        response = requests.post(TASKS_URL, json={"title": "テスト", "status": "todo", "priority": "urgent"})
        assert response.status_code == 422

    def test_18_create_with_invalid_due_date(self):
        response = requests.post(TASKS_URL, json={"title": "テスト", "status": "todo", "priority": "medium", "due_date": "not-a-date"})
        assert response.status_code == 422
