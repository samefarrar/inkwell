"""Session model — tracks a writing session from task to final draft."""

from datetime import UTC, datetime

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class Session(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    task_type: str  # essay, review, newsletter, landing_page, blog_post
    topic: str
    status: str = "interview"  # interview, drafting, highlighting, focused
    interview_summary: str | None = None
    key_material: str | None = None  # JSON list of key material strings
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
