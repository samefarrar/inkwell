"""Preference model — key-value store for learned user preferences."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Preference(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    key: str = Field(index=True)
    value: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
