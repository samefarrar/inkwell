"""FocusHandler — manages the focus editing session.

Runs style engine analysis, kicks off editorial comments,
handles feedback persistence, and delegates chat to focus_agent.
"""

import asyncio
import logging
import re
from html.parser import HTMLParser
from typing import Any

from proof_editor.db import db_session
from proof_editor.ws_types import (
    ErrorMessage,
    FocusChat,
    FocusCommentMsg,
    FocusEnter,
    FocusFeedbackMsg,
    FocusSuggestion,
)

logger = logging.getLogger(__name__)

MAX_DRAFT_CHARS = 50_000


class _HTMLStripper(HTMLParser):
    """Extract text content from HTML, discarding all tags."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


class FocusHandler:
    """Handles all focus mode operations for a session."""

    def __init__(
        self,
        send: Any,
        session_id: int | None,
        drafts: list[dict[str, Any]],
        interview_summary: str,
        key_material: list[str],
    ) -> None:
        self.send = send
        self.session_id = session_id
        self.drafts = drafts
        self.interview_summary = interview_summary
        self.key_material = key_material
        self.draft_index: int = -1
        self.draft_content: str = ""
        self._focus_agent: Any = None
        self._chat_lock = asyncio.Lock()
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    async def handle_enter(self, msg: FocusEnter) -> None:
        """Enter focus mode on a specific draft — run analysis."""
        self.draft_index = msg.draft_index
        if msg.draft_index < len(self.drafts):
            self.draft_content = self.drafts[msg.draft_index].get("content", "")
        else:
            await self.send(ErrorMessage(message="Invalid draft index"))
            return

        # Strip HTML for text analysis and enforce length limit
        plain_text = self._strip_html(self.draft_content)[:MAX_DRAFT_CHARS]

        # Run style engine (deterministic, fast)
        await self._run_style_analysis(plain_text)

        # Run editorial comments (LLM, slower)
        await self._run_editorial_analysis(plain_text)

    async def handle_feedback(self, msg: FocusFeedbackMsg) -> None:
        """Persist user feedback on a suggestion or comment."""
        if not self.session_id:
            return

        from proof_editor.models.feedback import Feedback

        accepted = msg.action == "accept"

        with db_session() as db:
            fb = Feedback(
                session_id=self.session_id,
                draft_index=self.draft_index,
                text="",
                accepted=accepted,
                action=msg.action,
                feedback_type=msg.feedback_type,
                rule_id=msg.id,
            )
            db.add(fb)
            db.commit()

    async def handle_chat(self, msg: FocusChat) -> None:
        """Handle chat message from user — delegate to focus agent."""
        if self._chat_lock.locked():
            return  # silently ignore while processing

        async with self._chat_lock:
            from proof_editor.agent.focus_agent import FocusAgent

            if not self._focus_agent:
                self._focus_agent = FocusAgent(
                    send=self.send,
                    draft_content=self.draft_content,
                    interview_summary=self.interview_summary,
                    key_material=self.key_material,
                )

            await self._focus_agent.handle_message(msg.message)

    async def _run_style_analysis(self, text: str) -> None:
        """Run the deterministic style engine and send suggestions."""
        from proof_editor.style.engine import analyze

        violations = analyze(text)
        for v in violations:
            if self._cancelled:
                return
            await self.send(
                FocusSuggestion(
                    id=v.id,
                    quote=v.quote,
                    start=v.start,
                    end=v.end,
                    replacement=v.replacement,
                    explanation=v.explanation,
                    rule_id=v.rule_id,
                )
            )

    async def _run_editorial_analysis(self, text: str) -> None:
        """Run the LLM editorial comment pass."""
        if self._cancelled:
            return
        try:
            from proof_editor.style.editorial import generate_comments

            comments = await generate_comments(
                text=text,
                interview_context=self.interview_summary,
            )
            for i, c in enumerate(comments):
                if self._cancelled:
                    return
                is_last = i == len(comments) - 1
                await self.send(
                    FocusCommentMsg(
                        id=c.id,
                        quote=c.quote,
                        start=c.start,
                        end=c.end,
                        comment=c.comment,
                        done=is_last,
                    )
                )
            # If no comments were generated, still signal done
            if not comments:
                await self.send(
                    FocusCommentMsg(
                        id="",
                        quote="",
                        start=0,
                        end=0,
                        comment="",
                        done=True,
                    )
                )
        except Exception as e:
            logger.error("Editorial analysis failed: %s", e, exc_info=True)
            await self.send(
                FocusCommentMsg(
                    id="",
                    quote="",
                    start=0,
                    end=0,
                    comment="Editorial analysis is temporarily unavailable.",
                    done=True,
                )
            )

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip HTML tags using a proper parser, not regex."""
        stripper = _HTMLStripper()
        stripper.feed(html)
        return re.sub(r"\s+", " ", stripper.get_text()).strip()
