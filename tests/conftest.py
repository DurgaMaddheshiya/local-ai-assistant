"""
Test configuration and shared fixtures.

Key design:
- A single SQLite in-memory connection is kept open for the entire session
  so the in-memory DB (and its tables) survives between tests.
- Every session/test uses a nested SAVEPOINT transaction.  On teardown we
  roll back to the SAVEPOINT, so tests are isolated without needing to
  re-create tables.
- The FastAPI get_db dependency is overridden to use the same session so
  HTTP tests hit the same data as direct model tests.
"""
import os
import pytest

# -----------------------------------------------------------------------
# Environment must be set BEFORE any backend module is imported
# -----------------------------------------------------------------------
os.environ["DATABASE_PATH"] = ":memory:"
os.environ["OLLAMA_HOST"]   = "http://127.0.0.1:11434"
os.environ["OLLAMA_MODEL"]  = "qwen2.5:3b"
os.environ["HOST"]          = "127.0.0.1"
os.environ["PORT"]          = "8000"
os.environ["LOG_LEVEL"]     = "WARNING"

# -----------------------------------------------------------------------
# Backend imports (they pick up the env vars above)
# -----------------------------------------------------------------------
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

import backend.database as db_module
from backend.database import Base, get_db
from backend.main import app

# Ensure all models are registered with Base.metadata
from backend.models.database_models import Conversation, Message, Setting  # noqa: F401


# -----------------------------------------------------------------------
# Session-scoped: one connection that lives for the whole test run
# -----------------------------------------------------------------------

@pytest.fixture(scope="session")
def db_connection():
    """
    One persistent SQLite in-memory connection for the entire test session.
    Keeping it open prevents the in-memory DB from being discarded.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    conn = engine.connect()
    Base.metadata.create_all(bind=conn)
    yield conn
    conn.close()
    engine.dispose()


# -----------------------------------------------------------------------
# Function-scoped: nested SAVEPOINT so each test rolls back cleanly
# -----------------------------------------------------------------------

@pytest.fixture()
def test_db(db_connection):
    """
    DB session bound to the shared connection.
    Uses a SAVEPOINT so we can roll back after each test without
    closing the connection (which would destroy the in-memory DB).
    """
    transaction = db_connection.begin_nested()   # SAVEPOINT
    SessionFactory = sessionmaker(bind=db_connection)
    session = SessionFactory()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()   # roll back to SAVEPOINT


# -----------------------------------------------------------------------
# FastAPI test client
# -----------------------------------------------------------------------

@pytest.fixture()
def client(test_db):
    """Test client whose get_db dependency returns the same session."""
    def _override():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------
# Convenience fixtures
# -----------------------------------------------------------------------

@pytest.fixture()
def sample_conversation(test_db):
    from backend.models.database_models import create_conversation, create_message
    conv = create_conversation(test_db, "Test Conversation", "qwen2.5:3b")
    create_message(test_db, conv.id, "user", "Hello, AI!")
    create_message(test_db, conv.id, "assistant", "Hello! How can I help?")
    return conv
