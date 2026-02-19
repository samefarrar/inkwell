"""Feedback model — tracks accepted/rejected style suggestions."""

from datetime import UTC, datetime
from typing import Literal

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class Feedback(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("session.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    draft_index: int | None = None
    text: str
    replacement: str | None = None
    accepted: bool
    rule_id: str | None = None
    action: Literal["accept", "reject", "dismiss"] | None = None
    feedback_type: Literal["suggestion", "comment"] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
