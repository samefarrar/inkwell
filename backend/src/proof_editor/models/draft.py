"""Draft model — persists generated drafts across synthesis rounds."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Draft(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id", index=True)
    draft_index: int
    title: str
    angle: str
    content: str
    word_count: int
    round: int = 0  # 0 = original 3 drafts, 1+ = synthesis rounds
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
