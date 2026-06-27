"""タスク管理API のテスト。"""
from __future__ import annotations


def _sample_payload(**overrides) -> dict:
    payload = {
        "title": "牛乳を買う",
        "description": "スーパーで2本",
        "priority": "high",
        "due_date": "2026-12-31",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# ヘルスチェック
# ---------------------------------------------------------------------------
def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# 作成
# ---------------------------------------------------------------------------
def test_create_task(client):
    res = client.post("/api/tasks", json=_sample_payload())
    assert res.status_code == 201
    data = res.json()
    assert data["id"] > 0
    assert data["title"] == "牛乳を買う"
    assert data["description"] == "スーパーで2本"
    assert data["priority"] == "high"
    assert data["due_date"] == "2026-12-31"
    assert data["completed"] is False
    assert data["created_at"]
    assert data["updated_at"]


def test_create_task_minimal(client):
    res = client.post("/api/tasks", json={"title": "最小タスク"})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "最小タスク"
    assert data["priority"] == "medium"
    assert data["description"] is None
    assert data["due_date"] is None


def test_create_task_empty_title(client):
    res = client.post("/api/tasks", json={"title": "   "})
    assert res.status_code == 422


def test_create_task_invalid_priority(client):
    res = client.post("/api/tasks", json={"title": "x", "priority": "urgent"})
    assert res.status_code == 422


def test_create_task_invalid_due_date(client):
    res = client.post("/api/tasks", json={"title": "x", "due_date": "2026/01/01"})
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# 一覧（フィルタ・検索）
# ---------------------------------------------------------------------------
def test_list_empty(client):
    res = client.get("/api/tasks")
    assert res.status_code == 200
    assert res.json() == []


def test_list_filter_and_search(client):
    client.post("/api/tasks", json=_sample_payload(title="買い物"))
    r2 = client.post("/api/tasks", json=_sample_payload(title="掃除", due_date=None))
    # 1件を完了にする
    task2_id = r2.json()["id"]
    client.patch(f"/api/tasks/{task2_id}/toggle")

    # 全件
    res_all = client.get("/api/tasks?filter=all")
    assert len(res_all.json()) == 2

    # 未完了のみ
    res_active = client.get("/api/tasks?filter=active")
    titles = [t["title"] for t in res_active.json()]
    assert titles == ["買い物"]

    # 完了のみ
    res_done = client.get("/api/tasks?filter=completed")
    assert [t["title"] for t in res_done.json()] == ["掃除"]

    # 検索
    res_search = client.get("/api/tasks?search=掃除")
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["title"] == "掃除"


def test_list_invalid_filter(client):
    res = client.get("/api/tasks?filter=unknown")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# 単体取得
# ---------------------------------------------------------------------------
def test_get_task(client):
    created = client.post("/api/tasks", json=_sample_payload()).json()
    res = client.get(f"/api/tasks/{created['id']}")
    assert res.status_code == 200
    assert res.json()["id"] == created["id"]


def test_get_task_not_found(client):
    res = client.get("/api/tasks/9999")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# 更新
# ---------------------------------------------------------------------------
def test_update_task(client):
    created = client.post("/api/tasks", json=_sample_payload()).json()
    res = client.put(
        f"/api/tasks/{created['id']}",
        json={"title": "牛乳と卵を買う", "priority": "low", "completed": True},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "牛乳と卵を買う"
    assert data["priority"] == "low"
    assert data["completed"] is True


def test_update_clear_due_date(client):
    created = client.post("/api/tasks", json=_sample_payload()).json()
    res = client.put(f"/api/tasks/{created['id']}", json={"due_date": None})
    assert res.status_code == 200
    assert res.json()["due_date"] is None


def test_update_task_not_found(client):
    res = client.put("/api/tasks/9999", json={"title": "x"})
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# トグル
# ---------------------------------------------------------------------------
def test_toggle_task(client):
    created = client.post("/api/tasks", json=_sample_payload()).json()
    assert created["completed"] is False

    res1 = client.patch(f"/api/tasks/{created['id']}/toggle")
    assert res1.status_code == 200
    assert res1.json()["completed"] is True

    res2 = client.patch(f"/api/tasks/{created['id']}/toggle")
    assert res2.json()["completed"] is False


def test_toggle_task_not_found(client):
    res = client.patch("/api/tasks/9999/toggle")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# 削除
# ---------------------------------------------------------------------------
def test_delete_task(client):
    created = client.post("/api/tasks", json=_sample_payload()).json()
    res = client.delete(f"/api/tasks/{created['id']}")
    assert res.status_code == 204
    # 削除後は404
    assert client.get(f"/api/tasks/{created['id']}").status_code == 404


def test_delete_task_not_found(client):
    res = client.delete("/api/tasks/9999")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# 統計
# ---------------------------------------------------------------------------
def test_stats(client):
    client.post("/api/tasks", json=_sample_payload(title="A"))
    r2 = client.post("/api/tasks", json=_sample_payload(title="B"))
    client.post("/api/tasks", json=_sample_payload(title="C"))
    client.patch(f"/api/tasks/{r2.json()['id']}/toggle")

    res = client.get("/api/stats")
    assert res.status_code == 200
    assert res.json() == {"total": 3, "completed": 1, "active": 2}
