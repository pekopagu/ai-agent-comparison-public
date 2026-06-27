def test_create_task(client):
    # 正常系: タスクを新規作成
    payload = {
        "title": "APIのテストを書く",
        "description": "pytestを使ってFastAPIエンドポイントのテストを実装する",
        "status": "todo",
        "priority": "high",
        "due_date": "2026-06-30",
        "tags": ["Python", "Testing"]
    }
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["status"] == payload["status"]
    assert data["priority"] == payload["priority"]
    assert data["due_date"] == payload["due_date"]
    assert len(data["tags"]) == 2
    assert any(t["name"] == "Python" for t in data["tags"])
    assert "id" in data

def test_read_tasks_and_filter(client):
    # テスト用タスクの作成
    client.post("/api/tasks", json={"title": "Task A", "status": "todo", "priority": "low", "tags": ["TagA"]})
    client.post("/api/tasks", json={"title": "Task B", "status": "in_progress", "priority": "medium", "tags": ["TagB"]})
    client.post("/api/tasks", json={"title": "Task C", "status": "done", "priority": "high", "tags": ["TagA", "TagB"]})

    # フィルタリングなし
    response = client.get("/api/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 3

    # ステータスフィルタ
    response = client.get("/api/tasks?status=in_progress")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task B"

    # 優先度フィルタ
    response = client.get("/api/tasks?priority=high")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task C"

    # タグフィルタ
    response = client.get("/api/tasks?tag=TagA")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # 検索フィルタ
    response = client.get("/api/tasks?search=Task")
    assert response.status_code == 200
    assert len(response.json()) == 3

    response = client.get("/api/tasks?search=Task A")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Task A"

def test_update_task(client):
    # タスク作成
    create_resp = client.post("/api/tasks", json={
        "title": "未修正のタスク",
        "description": "初期説明",
        "status": "todo",
        "priority": "low",
        "tags": ["旧タグ"]
    })
    task_id = create_resp.json()["id"]

    # タスク更新
    update_payload = {
        "title": "修正済みのタスク",
        "status": "in_progress",
        "priority": "medium",
        "tags": ["新タグA", "新タグB"]
    }
    response = client.put(f"/api/tasks/{task_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "修正済みのタスク"
    assert data["description"] == "初期説明"  # 未指定のフィールドは維持される
    assert data["status"] == "in_progress"
    assert data["priority"] == "medium"
    assert len(data["tags"]) == 2
    assert any(t["name"] == "新タグA" for t in data["tags"])
    assert not any(t["name"] == "旧タグ" for t in data["tags"])

def test_delete_task(client):
    # タスク作成
    create_resp = client.post("/api/tasks", json={"title": "消されるタスク"})
    task_id = create_resp.json()["id"]

    # 削除実行
    delete_resp = client.delete(f"/api/tasks/{task_id}")
    assert delete_resp.status_code == 204

    # 存在確認
    read_resp = client.get(f"/api/tasks/{task_id}")
    assert read_resp.status_code == 404

    # 重複削除はエラー
    delete_resp_2 = client.delete(f"/api/tasks/{task_id}")
    assert delete_resp_2.status_code == 404

def test_tags_api(client):
    # タグの一覧取得 (最初は空)
    response = client.get("/api/tags")
    assert response.status_code == 200
    assert len(response.json()) == 0

    # タグ作成
    tag_payload = {"name": "開発", "color": "#000000"}
    response = client.post("/api/tags", json=tag_payload)
    assert response.status_code == 201
    tag_data = response.json()
    assert tag_data["name"] == "開発"
    assert tag_data["color"] == "#000000"
    tag_id = tag_data["id"]

    # タグ一覧確認
    response = client.get("/api/tags")
    assert len(response.json()) == 1

    # タグ削除
    response = client.delete(f"/api/tags/{tag_id}")
    assert response.status_code == 204

    # 削除後の確認
    response = client.get("/api/tags")
    assert len(response.json()) == 0

def test_analytics_api(client):
    # 初期状態の分析情報
    response = client.get("/api/analytics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 0
    assert data["completion_rate"] == 0.0

    # 期限切れタスクと完了タスクを含むデータを作成
    # 期限切れ(昨日)のタスク
    import datetime
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    client.post("/api/tasks", json={"title": "期限切れタスク", "status": "todo", "due_date": yesterday})
    client.post("/api/tasks", json={"title": "期日内タスク", "status": "in_progress", "due_date": tomorrow})
    client.post("/api/tasks", json={"title": "完了済タスク", "status": "done", "due_date": yesterday}) # 完了しているので期限切れカウント対象外

    response = client.get("/api/analytics")
    data = response.json()
    assert data["total_tasks"] == 3
    assert data["todo_tasks"] == 1
    assert data["in_progress_tasks"] == 1
    assert data["done_tasks"] == 1
    assert data["overdue_tasks"] == 1
    assert data["completion_rate"] == 33.3 # 1 / 3 * 100
