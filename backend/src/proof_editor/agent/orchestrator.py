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
    HighlightRemove,
    HighlightUpdate,
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
        self.synthesis_round: int = 0

        # These get initialized lazily to avoid import-time LLM setup
        self._interviewer: Any = None
        self._generator: Any = None

    async def send(self, msg: Any) -> None:
        """Send a typed message over WebSocket."""
        await self.ws.send_text(msg.model_dump_json())

    async def handle_task_select(self, msg: TaskSelect) -> None:
        """Handle task selection — create session and start interview."""
        logger.info("task.select: %s / %s", msg.task_type, msg.topic)
        from proof_editor.agent.interviewer import Interviewer
        from proof_editor.agent.search import create_search_provider
        from proof_editor.db import get_session
        from proof_editor.models.session import Session

        self.task_type = msg.task_type
        self.topic = msg.topic
        self.conversation_history = []
        self.drafts = []
        self.highlights = []
        self.synthesis_round = 0

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
        search_provider = create_search_provider()
        self._interviewer = Interviewer(
            task_type=self.task_type,
            topic=self.topic,
            websocket=self.ws,
            search_provider=search_provider,
        )

        await self.send(
            StatusMessage(message=f"Starting interview for your {msg.task_type}...")
        )

        # Kick off the first question
        await self._interviewer.start()

    async def handle_interview_answer(self, msg: InterviewAnswer) -> None:
        """Handle user's answer during interview phase."""
        logger.info("interview.answer received")
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

        # Persist interview summary + key material to session
        if self.session_id:
            import json as _json

            from proof_editor.db import get_session as _get_db
            from proof_editor.models.session import Session as _Session

            with _get_db() as db:
                sess = db.get(_Session, self.session_id)
                if sess:
                    sess.interview_summary = self.interview_summary
                    sess.key_material = _json.dumps(self.key_material)
                    sess.status = "drafting"
                    db.commit()

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
        self._save_drafts()
        self.state = "highlighting"

    def _save_drafts(self) -> None:
        """Persist current drafts to database."""
        if not self.session_id:
            return

        from proof_editor.db import get_session
        from proof_editor.models.draft import Draft
        from proof_editor.models.session import Session as _Session

        with get_session() as db:
            for i, d in enumerate(self.drafts):
                draft = Draft(
                    session_id=self.session_id,
                    draft_index=i,
                    title=d.get("title", ""),
                    angle=d.get("angle", ""),
                    content=d.get("content", ""),
                    word_count=d.get("word_count", 0),
                    round=self.synthesis_round,
                )
                db.add(draft)
            # Update session status
            sess = db.get(_Session, self.session_id)
            if sess:
                sess.status = "highlighting"
            db.commit()

    async def handle_highlight(self, msg: DraftHighlight) -> None:
        """Handle highlight from user across drafts."""
        if self.state != "highlighting":
            await self.send(ErrorMessage(message="Not in highlighting state"))
            return

        # Extract highlighted text from draft content
        draft = (
            self.drafts[msg.draft_index] if msg.draft_index < len(self.drafts) else None
        )
        text = ""
        if draft:
            content = draft.get("content", "")
            text = content[msg.start : msg.end]

        highlight_data = {
            "draft_index": msg.draft_index,
            "start": msg.start,
            "end": msg.end,
            "text": text,
            "sentiment": msg.sentiment,
            "label": msg.label or "",
            "note": msg.note,
        }
        self.highlights.append(highlight_data)

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
                    text=text,
                    sentiment=msg.sentiment,
                    label=msg.label or "",
                    note=msg.note,
                )
                db.add(highlight)
                db.commit()

    async def handle_highlight_update(self, msg: HighlightUpdate) -> None:
        """Update the label on an existing highlight."""
        if self.state != "highlighting":
            await self.send(ErrorMessage(message="Not in highlighting state"))
            return

        # Find highlights for this draft
        draft_hl = [
            (i, h)
            for i, h in enumerate(self.highlights)
            if h["draft_index"] == msg.draft_index
        ]
        if msg.highlight_index >= len(draft_hl):
            await self.send(ErrorMessage(message="Highlight not found"))
            return

        global_idx = draft_hl[msg.highlight_index][0]
        self.highlights[global_idx]["label"] = msg.label

        # Update in DB
        if self.session_id:
            from sqlmodel import select

            from proof_editor.db import get_session
            from proof_editor.models.highlight import Highlight

            with get_session() as db:
                stmt = (
                    select(Highlight)
                    .where(Highlight.session_id == self.session_id)
                    .where(Highlight.draft_index == msg.draft_index)
                    .order_by(Highlight.id)
                )
                results = db.exec(stmt).all()
                if msg.highlight_index < len(results):
                    results[msg.highlight_index].label = msg.label
                    db.commit()

    async def handle_highlight_remove(self, msg: HighlightRemove) -> None:
        """Remove a highlight."""
        if self.state != "highlighting":
            await self.send(ErrorMessage(message="Not in highlighting state"))
            return

        # Find highlights for this draft
        draft_hl = [
            (i, h)
            for i, h in enumerate(self.highlights)
            if h["draft_index"] == msg.draft_index
        ]
        if msg.highlight_index >= len(draft_hl):
            await self.send(ErrorMessage(message="Highlight not found"))
            return

        global_idx = draft_hl[msg.highlight_index][0]
        self.highlights.pop(global_idx)

        # Remove from DB
        if self.session_id:
            from sqlmodel import select

            from proof_editor.db import get_session
            from proof_editor.models.highlight import Highlight

            with get_session() as db:
                stmt = (
                    select(Highlight)
                    .where(Highlight.session_id == self.session_id)
                    .where(Highlight.draft_index == msg.draft_index)
                    .order_by(Highlight.id)
                )
                results = db.exec(stmt).all()
                if msg.highlight_index < len(results):
                    db.delete(results[msg.highlight_index])
                    db.commit()

    async def handle_draft_edit(self, draft_index: int, content: str) -> None:
        """Handle user manually editing draft content."""
        if self.state != "highlighting":
            return

        if draft_index < len(self.drafts):
            self.drafts[draft_index]["content"] = content
            self.drafts[draft_index]["word_count"] = len(content.split())

    async def handle_synthesize(self, msg: DraftSynthesize) -> None:
        """Synthesize 3 new drafts from highlight feedback."""
        if self.state != "highlighting":
            await self.send(ErrorMessage(message="Not in highlighting state"))
            return

        if not self.highlights:
            await self.send(
                ErrorMessage(message="Add some highlights before synthesizing")
            )
            return

        from proof_editor.drafting.synthesizer import DraftSynthesizer
        from proof_editor.examples.loader import (
            format_examples_for_prompt,
            load_examples,
        )

        self.state = "drafting"
        self.synthesis_round += 1

        await self.send(
            StatusMessage(message=f"Synthesizing round {self.synthesis_round}...")
        )

        examples = load_examples()
        examples_context = format_examples_for_prompt(examples)

        synthesizer = DraftSynthesizer(
            task_type=self.task_type,
            topic=self.topic,
            interview_summary=self.interview_summary,
            key_material=self.key_material,
            drafts=self.drafts,
            highlights=self.highlights,
            websocket=self.ws,
            round_num=self.synthesis_round,
            examples_context=examples_context,
        )

        new_drafts = await synthesizer.synthesize()

        # Store previous highlights, then reset for new round
        self.drafts = new_drafts
        self.highlights = []
        self._save_drafts()
        self.state = "highlighting"

    async def handle_resume(self, session_id: int) -> None:
        """Hydrate orchestrator state from a persisted session."""
        import json as _json

        from sqlmodel import select

        from proof_editor.db import get_session as _get_db
        from proof_editor.models.draft import Draft
        from proof_editor.models.highlight import Highlight
        from proof_editor.models.session import Session as _Session

        with _get_db() as db:
            sess = db.get(_Session, session_id)
            if not sess:
                await self.send(ErrorMessage(message="Session not found"))
                return

            self.session_id = sess.id
            self.task_type = sess.task_type
            self.topic = sess.topic
            self.interview_summary = sess.interview_summary or ""
            self.key_material = (
                _json.loads(sess.key_material) if sess.key_material else []
            )

            # Load latest-round drafts
            max_round_stmt = (
                select(Draft.round)
                .where(Draft.session_id == session_id)
                .order_by(Draft.round.desc())  # type: ignore[union-attr]
                .limit(1)
            )
            max_round_result = db.exec(max_round_stmt).first()
            max_round = max_round_result if max_round_result is not None else 0
            self.synthesis_round = max_round

            draft_stmt = (
                select(Draft)
                .where(Draft.session_id == session_id)
                .where(Draft.round == max_round)
                .order_by(Draft.draft_index)
            )
            db_drafts = db.exec(draft_stmt).all()
            self.drafts = [
                {
                    "title": d.title,
                    "angle": d.angle,
                    "content": d.content,
                    "word_count": d.word_count,
                }
                for d in db_drafts
            ]

            # Load highlights
            hl_stmt = (
                select(Highlight)
                .where(Highlight.session_id == session_id)
                .order_by(Highlight.id)
            )
            db_highlights = db.exec(hl_stmt).all()
            self.highlights = [
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
            ]

        self.state = "highlighting"
        logger.info(
            "Resumed session %d: %d drafts, %d highlights, round %d",
            session_id,
            len(self.drafts),
            len(self.highlights),
            self.synthesis_round,
        )
