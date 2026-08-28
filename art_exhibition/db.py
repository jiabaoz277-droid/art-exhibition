"""SQLite 持久化：SQLAlchemy 引擎与会话，schema 版本标记。"""
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

# 确保 SQLite 文件父目录存在
if settings.database_url.startswith("sqlite:///"):
    Path(settings.database_url[len("sqlite:///"):]).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

SCHEMA_VERSION = 1


def init_db() -> None:
    """建表 + 写入 schema 版本标记（本阶段暂缓 Alembic，见技术适配声明）。"""
    import models  # noqa: F401  确保模型已注册
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"))
        conn.execute(text("INSERT OR IGNORE INTO schema_version (version) VALUES (1)"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
