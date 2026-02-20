"""Style management REST endpoints — scoped to authenticated user."""

import asyncio
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

import pymupdf
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlmodel import select

from proof_editor.auth_deps import get_current_user
from proof_editor.db import db_session
from proof_editor.models.style import StyleSample, WritingStyle
from proof_editor.models.user import User
from proof_editor.storage import upload_to_gcs

router = APIRouter(prefix="/api/styles", tags=["styles"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_PDF_PAGES = 100
MAX_PDF_TEXT_BYTES = 1_000_000  # 1 MB text cap
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}


def _extract_pdf_text(data: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF. Sync — run via to_thread."""
    doc = pymupdf.open(stream=data, filetype="pdf")
    try:
        if len(doc) > MAX_PDF_PAGES:
            raise ValueError(f"PDF has {len(doc)} pages, max {MAX_PDF_PAGES}")
        parts: list[str] = []
        total_len = 0
        for page in doc:
            text = page.get_text(sort=True)
            total_len += len(text)
            if total_len > MAX_PDF_TEXT_BYTES:
                break
            parts.append(text.strip())
        return "\n\n".join(p for p in parts if p)
    finally:
        doc.close()


class StyleCreate(BaseModel):
    name: str = Field(max_length=200)
    description: str = Field(default="", max_length=2000)
    tone: str | None = Field(default=None, max_length=50)
    audience: str | None = Field(default=None, max_length=200)
    domain: str | None = Field(default=None, max_length=200)


class StyleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    tone: str | None = Field(default=None, max_length=50)
    audience: str | None = Field(default=None, max_length=200)
    domain: str | None = Field(default=None, max_length=200)


class SampleCreate(BaseModel):
    title: str = Field(default="", max_length=500)
    content: str = Field(max_length=500_000)


@router.get("")
def list_styles(user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    """List user's writing styles."""
    with db_session() as db:
        styles = db.exec(
            select(WritingStyle)
            .where(WritingStyle.user_id == user.id)
            .order_by(WritingStyle.updated_at.desc())  # type: ignore[union-attr]
        ).all()
        return [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "tone": s.tone,
                "audience": s.audience,
                "domain": s.domain,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in styles
        ]


@router.post("")
def create_style(
    body: StyleCreate, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Create a new writing style."""
    with db_session() as db:
        style = WritingStyle(
            name=body.name,
            description=body.description,
            tone=body.tone,
            audience=body.audience,
            domain=body.domain,
            user_id=user.id,
        )
        db.add(style)
        db.commit()
        db.refresh(style)
        return {
            "id": style.id,
            "name": style.name,
            "description": style.description,
            "tone": style.tone,
            "audience": style.audience,
            "domain": style.domain,
        }


def _get_user_style(db, style_id: int, user_id: int) -> WritingStyle:  # type: ignore[no-untyped-def]
    """Get a style, verifying ownership. Raises 404 if not found."""
    style = db.get(WritingStyle, style_id)
    if not style or style.user_id != user_id:
        raise HTTPException(404, "Style not found")
    return style


@router.get("/{style_id}")
def get_style(style_id: int, user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Get a style with its samples."""
    with db_session() as db:
        style = _get_user_style(db, style_id, user.id)  # type: ignore[arg-type]

        samples = db.exec(
            select(StyleSample)
            .where(StyleSample.style_id == style_id)
            .order_by(StyleSample.created_at.desc())  # type: ignore[union-attr]
        ).all()

        return {
            "id": style.id,
            "name": style.name,
            "description": style.description,
            "tone": style.tone,
            "audience": style.audience,
            "domain": style.domain,
            "samples": [
                {
                    "id": s.id,
                    "title": s.title,
                    "content": s.content,
                    "source_type": s.source_type,
                    "word_count": s.word_count,
                    "created_at": s.created_at.isoformat(),
                }
                for s in samples
            ],
        }


@router.put("/{style_id}")
def update_style(
    style_id: int, body: StyleUpdate, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Update a style's name or description."""
    with db_session() as db:
        style = _get_user_style(db, style_id, user.id)  # type: ignore[arg-type]

        if body.name is not None:
            style.name = body.name
        if body.description is not None:
            style.description = body.description
        if body.tone is not None:
            style.tone = body.tone
        if body.audience is not None:
            style.audience = body.audience
        if body.domain is not None:
            style.domain = body.domain
        style.updated_at = datetime.now(UTC)
        db.commit()
        db.refresh(style)
        return {
            "id": style.id,
            "name": style.name,
            "description": style.description,
            "tone": style.tone,
            "audience": style.audience,
            "domain": style.domain,
        }


@router.delete("/{style_id}")
def delete_style(
    style_id: int, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """Delete a style and all its samples."""
    with db_session() as db:
        style = _get_user_style(db, style_id, user.id)  # type: ignore[arg-type]

        samples = db.exec(
            select(StyleSample).where(StyleSample.style_id == style_id)
        ).all()
        for s in samples:
            db.delete(s)
        db.delete(style)
        db.commit()
        return {"status": "deleted"}


@router.post("/{style_id}/samples")
def add_sample(
    style_id: int, body: SampleCreate, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Add a text sample to a style."""
    with db_session() as db:
        _get_user_style(db, style_id, user.id)  # type: ignore[arg-type]

        word_count = len(body.content.split())
        sample = StyleSample(
            style_id=style_id,
            title=body.title,
            content=body.content,
            source_type="paste",
            word_count=word_count,
        )
        db.add(sample)
        db.commit()
        db.refresh(sample)
        return {
            "id": sample.id,
            "title": sample.title,
            "word_count": sample.word_count,
            "source_type": sample.source_type,
        }


@router.post("/{style_id}/samples/upload")
async def upload_sample(
    style_id: int, file: UploadFile, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Upload a document as a style sample (txt, md, pdf)."""
    safe_name = PurePosixPath(file.filename or "untitled").name
    ext = PurePosixPath(safe_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(ALLOWED_EXTENSIONS)
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {allowed}")

    # Read in chunks to enforce size limit
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(64 * 1024):
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise HTTPException(
                400, f"File too large. Max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB"
            )
        chunks.append(chunk)
    raw_bytes = b"".join(chunks)

    # Extract text — PDF uses PyMuPDF, others decode as UTF-8
    if ext == ".pdf":
        try:
            text = await asyncio.to_thread(_extract_pdf_text, raw_bytes)
        except ValueError as e:
            raise HTTPException(400, str(e))
    else:
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(400, "File must be valid UTF-8 text")

    # Derive content type from extension (don't trust client-provided value)
    ext_to_mime = {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".pdf": "application/pdf",
    }
    content_type = ext_to_mime.get(ext, "application/octet-stream")
    gcs_uri = await asyncio.to_thread(
        upload_to_gcs, raw_bytes, style_id, safe_name, content_type
    )

    word_count = len(text.split())
    title = PurePosixPath(safe_name).stem

    with db_session() as db:
        _get_user_style(db, style_id, user.id)  # type: ignore[arg-type]

        sample = StyleSample(
            style_id=style_id,
            title=title,
            content=text,
            source_type="upload",
            word_count=word_count,
            gcs_uri=gcs_uri or "",
        )
        db.add(sample)
        db.commit()
        db.refresh(sample)
        return {
            "id": sample.id,
            "title": sample.title,
            "word_count": sample.word_count,
            "source_type": sample.source_type,
        }


@router.post("/{style_id}/analyze")
async def analyze_style(
    style_id: int, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Run 'What do you notice?' LLM analysis on all samples for this style.

    Extracts a structured voice profile and stores it in the Preference table.
    Returns the extracted profile.
    """
    from proof_editor.learning import save_voice_profile
    from proof_editor.learning.pattern_extractor import extract_patterns

    with db_session() as db:
        _get_user_style(db, style_id, user.id)  # type: ignore[arg-type]
        samples = db.exec(
            select(StyleSample).where(StyleSample.style_id == style_id)
        ).all()

    if not samples:
        raise HTTPException(400, "Add at least one writing sample before analyzing")

    profile = await extract_patterns(samples)
    if not profile:
        raise HTTPException(500, "Analysis failed — please try again")

    save_voice_profile(user.id, style_id, profile)  # type: ignore[arg-type]
    return profile


@router.get("/{style_id}/voice_profile")
def get_voice_profile(
    style_id: int, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Return the stored voice profile for this style, or 404 if not analyzed yet."""
    from proof_editor.learning import load_voice_profile

    _get_user_style_by_id(style_id, user.id)  # type: ignore[arg-type]
    profile = load_voice_profile(user.id, style_id)  # type: ignore[arg-type]
    if not profile:
        raise HTTPException(404, "No voice profile yet — run /analyze first")
    return profile


def _get_user_style_by_id(style_id: int, user_id: int) -> None:
    """Verify style ownership without keeping a DB session open."""
    with db_session() as db:
        _get_user_style(db, style_id, user_id)


@router.delete("/{style_id}/samples/{sample_id}")
def delete_sample(
    style_id: int, sample_id: int, user: User = Depends(get_current_user)
) -> dict[str, str]:
    """Delete a specific sample from a style."""
    with db_session() as db:
        _get_user_style(db, style_id, user.id)  # type: ignore[arg-type]

        sample = db.get(StyleSample, sample_id)
        if not sample or sample.style_id != style_id:
            raise HTTPException(404, "Sample not found")
        db.delete(sample)
        db.commit()
        return {"status": "deleted"}
