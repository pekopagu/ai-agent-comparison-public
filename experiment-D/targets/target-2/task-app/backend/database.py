"""データベース接続とセッション管理を行うモジュール。"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite データベースの接続URL（同一ディレクトリに tasks.db を作成）
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"

# SQLite を FastAPI（マルチスレッド）で利用するため check_same_thread を無効化
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """リクエストごとに DB セッションを生成し、終了時にクローズする。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
