"""Database setup — SQLite via SQLModel with WAL mode and FK enforcement."""

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DATA_DIR / "proof_editor.db"

SCHEMA_VERSION = 2  # Bump when models change

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, connection_record):  # type: ignore[no-untyped-def]
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA busy_timeout = 5000")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.close()


def create_tables() -> None:
    """Create all tables if they don't exist. Auto-wipes stale schema."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Schema version check — auto-wipe stale DB
    if DB_PATH.exists():
        conn = sqlite3.connect(str(DB_PATH))
        current = conn.execute("PRAGMA user_version").fetchone()[0]
        conn.close()
        if current < SCHEMA_VERSION:
            DB_PATH.unlink()
            logger.warning(
                "Schema %d < %d — deleted stale database", current, SCHEMA_VERSION
            )

    # Import all models so SQLModel registers them
    from proof_editor.models import (  # noqa: F401
        draft,
        feedback,
        highlight,
        interview_message,
        preference,
        session,
        style,
        user,
    )

    SQLModel.metadata.create_all(engine)

    # Stamp version
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Database session with guaranteed cleanup and rollback on error."""
    session = Session(engine)
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
