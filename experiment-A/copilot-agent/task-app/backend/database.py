"""データベース接続とセッション管理"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLiteデータベースのURL（backendディレクトリ直下にファイルを作成）
SQLALCHEMY_DATABASE_URL = "sqlite:///./tasks.db"

# SQLiteはデフォルトで同一スレッドのみ許可するため、check_same_thread を無効化
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# セッションファクトリ
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルのベースクラス
Base = declarative_base()


def get_db():
    """リクエストごとにDBセッションを払い出す依存関数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
