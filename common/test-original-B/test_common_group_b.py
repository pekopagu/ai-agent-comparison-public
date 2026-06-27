"""
実験B 共通テスト【グループB: completed2値モデル】
対象: Codex CLI, Codex IDE, Copilot Agent

観点（実験Aの共通テストおよび実験Eの発見を踏襲）:
  1. 基本CRUD（作成・一覧・取得・更新・削除）
  2. フィルタ（active/completed）
  3. toggle（完了状態の切り替え）
  4. 異常系（不正なpriority、存在しないID、空titleなど）
  5. PUT部分更新時のnull処理（実験Eで発見された盲点）

実行方法:
    python3 -m pytest test_common_group_b.py -v
"""
from __future__ import annotations

import importlib
import sys

import pytest
from fastapi.testclient import TestClient


# ============================================================
# エージェントごとのアプリ取得・レスポンス正規化
# ============================================================

AGENT_CONFIGS = {
    "codex-cli": {
        "module": "app.main",
        "app_attr": "app",
        "list_path": "/api/tasks",
        "create_path": "/api/tasks",
        "task_path": "/api/tasks/{id}",
        "toggle_path": "/api/tasks/{id}/toggle",
        "status_filter_param": "status",  # active / completed
        "extract_list": lambda data: data,  # 配列を直接返す
    },
    "codex-ide": {
        "module": "app.main",
        "app_attr": "app",
        "list_path": "/api/tasks",
        "create_path": "/api/tasks",
        "task_path": "/api/tasks/{id}",
        "toggle_path": "/api/tasks/{id}/toggle",
        "status_filter_param": "status",  # all / active / completed
        "extract_list": lambda data: data["items"],  # {items, total, active, completed} ラッパー
    },
    "copilot-agent": {
        "module": "backend.main",
        "app_attr": "app",
        "list_path": "/api/tasks",
        "create_path": "/api/tasks",
        "task_path": "/api/tasks/{id}",
        "toggle_path": "/api/tasks/{id}/toggle",
        "status_filter_param": "filter",  # all / active / completed
        "extract_list": lambda data: data,
    },
}


def get_client(agent_id: str, db_path) -> TestClient:
    """指定エージェントのFastAPIアプリをTestClientとして返す（lifespan発火を保証）。

    codex-ideは app.state.database_path、copilot-agentは
    app.dependency_overrides という、それぞれ独自の仕組みでDBパスを
    切り替えるため、個別に対応する。
    """
    config = AGENT_CONFIGS[agent_id]
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith(("app", "backend", "main", "models", "schemas", "database", "repository")):
            del sys.modules[mod_name]
    module = importlib.import_module(config["module"])
    app = getattr(module, config["app_attr"])

    if agent_id == "codex-ide":
        app.state.database_path = db_path  # lifespan発火前に設定する
    elif agent_id == "copilot-agent":
        database_module = importlib.import_module("backend.database")
        test_db = database_module.Database(db_path)
        app.dependency_overrides[module.get_db] = lambda: test_db

    client = TestClient(app)
    client.__enter__()
    return client


@pytest.fixture(params=list(AGENT_CONFIGS.keys()))
def agent(request, tmp_path, monkeypatch):
    agent_id = request.param
    db_path = tmp_path / f"{agent_id}_test.db"

    monkeypatch.setenv("TASKS_DB_PATH", str(db_path))
    monkeypatch.setenv("TASK_DB_PATH", str(db_path))
    # 注意: monkeypatch.chdir は static ファイルマウント（相対パス "static"）を
    # 壊すエージェントがあるため使用しない。カレントディレクトリは
    # pytest実行時の各エージェントのプロジェクトルートのままにする。

    client = get_client(agent_id, db_path)
    config = AGENT_CONFIGS[agent_id]
    return agent_id, client, config


# ============================================================
# 1. 基本CRUD
# ============================================================

