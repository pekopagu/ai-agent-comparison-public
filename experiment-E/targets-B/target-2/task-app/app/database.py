"""SQLite データベースの接続・初期化を担うモジュール。

標準ライブラリの sqlite3 のみを使用し、外部 ORM には依存しない。
DB ファイルのパスは環境変数 ``TASKS_DB_PATH`` で上書きできる
（テスト時に独立した DB を使うため）。
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# デフォルトの DB ファイル。app/ の1つ上（プロジェクトルート）に置く。
_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "tasks.db"


def get_db_path() -> str:
    """使用する DB ファイルパスを返す（環境変数で上書き可能）。"""
    return os.environ.get("TASKS_DB_PATH", str(_DEFAULT_DB_PATH))


def get_connection() -> sqlite3.Connection:
    """新しい SQLite 接続を返す。

    ``row_factory`` を設定し、結果を辞書ライクに扱えるようにする。
    """
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    # 外部キー制約を有効化（将来の拡張に備える）
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """テーブルが無ければ作成する。アプリ起動時に呼ぶ。"""
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT,
                status      TEXT    NOT NULL DEFAULT 'todo',
                priority    TEXT    NOT NULL DEFAULT 'medium',
                due_date    TEXT,
                created_at  TEXT    NOT NULL,
                updated_at  TEXT    NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()
