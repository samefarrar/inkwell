"""Feedback model — tracks accepted/rejected style suggestions."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Feedback(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
    draft_index: int | None = None
    text: str
    replacement: str | None = None
    accepted: bool
    rule_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
