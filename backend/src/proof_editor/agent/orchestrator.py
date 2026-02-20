"""Orchestrator — manages the writing partner session state machine.

States: task_select → interview → drafting → highlighting → focused
"""

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

from proof_editor.db import db_session
from proof_editor.ws_types import (
    DraftHighlight,
    DraftSynthesize,
    ErrorMessage,
    FocusChat,
    FocusEnter,
    FocusFeedbackMsg,
    HighlightRemove,
    HighlightUpdate,
    InterviewAnswer,
    StatusMessage,
    TaskSelect,
)

logger = logging.getLogger(__name__)


class Orchestrator:
    """Routes WebSocket messages to the appropriate handler based on state."""

    def __init__(self, websocket: WebSocket, user_id: int) -> None:
        self.ws = websocket
        self.user_id = user_id
        self.state = "idle"  # idle, interview, outline, drafting, highlighting, focused
        self.session_id: int | None = None
        self.task_type: str = ""
        self.topic: str = ""
        self.style_id: int | None = None
        self.conversation_history: list[dict[str, Any]] = []
        self.drafts: list[dict[str, Any]] = []
        self.highlights: list[dict[str, Any]] = []
        self.interview_summary: str = ""
        self.key_material: list[str] = []
        self.synthesis_round: int = 0
        self._interview_msg_counter: int = 0
        self._active_tasks: list[asyncio.Task[Any]] = []

        # These get initialized lazily to avoid import-time LLM setup
        self._interviewer: Any = None
        self._generator: Any = None
        self._focus_handler: Any = None

    async def send(self, msg: Any) -> None:
        """Send a typed message over WebSocket."""
        await self.ws.send_text(msg.model_dump_json())

    async def handle_cancel(self) -> None:
        """Cancel any in-flight LLM tasks and reset to idle."""
        cancelled = len(self._active_tasks)
        for task in self._active_tasks:
            task.cancel()
        self._active_tasks = []
        self.state = "idle"
        logger.info("Session cancelled, %d tasks aborted", cancelled)

    def _save_interview_message(
        self,
        role: str,
        content: str,
        *,
        thought_json: str | None = None,
        search_json: str | None = None,
        ready_json: str | None = None,
    ) -> None:
        """Persist an interview message to the database."""
        if not self.session_id:
            return

        from proof_editor.models.interview_message import InterviewMessage

        with db_session() as db:
            msg = InterviewMessage(
                session_id=self.session_id,
                role=role,
                content=content,
                thought_json=thought_json,
                search_json=search_json,
                ready_json=ready_json,
                ordering=self._interview_msg_counter,
            )
            db.add(msg)
            db.commit()

        self._interview_msg_counter += 1

    async def handle_task_select(self, msg: TaskSelect) -> None:
        """Handle task selection — create session and start interview."""
        logger.info("task.select: %s / %s", msg.task_type, msg.topic)
        from proof_editor.agent.interviewer import Interviewer
        from proof_editor.agent.search import create_search_provider
        from proof_editor.models.session import Session

        self.task_type = msg.task_type
        self.topic = msg.topic
        self.style_id = msg.style_id
        self.conversation_history = []
        self.drafts = []
        self.highlights = []
        self.synthesis_round = 0

        # Create DB session
        with db_session() as db:
            session = Session(
                task_type=msg.task_type,
                topic=msg.topic,
                status="interview",
                user_id=self.user_id,
                style_id=self.style_id,
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            self.session_id = session.id

        # Persist last-used style for pre-selection on next session
        if self.style_id is not None:
            from proof_editor.learning import save_preference

            save_preference(self.user_id, "user:last_style_id", str(self.style_id))

        self.state = "interview"
        self._interview_msg_counter = 0
        search_provider = create_search_provider()
        self._interviewer = Interviewer(
            task_type=self.task_type,
            topic=self.topic,
            websocket=self.ws,
            search_provider=search_provider,
            on_message=self._save_interview_message,
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

        # Save user's answer before processing
        self._save_interview_message("user", msg.answer)

        result = await self._interviewer.process_answer(msg.answer)

        if result.get("ready_to_draft"):
            self.interview_summary = result.get("summary", "")
            self.key_material = result.get("key_material", [])
            await self._start_outline()

    async def _start_outline(self) -> None:
        """Transition to outline state — generate structural nodes for user review."""
        from proof_editor.learning.outline_generator import generate_outline
        from proof_editor.ws_types import OutlineNodeData, OutlineNodesMessage

        self.state = "outline"

        # Pull structural signature from voice profile if available
        structural_signature = ""
        if self.style_id:
            from proof_editor.learning import load_voice_profile

            profile = load_voice_profile(self.user_id, self.style_id)
            if profile:
                structural_signature = profile.get("structural_signature", "")

        await self.send(StatusMessage(message="Building your outline..."))

        nodes = await generate_outline(
            task_type=self.task_type,
            topic=self.topic,
            interview_summary=self.interview_summary,
            key_material=self.key_material,
            structural_signature=structural_signature,
        )

        await self.send(
            OutlineNodesMessage(nodes=[OutlineNodeData(**n) for n in nodes])
        )

    async def handle_outline_confirm(self, msg: Any) -> None:
        """User confirmed (possibly reordered) outline — proceed to drafting."""
        if self.state != "outline":
            await self.send(ErrorMessage(message="Not in outline state"))
            return

        from proof_editor.ws_types import OutlineConfirm

        confirmed: OutlineConfirm = msg
        outline_dicts = [n.model_dump() for n in confirmed.nodes]
        self.state = "drafting"
        await self._start_drafting(outline=outline_dicts)

    async def handle_outline_skip(self) -> None:
        """User skipped the outline step — draft immediately with no structure."""
        if self.state != "outline":
            await self.send(ErrorMessage(message="Not in outline state"))
            return

        self.state = "drafting"
        await self._start_drafting()

    def _load_examples_context(self) -> str:
        """Load writing style samples or fall back to static inspo examples."""
        if self.style_id:
            from sqlmodel import select

            from proof_editor.learning import format_samples_for_prompt
            from proof_editor.models.style import StyleSample

            with db_session() as db:
                samples = db.exec(
                    select(StyleSample).where(StyleSample.style_id == self.style_id)
                ).all()

            ctx = format_samples_for_prompt(samples)
            if ctx:
                # Prepend voice profile summary if one has been analyzed
                from proof_editor.learning import (
                    format_voice_profile_for_prompt,
                    load_voice_profile,
                )

                profile = load_voice_profile(self.user_id, self.style_id)
                if profile:
                    ctx = format_voice_profile_for_prompt(profile) + "\n\n" + ctx
                return ctx

        from proof_editor.examples.loader import (
            format_examples_for_prompt,
            load_examples,
        )

        return format_examples_for_prompt(load_examples())

    async def _start_drafting(
        self, outline: list[dict[str, Any]] | None = None
    ) -> None:
        """Transition to drafting — generate 3 concurrent drafts."""
        import json as _json

        from proof_editor.drafting.generator import DraftGenerator

        # Persist interview summary + key material to session
        if self.session_id:
            from proof_editor.models.session import Session as _Session

            with db_session() as db:
                sess = db.get(_Session, self.session_id)
                if sess:
                    sess.interview_summary = self.interview_summary
                    sess.key_material = _json.dumps(self.key_material)
                    sess.status = "drafting"
                    if outline is not None:
                        sess.outline = _json.dumps(outline)
                    db.commit()

        await self.send(StatusMessage(message="Developing your drafts..."))

        examples_context = self._load_examples_context()

        self._generator = DraftGenerator(
            task_type=self.task_type,
            topic=self.topic,
            interview_summary=self.interview_summary,
            key_material=self.key_material,
            websocket=self.ws,
            examples_context=examples_context,
            outline=outline or [],
        )

        drafts = await self._generator.generate()
        self.drafts = drafts
        self._save_drafts()
        self.state = "highlighting"

    def _save_drafts(self) -> None:
        """Persist current drafts to database."""
        if not self.session_id:
            return

        from proof_editor.models.draft import Draft
        from proof_editor.models.session import Session as _Session

        with db_session() as db:
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
            from proof_editor.models.highlight import Highlight

            with db_session() as db:
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

            from proof_editor.models.highlight import Highlight

            with db_session() as db:
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

            from proof_editor.models.highlight import Highlight

            with db_session() as db:
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

        self.state = "drafting"
        self.synthesis_round += 1

        await self.send(
            StatusMessage(message=f"Synthesizing round {self.synthesis_round}...")
        )

        examples_context = self._load_examples_context()

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

        from sqlmodel import func, select

        from proof_editor.models.draft import Draft
        from proof_editor.models.highlight import Highlight
        from proof_editor.models.interview_message import InterviewMessage
        from proof_editor.models.session import Session as _Session

        with db_session() as db:
            sess = db.get(_Session, session_id)
            if not sess or sess.user_id != self.user_id:
                await self.send(ErrorMessage(message="Session not found"))
                return

            self.session_id = sess.id
            self.task_type = sess.task_type
            self.topic = sess.topic
            self.interview_summary = sess.interview_summary or ""
            self.key_material = (
                _json.loads(sess.key_material) if sess.key_material else []
            )

            # Restore interview message counter
            count_stmt = select(func.count()).where(
                InterviewMessage.session_id == session_id
            )
            self._interview_msg_counter = db.exec(count_stmt).one()

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

    async def handle_focus_enter(self, msg: FocusEnter) -> None:
        """Enter focus editing mode on a specific draft."""
        if self.state not in ("highlighting", "focused"):
            await self.send(ErrorMessage(message="Not in highlighting state"))
            return

        from proof_editor.agent.focus_handler import FocusHandler

        # Cancel old handler if switching drafts
        if self._focus_handler is not None:
            self._focus_handler.cancel()

        # Record which draft the user selected
        if self.session_id:
            from proof_editor.models.session import Session as _Session

            with db_session() as db:
                sess = db.get(_Session, self.session_id)
                if sess:
                    sess.selected_draft_index = msg.draft_index
                    db.commit()

        # Build voice profile context; load style tone for rule suppression
        voice_profile_context = ""
        style_tone: str | None = None
        if self.style_id:
            from proof_editor.learning import (
                format_voice_profile_for_prompt,
                load_voice_profile,
            )
            from proof_editor.learning.feedback_distiller import (
                format_rule_stats_for_prompt,
                load_rule_stats,
            )
            from proof_editor.models.style import WritingStyle

            with db_session() as db:
                ws = db.get(WritingStyle, self.style_id)
                if ws:
                    style_tone = ws.tone

            profile = load_voice_profile(self.user_id, self.style_id)
            if profile:
                voice_profile_context = format_voice_profile_for_prompt(profile)

            rule_stats = load_rule_stats(self.user_id, self.style_id)
            rule_context = format_rule_stats_for_prompt(rule_stats)
            if rule_context:
                voice_profile_context = (
                    voice_profile_context + "\n\n" + rule_context
                    if voice_profile_context
                    else rule_context
                )

        self.state = "focused"
        self._focus_handler = FocusHandler(
            send=self.send,
            session_id=self.session_id,
            drafts=self.drafts,
            interview_summary=self.interview_summary,
            key_material=self.key_material,
            voice_profile_context=voice_profile_context,
            style_tone=style_tone,
        )
        await self._focus_handler.handle_enter(msg)

    async def handle_focus_exit(self) -> None:
        """Exit focus mode, return to highlighting."""
        self.state = "highlighting"
        self._focus_handler = None
        logger.info("Exited focus mode")

        # Fire-and-forget: distill session feedback into rule stats
        if self.style_id and self.session_id:
            from proof_editor.learning.feedback_distiller import (
                distill_session_feedback,
            )

            task = asyncio.get_event_loop().run_in_executor(
                None,
                distill_session_feedback,
                self.user_id,
                self.style_id,
                self.session_id,
            )
            asyncio.ensure_future(task)

    async def handle_focus_feedback(self, msg: FocusFeedbackMsg) -> None:
        """Handle feedback on a suggestion or comment."""
        if self.state != "focused" or not self._focus_handler:
            return
        await self._focus_handler.handle_feedback(msg)

    async def handle_focus_chat(self, msg: FocusChat) -> None:
        """Handle chat message in focus mode."""
        if self.state != "focused" or not self._focus_handler:
            await self.send(ErrorMessage(message="Not in focus mode"))
            return
        await self._focus_handler.handle_chat(msg)

    async def handle_focus_approve_comment(self, msg: Any) -> None:
        """Handle approve comment — ask LLM to apply the editorial suggestion."""
        if self.state != "focused" or not self._focus_handler:
            return
        await self._focus_handler.handle_approve_comment(msg)
