"""Highlight model — tracks text the user liked or flagged across drafts."""

from datetime import UTC, datetime

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class Highlight(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("session.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    draft_index: int
    start: int
    end: int
    text: str = ""
    sentiment: str  # "like" or "flag"
    label: str = ""  # custom snake_cased label (empty = use sentiment as tag)
    note: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
