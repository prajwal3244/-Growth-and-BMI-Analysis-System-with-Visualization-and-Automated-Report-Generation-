"""SQLAlchemy declarative base and engine/session factory.

A single ``Base`` and ``SessionLocal`` are shared by models and the API. Using a
URL from settings means the same code runs on SQLite in dev and PostgreSQL in
prod with no changes (Dependency Inversion at the infrastructure boundary).
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from growthai.config import get_settings

settings = get_settings()

# ``check_same_thread`` only applies to SQLite; harmless elsewhere.
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def init_db() -> None:
    """Create all tables. Called at API startup and in tests."""
    from growthai.db import models  # noqa: F401 - register models

    Base.metadata.create_all(bind=engine)
