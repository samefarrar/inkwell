"""Preference model — key-value store for learned user preferences."""

from datetime import UTC, datetime

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, SQLModel


class Preference(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    key: str = Field(index=True)
    value: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
