"""InterviewMessage model — persists interview conversation for session replay."""

from datetime import UTC, datetime

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class InterviewMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("session.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    role: str  # "user", "ai", "thought", "search", "status", "ready_to_draft"
    content: str  # main display text
    thought_json: str | None = None  # JSON for thought blocks
    search_json: str | None = None  # JSON for search results
    ready_json: str | None = None  # JSON for ready_to_draft data
    ordering: int = 0  # monotonic counter for replay order
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
