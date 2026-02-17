"""Database setup — SQLite via SQLModel."""

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DATA_DIR / "proof_editor.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def create_tables() -> None:
    """Create all tables if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Import models so SQLModel registers them
    from proof_editor.models import (  # noqa: F401
        draft,
        feedback,
        highlight,
        preference,
        session,
    )

    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Get a new database session."""
    return Session(engine)
