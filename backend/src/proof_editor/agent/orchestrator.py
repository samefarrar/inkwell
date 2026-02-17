"""Orchestrator — manages the writing partner session state machine.

States: task_select → interview → drafting → highlighting → focused
"""

import logging
from typing import Any

from fastapi import WebSocket

from proof_editor.ws_types import (
    DraftHighlight,
    DraftSynthesize,
    ErrorMessage,
    InterviewAnswer,
    StatusMessage,
    TaskSelect,
)

logger = logging.getLogger(__name__)


class Orchestrator:
    """Routes WebSocket messages to the appropriate handler based on state."""

    def __init__(self, websocket: WebSocket) -> None:
        self.ws = websocket
        self.state = "idle"  # idle, interview, drafting, highlighting, focused
        self.session_id: int | None = None
        self.task_type: str = ""
        self.topic: str = ""
        self.conversation_history: list[dict[str, Any]] = []
        self.drafts: list[dict[str, Any]] = []
        self.highlights: list[dict[str, Any]] = []
        self.interview_summary: str = ""
        self.key_material: list[str] = []

        # These get initialized lazily to avoid import-time LLM setup
        self._interviewer: Any = None
        self._generator: Any = None

    async def send(self, msg: Any) -> None:
        """Send a typed message over WebSocket."""
        await self.ws.send_text(msg.model_dump_json())

    async def handle_task_select(self, msg: TaskSelect) -> None:
        """Handle task selection — create session and start interview."""
        from proof_editor.agent.interviewer import Interviewer
        from proof_editor.db import get_session
        from proof_editor.models.session import Session

        self.task_type = msg.task_type
        self.topic = msg.topic
        self.conversation_history = []
        self.drafts = []
        self.highlights = []

        # Create DB session
        with get_session() as db:
            session = Session(
                task_type=msg.task_type,
                topic=msg.topic,
                status="interview",
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            self.session_id = session.id

        self.state = "interview"
        self._interviewer = Interviewer(
            task_type=self.task_type,
            topic=self.topic,
            websocket=self.ws,
        )

        await self.send(
            StatusMessage(message=f"Starting interview for your {msg.task_type}...")
        )

        # Kick off the first question
        await self._interviewer.start()

    async def handle_interview_answer(self, msg: InterviewAnswer) -> None:
        """Handle user's answer during interview phase."""
        if self.state != "interview":
            await self.send(ErrorMessage(message="Not in interview state"))
            return

        if not self._interviewer:
            await self.send(ErrorMessage(message="No active interview"))
            return

        result = await self._interviewer.process_answer(msg.answer)

        if result.get("ready_to_draft"):
            self.interview_summary = result.get("summary", "")
            self.key_material = result.get("key_material", [])
            self.state = "drafting"
            await self._start_drafting()

    async def _start_drafting(self) -> None:
        """Transition to drafting — generate 3 concurrent drafts."""
        from proof_editor.drafting.generator import DraftGenerator

        await self.send(StatusMessage(message="Developing your drafts..."))

        self._generator = DraftGenerator(
            task_type=self.task_type,
            topic=self.topic,
            interview_summary=self.interview_summary,
            key_material=self.key_material,
            websocket=self.ws,
        )

        drafts = await self._generator.generate()
        self.drafts = drafts
        self.state = "highlighting"

    async def handle_highlight(self, msg: DraftHighlight) -> None:
        """Handle highlight from user across drafts."""
        if self.state != "highlighting":
            await self.send(ErrorMessage(message="Not in highlighting state"))
            return

        self.highlights.append(
            {
                "draft_index": msg.draft_index,
                "start": msg.start,
                "end": msg.end,
                "sentiment": msg.sentiment,
                "note": msg.note,
            }
        )

        # Store in DB
        if self.session_id:
            from proof_editor.db import get_session
            from proof_editor.models.highlight import Highlight

            with get_session() as db:
                highlight = Highlight(
                    session_id=self.session_id,
                    draft_index=msg.draft_index,
                    start=msg.start,
                    end=msg.end,
                    sentiment=msg.sentiment,
                    note=msg.note,
                )
                db.add(highlight)
                db.commit()

    async def handle_synthesize(self, msg: DraftSynthesize) -> None:
        """Handle synthesis request — merge highlighted favorites."""
        if self.state != "highlighting":
            await self.send(ErrorMessage(message="Not in highlighting state"))
            return

        # Synthesis is Phase 4 — for now, acknowledge
        await self.send(StatusMessage(message="Synthesis coming in Phase 4"))
