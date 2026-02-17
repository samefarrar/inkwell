"""FastAPI application — entry point for the Proof Editor backend."""

import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from proof_editor.agent.orchestrator import Orchestrator
from proof_editor.db import create_tables
from proof_editor.ws_types import (
    DraftHighlight,
    DraftSynthesize,
    ErrorMessage,
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
                    msg = TaskSelect(**data)
                    await orchestrator.handle_task_select(msg)
                elif msg_type == "interview.answer":
                    msg_answer = InterviewAnswer(**data)
                    await orchestrator.handle_interview_answer(msg_answer)
                elif msg_type == "draft.highlight":
                    msg_highlight = DraftHighlight(**data)
                    await orchestrator.handle_highlight(msg_highlight)
                elif msg_type == "draft.synthesize":
                    msg_synth = DraftSynthesize(**data)
                    await orchestrator.handle_synthesize(msg_synth)
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
