"""Request-scoped session dependency for FastAPI."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from growthai.db.base import SessionLocal


def get_db() -> Iterator[Session]:
    """Yield a DB session and guarantee it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
