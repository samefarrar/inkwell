"""User model — authentication and plan management."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import field_validator
from sqlmodel import Field, SQLModel


class Plan(StrEnum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    hashed_password: str
    plan: Plan = Field(default=Plan.FREE)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserCreate(SQLModel):
    """Registration form input."""

    email: str
    name: str
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            msg = "Password must be at least 8 characters"
            raise ValueError(msg)
        return v


class UserRead(SQLModel):
    """API response — never includes password hash."""

    id: int
    email: str
    name: str
    plan: Plan
    created_at: datetime
