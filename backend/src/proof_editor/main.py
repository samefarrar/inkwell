"""FastAPI application — entry point for the Proof Editor backend."""

import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from proof_editor.agent.orchestrator import Orchestrator
from proof_editor.db import create_tables
from proof_editor.ws_types import (
    DraftEdit,
    DraftHighlight,
    DraftSynthesize,
    ErrorMessage,
    HighlightRemove,
    HighlightUpdate,
    InterviewAnswer,
    TaskSelect,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown events."""
    from pathlib import Path

    from dotenv import load_dotenv

    # Load .env in worker process (main() only runs in reloader parent)
    env_path = Path(__file__).resolve().parents[3] / ".env"
    load_dotenv(env_path)

    logging.basicConfig(level=logging.INFO, force=True)
    create_tables()
    logger.info("Database tables created")
    yield


app = FastAPI(title="Proof Editor", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/sessions")
async def list_sessions() -> list[dict[str, Any]]:
    """Return all sessions with summary metadata, newest first."""
    from sqlmodel import func, select

    from proof_editor.db import get_session
    from proof_editor.models.draft import Draft
    from proof_editor.models.session import Session

    with get_session() as db:
        sessions = db.exec(
            select(Session).order_by(Session.created_at.desc())  # type: ignore[union-attr]
        ).all()

        result = []
        for sess in sessions:
            # Count drafts and find max round
            draft_count_stmt = select(func.count()).where(Draft.session_id == sess.id)
            draft_count = db.exec(draft_count_stmt).one()

            max_round_stmt = select(func.max(Draft.round)).where(
                Draft.session_id == sess.id
            )
            max_round = db.exec(max_round_stmt).one() or 0

            result.append(
                {
                    "id": sess.id,
                    "task_type": sess.task_type,
                    "topic": sess.topic,
                    "status": sess.status,
                    "draft_count": draft_count,
                    "max_round": max_round,
                    "created_at": sess.created_at.isoformat(),
                }
            )

        return result


@app.get("/api/sessions/{session_id}")
async def get_session_detail(session_id: int) -> dict[str, Any]:
    """Return full session detail: interview + drafts by round + highlights."""
    from sqlmodel import select

    from proof_editor.db import get_session
    from proof_editor.models.draft import Draft
    from proof_editor.models.highlight import Highlight
    from proof_editor.models.interview_message import InterviewMessage
    from proof_editor.models.session import Session

    with get_session() as db:
        sess = db.get(Session, session_id)
        if not sess:
            return {"found": False}

        # Interview messages
        im_stmt = (
            select(InterviewMessage)
            .where(InterviewMessage.session_id == session_id)
            .order_by(InterviewMessage.ordering)
        )
        interview_msgs = db.exec(im_stmt).all()

        # All drafts grouped by round
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

        # Highlights
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


@app.get("/api/sessions/latest")
async def latest_session() -> dict[str, Any]:
    """Return the most recent session that has drafts."""
    from sqlmodel import select

    from proof_editor.db import get_session
    from proof_editor.models.draft import Draft
    from proof_editor.models.highlight import Highlight
    from proof_editor.models.session import Session

    with get_session() as db:
        # Find session IDs that have drafts
        session_ids_with_drafts = select(Draft.session_id).distinct()
        stmt = (
            select(Session)
            .where(Session.id.in_(session_ids_with_drafts))  # type: ignore[union-attr]
            .order_by(Session.created_at.desc())  # type: ignore[union-attr]
            .limit(1)
        )
        sess = db.exec(stmt).first()
        if not sess:
            return {"found": False}

        # Get max round
        max_round_stmt = (
            select(Draft.round)
            .where(Draft.session_id == sess.id)
            .order_by(Draft.round.desc())  # type: ignore[union-attr]
            .limit(1)
        )
        max_round = db.exec(max_round_stmt).first() or 0

        # Load latest-round drafts
        draft_stmt = (
            select(Draft)
            .where(Draft.session_id == sess.id)
            .where(Draft.round == max_round)
            .order_by(Draft.draft_index)
        )
        db_drafts = db.exec(draft_stmt).all()

        # Load highlights
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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Main WebSocket endpoint for the writing partner workflow."""
    await websocket.accept()
    orchestrator = Orchestrator(websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(
                    ErrorMessage(message="Invalid JSON").model_dump_json()
                )
                continue

            msg_type = data.get("type")
            try:
                if msg_type == "task.select":
                    await orchestrator.handle_task_select(TaskSelect(**data))
                elif msg_type == "interview.answer":
                    await orchestrator.handle_interview_answer(InterviewAnswer(**data))
                elif msg_type == "draft.highlight":
                    await orchestrator.handle_highlight(DraftHighlight(**data))
                elif msg_type == "highlight.update":
                    await orchestrator.handle_highlight_update(HighlightUpdate(**data))
                elif msg_type == "highlight.remove":
                    await orchestrator.handle_highlight_remove(HighlightRemove(**data))
                elif msg_type == "draft.edit":
                    msg_edit = DraftEdit(**data)
                    await orchestrator.handle_draft_edit(
                        msg_edit.draft_index, msg_edit.content
                    )
                elif msg_type == "draft.synthesize":
                    await orchestrator.handle_synthesize(DraftSynthesize(**data))
                elif msg_type == "session.resume":
                    from proof_editor.ws_types import SessionResume

                    await orchestrator.handle_resume(SessionResume(**data).session_id)
                else:
                    await websocket.send_text(
                        ErrorMessage(
                            message=f"Unknown message type: {msg_type}"
                        ).model_dump_json()
                    )
            except ValidationError as e:
                await websocket.send_text(
                    ErrorMessage(
                        message=f"Validation error: {e.error_count()} errors"
                    ).model_dump_json()
                )

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")


def main() -> None:
    """Run the server."""
    from pathlib import Path

    import uvicorn
    from dotenv import load_dotenv

    # Load .env from project root before starting server
    env_path = Path(__file__).resolve().parents[3] / ".env"
    load_dotenv(env_path)

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "proof_editor.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
