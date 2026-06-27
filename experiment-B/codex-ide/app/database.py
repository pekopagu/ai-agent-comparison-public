from collections.abc import Generator
from pathlib import Path
import sqlite3

from fastapi import Request


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent.parent / "tasks.db"


def connect(database_path: Path | str = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(database_path: Path | str = DEFAULT_DATABASE_PATH) -> None:
    with connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
                due_date TEXT,
                completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def get_database_path(request: Request) -> Path:
    return Path(getattr(request.app.state, "database_path", DEFAULT_DATABASE_PATH))


def get_db(request: Request) -> Generator[sqlite3.Connection, None, None]:
    connection = connect(get_database_path(request))
    try:
        yield connection
    finally:
        connection.close()
