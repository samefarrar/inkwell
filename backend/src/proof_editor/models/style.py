"""Writing style models — styles and their training samples."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class WritingStyle(SQLModel, table=True):
    __tablename__ = "writing_style"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=200)
    description: str = Field(default="", max_length=2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StyleSample(SQLModel, table=True):
    __tablename__ = "style_sample"

    id: int | None = Field(default=None, primary_key=True)
    style_id: int = Field(foreign_key="writing_style.id", index=True)
    title: str = Field(default="", max_length=500)
    content: str
    source_type: str = "paste"  # "upload" | "paste"
    word_count: int = 0
    gcs_uri: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
