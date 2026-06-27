"""API テスト用の共通フィクスチャ。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.database import Database
from backend.main import app, get_db


@pytest.fixture()
def client(tmp_path):
    """各テストで独立した一時ファイルDBを使う TestClient を返す。

    sqlite3 の ":memory:" はコネクションごとに別DBになるため、
    コネクションを都度開く本設計ではテスト用に一時ファイルDBを使う。
    """
    db_file = tmp_path / "test_tasks.db"
    test_db = Database(db_file)

    def override_get_db() -> Database:
        return test_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
