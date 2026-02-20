"""FastAPI application — entry point for the Inkwell backend."""

import json
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import jwt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from starlette.requests import Request

from proof_editor.agent.orchestrator import Orchestrator
from proof_editor.api.auth import router as auth_router
from proof_editor.api.sessions import router as sessions_router
from proof_editor.api.styles import router as styles_router
from proof_editor.api.voice import router as voice_router
from proof_editor.auth_deps import JWT_ALGORITHM, _get_secret_key
from proof_editor.db import create_tables
from proof_editor.ws_types import (
    DraftEdit,
    DraftHighlight,
    DraftSynthesize,
    ErrorMessage,
    FocusChat,
    FocusEnter,
    FocusFeedbackMsg,
    HighlightRemove,
    HighlightUpdate,
    InterviewAnswer,
    SessionResume,
    TaskSelect,
)

logger = logging.getLogger(__name__)


def _get_allowed_origins() -> set[str]:
    """Build allowed origins from env var + dev defaults."""
    origins = {
        "http://localhost:5173",
        "http://localhost:4173",
        "http://localhost:8323",
        "http://65.109.63.226:8323",
    }
    extra = os.environ.get("CORS_ORIGINS", "")
    if extra:
        origins.update(o.strip() for o in extra.split(",") if o.strip())
    return origins


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown events."""
    from pathlib import Path

    from dotenv import load_dotenv

    # Load .env in worker process (main() only runs in reloader parent)
    env_path = Path(__file__).resolve().parents[3] / ".env"
    load_dotenv(env_path)

    # Validate JWT secret early (will raise RuntimeError if < 32 chars)
    _get_secret_key()

    logging.basicConfig(level=logging.INFO, force=True)
    create_tables()
    logger.info("Database tables created")
    yield


app = FastAPI(title="Inkwell", version="0.1.0", lifespan=lifespan)

# CORS — origins from env var
ALLOWED_ORIGINS = _get_allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# CSRF middleware — validate Origin on mutating requests
@app.middleware("http")
async def csrf_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        origin = request.headers.get("origin", "")
        if origin and origin not in ALLOWED_ORIGINS:
            return JSONResponse(status_code=403, content={"detail": "CSRF rejected"})
    return await call_next(request)


app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(styles_router)
app.include_router(voice_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Main WebSocket endpoint for the writing partner workflow."""
    # Auth: extract JWT from cookie before accepting
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=4001, reason="Not authenticated")
        return
    try:
        secret = _get_secret_key()
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Origin check
    origin = websocket.headers.get("origin", "")
    if origin and origin not in ALLOWED_ORIGINS:
        await websocket.close(code=4003, reason="Origin not allowed")
        return

    await websocket.accept()
    orchestrator = Orchestrator(websocket, user_id=user_id)

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
                    await orchestrator.handle_resume(SessionResume(**data).session_id)
                elif msg_type == "focus.enter":
                    await orchestrator.handle_focus_enter(FocusEnter(**data))
                elif msg_type == "focus.exit":
                    await orchestrator.handle_focus_exit()
                elif msg_type == "focus.feedback":
                    await orchestrator.handle_focus_feedback(FocusFeedbackMsg(**data))
                elif msg_type == "focus.chat":
                    await orchestrator.handle_focus_chat(FocusChat(**data))
                elif msg_type == "session.cancel":
                    await orchestrator.handle_cancel()
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
        port=8322,
        reload=True,
    )


if __name__ == "__main__":
    main()