class TestBasicCRUD:

    def test_create_task(self, agent):
        agent_id, client, config = agent
        res = client.post(config["create_path"], json={"title": "テストタスク"})
        assert res.status_code == 201, f"[{agent_id}] 作成が201でない: {res.status_code} {res.text}"
        data = res.json()
        assert data["title"] == "テストタスク"
        assert data["completed"] is False, f"[{agent_id}] 新規作成時にcompletedがFalseでない"

    def test_list_tasks(self, agent):
        agent_id, client, config = agent
        client.post(config["create_path"], json={"title": "タスク1"})
        client.post(config["create_path"], json={"title": "タスク2"})
        res = client.get(config["list_path"])
        assert res.status_code == 200, f"[{agent_id}] 一覧取得が200でない"
        items = config["extract_list"](res.json())
        assert len(items) == 2, f"[{agent_id}] 一覧件数が想定と異なる: {items}"

    def test_get_task(self, agent):
        agent_id, client, config = agent
        created = client.post(config["create_path"], json={"title": "詳細取得テスト"}).json()
        path = config["task_path"].format(id=created["id"])
        res = client.get(path)
        assert res.status_code == 200, f"[{agent_id}] 詳細取得が200でない"
        assert res.json()["title"] == "詳細取得テスト"

    def test_update_task(self, agent):
        agent_id, client, config = agent
        created = client.post(config["create_path"], json={"title": "更新前"}).json()
        path = config["task_path"].format(id=created["id"])
        res = client.put(path, json={"title": "更新後"})
        assert res.status_code == 200, f"[{agent_id}] 更新が200でない: {res.text}"
        assert res.json()["title"] == "更新後"

    def test_delete_task(self, agent):
        agent_id, client, config = agent
        created = client.post(config["create_path"], json={"title": "削除対象"}).json()
        path = config["task_path"].format(id=created["id"])
        res = client.delete(path)
        assert res.status_code in (200, 204), f"[{agent_id}] 削除が200/204でない: {res.status_code}"
        res2 = client.get(path)
        assert res2.status_code == 404, f"[{agent_id}] 削除後も取得できてしまう"


# ============================================================
# 2. フィルタ（active / completed）
# ============================================================

class TestStatusFilter:

    def test_filter_by_active(self, agent):
        agent_id, client, config = agent
        client.post(config["create_path"], json={"title": "未完了タスク"})
        param = config["status_filter_param"]
        res = client.get(config["list_path"], params={param: "active"})
        assert res.status_code == 200, f"[{agent_id}] activeフィルタが200でない: {res.text}"
        items = config["extract_list"](res.json())
        assert all(item.get("completed") is False for item in items), (
            f"[{agent_id}] activeフィルタにcompleted=Trueが含まれる"
        )

    def test_filter_by_completed(self, agent):
        agent_id, client, config = agent
        created = client.post(config["create_path"], json={"title": "完了予定タスク"}).json()
        toggle_path = config["toggle_path"].format(id=created["id"])
        client.patch(toggle_path)

        param = config["status_filter_param"]
        res = client.get(config["list_path"], params={param: "completed"})
        assert res.status_code == 200, f"[{agent_id}] completedフィルタが200でない: {res.text}"
        items = config["extract_list"](res.json())
        assert all(item.get("completed") is True for item in items), (
            f"[{agent_id}] completedフィルタにcompleted=Falseが含まれる"
        )


# ============================================================
# 3. toggle（完了状態の切り替え）
# ============================================================

class TestToggle:

    def test_toggle_marks_completed(self, agent):
        agent_id, client, config = agent
        created = client.post(config["create_path"], json={"title": "トグル対象"}).json()
        assert created["completed"] is False

        toggle_path = config["toggle_path"].format(id=created["id"])
        res = client.patch(toggle_path)
        assert res.status_code == 200, f"[{agent_id}] toggleが200でない: {res.text}"
        assert res.json()["completed"] is True, f"[{agent_id}] toggle後にcompletedがTrueになっていない"

    def test_toggle_twice_returns_to_original(self, agent):
        agent_id, client, config = agent
        created = client.post(config["create_path"], json={"title": "二重トグル対象"}).json()
        toggle_path = config["toggle_path"].format(id=created["id"])

        client.patch(toggle_path)
        res = client.patch(toggle_path)
        assert res.status_code == 200
        assert res.json()["completed"] is False, f"[{agent_id}] 2回toggleしても元の状態に戻らない"


# ============================================================
# 4. 異常系
# ============================================================

