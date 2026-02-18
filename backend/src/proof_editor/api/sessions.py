"""Session REST endpoints — scoped to authenticated user."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import func, select

from proof_editor.auth_deps import get_current_user
from proof_editor.db import get_db
from proof_editor.models.draft import Draft
from proof_editor.models.highlight import Highlight
from proof_editor.models.interview_message import InterviewMessage
from proof_editor.models.session import Session
from proof_editor.models.user import User

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("")
def list_sessions(user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    """Return user's sessions with summary metadata, newest first."""
    with get_db() as db:
        stmt = (
            select(
                Session.id,
                Session.task_type,
                Session.topic,
                Session.status,
                Session.created_at,
                func.count(Draft.id).label("draft_count"),
                func.coalesce(func.max(Draft.round), 0).label("max_round"),
            )
            .outerjoin(Draft, Draft.session_id == Session.id)
            .where(Session.user_id == user.id)
            .group_by(Session.id)
            .order_by(Session.created_at.desc())  # type: ignore[union-attr]
            .limit(50)
        )
        rows = db.exec(stmt).all()

        return [
            {
                "id": row[0],
                "task_type": row[1],
                "topic": row[2],
                "status": row[3],
                "created_at": row[4].isoformat(),
                "draft_count": row[5],
                "max_round": row[6],
            }
            for row in rows
        ]


@router.get("/latest")
def latest_session(user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Return the most recent session that has drafts."""
    with get_db() as db:
        session_ids_with_drafts = select(Draft.session_id).distinct()
        stmt = (
            select(Session)
            .where(Session.id.in_(session_ids_with_drafts))  # type: ignore[union-attr]
            .where(Session.user_id == user.id)
            .order_by(Session.created_at.desc())  # type: ignore[union-attr]
            .limit(1)
        )
        sess = db.exec(stmt).first()
        if not sess:
            return {"found": False}

        max_round_stmt = (
            select(Draft.round)
            .where(Draft.session_id == sess.id)
            .order_by(Draft.round.desc())  # type: ignore[union-attr]
            .limit(1)
        )
        max_round = db.exec(max_round_stmt).first() or 0

        draft_stmt = (
            select(Draft)
            .where(Draft.session_id == sess.id)
            .where(Draft.round == max_round)
            .order_by(Draft.draft_index)
        )
        db_drafts = db.exec(draft_stmt).all()

        hl_stmt = (
            select(Highlight)
            .where(Highlight.session_id == sess.id)
            .order_by(Highlight.id)
        )
        db_highlights = db.exec(hl_stmt).all()

        return {
            "found": True,
            "session_id": sess.id,
            "task_type": sess.task_type,
            "topic": sess.topic,
            "synthesis_round": max_round,
            "drafts": [
                {
                    "title": d.title,
                    "angle": d.angle,
                    "content": d.content,
                    "word_count": d.word_count,
                }
                for d in db_drafts
            ],
            "highlights": [
                {
                    "draft_index": h.draft_index,
                    "start": h.start,
                    "end": h.end,
                    "text": h.text,
                    "sentiment": h.sentiment,
                    "label": h.label,
                    "note": h.note,
                }
                for h in db_highlights
            ],
        }


@router.get("/{session_id}")
def get_session_detail(
    session_id: int, user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Return full session detail: interview + drafts by round + highlights."""
    with get_db() as db:
        sess = db.get(Session, session_id)
        if not sess or sess.user_id != user.id:
            return {"found": False}

        im_stmt = (
            select(InterviewMessage)
            .where(InterviewMessage.session_id == session_id)
            .order_by(InterviewMessage.ordering)
        )
        interview_msgs = db.exec(im_stmt).all()

        draft_stmt = (
            select(Draft)
            .where(Draft.session_id == session_id)
            .order_by(Draft.round, Draft.draft_index)
        )
        db_drafts = db.exec(draft_stmt).all()

        rounds: dict[int, list[dict[str, Any]]] = {}
        for d in db_drafts:
            rounds.setdefault(d.round, []).append(
                {
                    "title": d.title,
                    "angle": d.angle,
                    "content": d.content,
                    "word_count": d.word_count,
                    "draft_index": d.draft_index,
                }
            )

        hl_stmt = (
            select(Highlight)
            .where(Highlight.session_id == session_id)
            .order_by(Highlight.id)
        )
        db_highlights = db.exec(hl_stmt).all()

        return {
            "found": True,
            "session_id": sess.id,
            "task_type": sess.task_type,
            "topic": sess.topic,
            "status": sess.status,
            "created_at": sess.created_at.isoformat(),
            "interview_messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "thought_json": m.thought_json,
                    "search_json": m.search_json,
                    "ready_json": m.ready_json,
                    "ordering": m.ordering,
                }
                for m in interview_msgs
            ],
            "rounds": {str(k): v for k, v in sorted(rounds.items())},
            "highlights": [
                {
                    "draft_index": h.draft_index,
                    "start": h.start,
                    "end": h.end,
                    "text": h.text,
                    "sentiment": h.sentiment,
                    "label": h.label,
                    "note": h.note,
                }
                for h in db_highlights
            ],
        }
