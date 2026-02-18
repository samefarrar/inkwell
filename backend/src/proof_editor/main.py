"""FastAPI application — entry point for the Inkwell backend."""

import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from proof_editor.agent.orchestrator import Orchestrator
from proof_editor.api.sessions import router as sessions_router
from proof_editor.api.styles import router as styles_router
from proof_editor.db import create_tables
from proof_editor.ws_types import (
    DraftEdit,
    DraftHighlight,
    DraftSynthesize,
    ErrorMessage,
    HighlightRemove,
    HighlightUpdate,
    InterviewAnswer,
    SessionCancel,
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


app = FastAPI(title="Inkwell", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)
app.include_router(styles_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


ALLOWED_ORIGINS = {"http://localhost:5173", "http://localhost:4173"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Main WebSocket endpoint for the writing partner workflow."""
    origin = websocket.headers.get("origin", "")
    if origin not in ALLOWED_ORIGINS:
        await websocket.close(code=4003, reason="Origin not allowed")
        return
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
                elif msg_type == "session.cancel":
                    SessionCancel(**data)  # validate
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
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
