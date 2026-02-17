"""Highlight model — tracks text the user liked or flagged across drafts."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Highlight(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
    draft_index: int
    start: int
    end: int
    text: str = ""
    sentiment: str  # "like" or "flag"
    label: str = ""  # custom snake_cased label (empty = use sentiment as tag)
    note: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