class TestErrorCases:

    def test_get_nonexistent_task(self, agent):
        agent_id, client, config = agent
        path = config["task_path"].format(id=99999)
        res = client.get(path)
        assert res.status_code == 404, f"[{agent_id}] 存在しないIDで404でない: {res.status_code}"

    def test_create_without_title(self, agent):
        agent_id, client, config = agent
        res = client.post(config["create_path"], json={})
        assert res.status_code == 422, f"[{agent_id}] titleなしで422でない: {res.status_code}"

    def test_create_with_invalid_priority(self, agent):
        agent_id, client, config = agent
        res = client.post(config["create_path"], json={"title": "テスト", "priority": "invalid_value"})
        if res.status_code not in (422,):
            pytest.xfail(
                f"[{agent_id}] 不正なpriority('invalid_value')が拒否されず "
                f"status={res.status_code} で受け入れられた（バリデーション漏れ）"
            )

    def test_toggle_nonexistent_task(self, agent):
        agent_id, client, config = agent
        toggle_path = config["toggle_path"].format(id=99999)
        res = client.patch(toggle_path)
        assert res.status_code == 404, f"[{agent_id}] 存在しないIDのtoggleで404でない: {res.status_code}"


# ============================================================
# 5. PUT部分更新時のnull処理（実験Eで発見された全エージェント共通の盲点）
# ============================================================

class TestPartialUpdateNullHandling:

    def test_partial_update_without_title_does_not_fail(self, agent):
        """部分更新（titleを含まない更新）が422にならないことを確認する。

        実験Eで発見された問題: TaskUpdate(TaskBase)継承等により
        titleが暗黙的に必須化され、部分更新が機能しないケースがあった
        （Codex CLI/Codex IDEともにこのパターンの懸念があった）。
        """
        agent_id, client, config = agent
        created = client.post(config["create_path"], json={"title": "部分更新テスト"}).json()
        path = config["task_path"].format(id=created["id"])

        res = client.put(path, json={"priority": "high"})  # titleを送らない

        if res.status_code == 422:
            pytest.fail(
                f"[{agent_id}] titleを含まない部分更新が422で拒否された "
                f"（PUT部分更新の重大バグ）: {res.text}"
            )
        assert res.status_code == 200, f"[{agent_id}] 部分更新が200でない: {res.text}"

        updated = res.json()
        if updated["title"] != "部分更新テスト":
            pytest.fail(
                f"[{agent_id}] 部分更新でtitleが意図せず変化した: {updated}"
            )

    def test_partial_update_does_not_reset_completed(self, agent):
        """completedを指定しない更新で、completedが意図せずFalseに戻されないことを確認する。

        実験Eで指摘された問題: 「completedを指定せずにリクエストを送ると
        デフォルト値Falseが適用され、タスク状態が強制的に『未完了』に
        巻き戻される」（target-5=codex-cli等で複数レビュアーが指摘）。
        """
        agent_id, client, config = agent
        created = client.post(config["create_path"], json={"title": "完了状態保持テスト"}).json()
        toggle_path = config["toggle_path"].format(id=created["id"])
        client.patch(toggle_path)  # completed = True にする

        path = config["task_path"].format(id=created["id"])
        res = client.put(path, json={"priority": "low"})  # completedを指定しない更新

        if res.status_code != 200:
            pytest.skip(f"[{agent_id}] 部分更新自体が失敗するため本観点は評価不能")

        updated = res.json()
        if updated.get("completed") is False:
            pytest.fail(
                f"[{agent_id}] completedを指定しない更新でTrue→Falseに巻き戻された "
                f"（実験Eで指摘された重大バグの再現）: {updated}"
            )

    def test_partial_update_preserves_unspecified_fields(self, agent):
        """未指定フィールド（description）が上書き消去されないことを確認する"""
        agent_id, client, config = agent
        created = client.post(
            config["create_path"],
            json={"title": "保持確認", "description": "残るはずの説明", "priority": "high"},
        ).json()
        path = config["task_path"].format(id=created["id"])

        res = client.put(path, json={"priority": "low"})  # descriptionを指定しない

        if res.status_code != 200:
            pytest.skip(f"[{agent_id}] 部分更新自体が失敗するため本観点は評価不能")

        updated = res.json()
        if updated.get("description") != "残るはずの説明":
            pytest.fail(
                f"[{agent_id}] 未指定フィールド(description)が消失/変化した: {updated}"
            )
