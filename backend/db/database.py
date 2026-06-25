"""
Database engine + session factory.
Uses SQLite by default (compliance.db in project root).
Swap DATABASE_URL in .env for Postgres/MySQL in production.
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the backend folder (works wherever the process is run from)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./compliance.db")

# connect_args only needed for SQLite (thread safety)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# ── SQLite: enable foreign key enforcement on every connection ────────────────
# Without this, SQLite silently ignores FK constraints and cascade deletes
# only work if SQLAlchemy loads child rows into memory first.
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once at app startup."""
    from db import models  # noqa: F401 — registers models with Base
    Base.metadata.create_all(bind=engine)
