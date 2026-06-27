"""
実験B 共通テスト【グループA: status3値モデル】
対象: Claude Code, Antigravity CLI, Antigravity IDE

各エージェントのAPIパス・データモデルは自由設計のため、
本テストは「観点」を統一しつつ、エージェントごとに
レスポンス構造の差異（配列 vs ラッパー構造等）を吸収する
ヘルパー関数を用意している。

観点（実験Aの共通テストおよび実験Eの発見を踏襲）:
  1. 基本CRUD（作成・一覧・取得・更新・削除）
  2. フィルタ（status）
  3. 異常系（不正なstatus/priority、存在しないID、空titleなど）
  4. PUT部分更新時のnull処理（実験Eで全エージェント共通の盲点として発見）
  5. CORS設定の妥当性（実験Eで複数エージェントが指摘した観点）

実行方法:
    python3 -m pytest test_common_group_a.py -v
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
    "claude-code": {
        "module": "app.main",
        "app_attr": "app",
        "status_values": ["todo", "doing", "done"],
        "list_path": "/api/tasks",
        "create_path": "/api/tasks",
        "task_path": "/api/tasks/{id}",
        "extract_list": lambda data: data,  # 配列をそのまま返す
    },
    "antigravity-cli": {
        "module": "main",
        "app_attr": "app",
        "status_values": ["todo", "in_progress", "done"],
        "list_path": "/api/tasks",
        "create_path": "/api/tasks",
        "task_path": "/api/tasks/{id}",
        "extract_list": lambda data: data,
    },
    "antigravity-ide": {
        "module": "backend.main",
        "app_attr": "app",
        "status_values": ["todo", "in_progress", "done"],
        "list_path": "/api/tasks",
        "create_path": "/api/tasks",
        "task_path": "/api/tasks/{id}",
        "extract_list": lambda data: data,
    },
}


def get_client(agent_id: str, tmp_path) -> TestClient:
    """指定エージェントのFastAPIアプリをTestClientとして返す。

    with文（コンテキストマネージャ）を使わずTestClient(app)を直接返すと
    lifespanイベント（init_db等）が発火しないエージェントがあるため、
    enter_context相当の処理を行い、確実にlifespanを起動させる。
    """
    config = AGENT_CONFIGS[agent_id]
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith(("app", "backend", "main", "models", "schemas", "database", "crud")):
            del sys.modules[mod_name]
    module = importlib.import_module(config["module"])
    app = getattr(module, config["app_attr"])
    client = TestClient(app)
    client.__enter__()  # lifespanイベント（init_db等）を確実に発火させる
    return client


# ============================================================
# フィクスチャ（agent_id をパラメータ化）
# ============================================================

@pytest.fixture(params=list(AGENT_CONFIGS.keys()))
def agent(request, tmp_path, monkeypatch):
    """各エージェントごとにテストDBパスを設定し、クリーンな状態で起動する。"""
    agent_id = request.param
    db_path = tmp_path / f"{agent_id}_test.db"

    # 各エージェントが参照する環境変数名が異なるため、可能性のあるものを全て設定
    monkeypatch.setenv("TASKS_DB_PATH", str(db_path))
    monkeypatch.setenv("TASK_DB_PATH", str(db_path))
    # 注意: monkeypatch.chdir は static ファイルマウント（相対パス指定の
    # エージェント）を壊す可能性があるため使用しない。

    client = get_client(agent_id, tmp_path)
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
        assert "id" in data

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
        # 削除後は404になることを確認
        res2 = client.get(path)
        assert res2.status_code == 404, f"[{agent_id}] 削除後も取得できてしまう"


# ============================================================
# 2. フィルタ（status）
# ============================================================

class TestStatusFilter:

    def test_filter_by_first_status_value(self, agent):
        """各エージェントのstatus許容値の1番目（todo相当）でフィルタする"""
        agent_id, client, config = agent
        status_values = config["status_values"]
        first_status = status_values[0]  # todo

        client.post(config["create_path"], json={"title": "対象タスク"})

        res = client.get(config["list_path"], params={"status": first_status})
        assert res.status_code == 200, f"[{agent_id}] statusフィルタが200でない"
        items = config["extract_list"](res.json())
        assert all(item.get("status") == first_status for item in items), (
            f"[{agent_id}] フィルタ結果に{first_status}以外が含まれる"
        )


# ============================================================
# 3. 異常系
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
        """不正なpriorityが拒否されるか（Antigravity IDEで検証漏れが発覚した観点）"""
        agent_id, client, config = agent
        res = client.post(config["create_path"], json={"title": "テスト", "priority": "invalid_value"})
        # この観点が機能しないエージェントが存在することを記録するため、
        # アサーションは行わず結果を記録する（xfail的に扱う）
        if res.status_code not in (422,):
            pytest.xfail(
                f"[{agent_id}] 不正なpriority('invalid_value')が拒否されず "
                f"status={res.status_code} で受け入れられた（バリデーション漏れ）"
            )


# ============================================================
# 4. PUT部分更新時のnull処理（実験Eで発見された全エージェント共通の盲点）
# ============================================================

class TestPartialUpdateNullHandling:

    def test_partial_update_without_title_does_not_fail(self, agent):
        """部分更新（titleを含まない更新）が422にならないことを確認する。

        実験Eで発見された問題: TaskUpdate(TaskBase)継承等により
        titleが暗黙的に必須化され、部分更新が機能しないケースがあった。
        """
        agent_id, client, config = agent
        created = client.post(config["create_path"], json={"title": "部分更新テスト"}).json()
        path = config["task_path"].format(id=created["id"])

        status_values = config["status_values"]
        res = client.put(path, json={"status": status_values[1]})  # doing/in_progress相当のみ送る

        if res.status_code == 422:
            pytest.fail(
                f"[{agent_id}] titleを含まない部分更新が422で拒否された "
                f"（PUT部分更新の重大バグ）: {res.text}"
            )
        assert res.status_code == 200, f"[{agent_id}] 部分更新が200でない: {res.text}"

        # タイトルが意図せず変更/消失していないか確認
        updated = res.json()
        assert updated["title"] == "部分更新テスト", (
            f"[{agent_id}] 部分更新でtitleが意図せず変化した: {updated}"
        )

    def test_partial_update_preserves_unspecified_fields(self, agent):
        """未指定フィールドが上書き消去されないことを確認する"""
        agent_id, client, config = agent
        created = client.post(
            config["create_path"],
            json={"title": "保持確認", "description": "残るはずの説明", "priority": "high"},
        ).json()
        path = config["task_path"].format(id=created["id"])

        status_values = config["status_values"]
        res = client.put(path, json={"status": status_values[2]})  # done相当のみ送る

        if res.status_code != 200:
            pytest.skip(f"[{agent_id}] 部分更新自体が失敗するため本観点は評価不能")

        updated = res.json()
        if updated.get("description") != "残るはずの説明":
            pytest.fail(
                f"[{agent_id}] 未指定フィールド(description)が消失/変化した: {updated}"
            )
        if updated.get("priority") != "high":
            pytest.fail(
                f"[{agent_id}] 未指定フィールド(priority)が消失/変化した: {updated}"
            )
