"""
Database configuration and session management
"""
import logging
from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.engine import Engine

from .config import settings

logger = logging.getLogger(__name__)

DATABASE_URL = f"sqlite:///{settings.database_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 20
    },
    echo=False,
    pool_pre_ping=True
)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable WAL mode and foreign keys for better SQLite performance"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=1000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """Create all tables if they don't exist"""
    logger.info("Initializing database schema...")

    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Import here to ensure models are registered before create_all
    from .models.database_models import Conversation, Message, Setting  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info(f"Database ready at: {settings.database_path}")


def get_database_info() -> dict:
    """Return diagnostic information about the database"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "connected",
            "path": settings.database_path,
            "exists": Path(settings.database_path).exists()
        }
    except Exception as e:
        logger.error(f"Database info error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "path": settings.database_path,
            "exists": Path(settings.database_path).exists()
        }


async def check_database_health() -> bool:
    """Async health check — returns True if the database is reachable"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
