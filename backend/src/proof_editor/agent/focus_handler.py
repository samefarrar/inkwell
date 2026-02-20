"""FocusHandler — manages the focus editing session.

Runs style engine analysis, kicks off editorial comments,
handles feedback persistence, and delegates chat to focus_agent.
"""

import asyncio
import json
import logging
import re
from html.parser import HTMLParser
from typing import Any

from proof_editor.db import db_session
from proof_editor.ws_types import (
    ErrorMessage,
    FocusApproveComment,
    FocusChat,
    FocusCommentMsg,
    FocusEditApplied,
    FocusEnter,
    FocusFeedbackMsg,
    FocusSuggestion,
)

logger = logging.getLogger(__name__)

MAX_DRAFT_CHARS = 50_000

_APPROVE_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "apply_edit",
            "description": "Apply the editorial change to the draft text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "old_text": {
                        "type": "string",
                        "description": (
                            "Exact passage to replace (copy verbatim from the draft)"
                        ),
                    },
                    "new_text": {
                        "type": "string",
                        "description": (
                            "Improved replacement text implementing the suggestion"
                        ),
                    },
                },
                "required": ["old_text", "new_text"],
            },
        },
    }
]


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
        # Store comments by ID so we can look them up on approve
        self._comment_store: dict[str, FocusCommentMsg] = {}

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

    async def handle_approve_comment(self, msg: FocusApproveComment) -> None:
        """User approved an editorial comment — ask LLM to apply it."""
        comment = self._comment_store.get(msg.id)
        if not comment:
            logger.warning("approve_comment: unknown comment id %s", msg.id)
            return

        current_text = self._strip_html(msg.current_content)[:MAX_DRAFT_CHARS]

        try:
            from litellm import acompletion

            prompt = (
                f"You are an editor. The writer has approved this editorial comment "
                f"and wants you to apply it to their draft.\n\n"
                f"Editorial comment: {comment.comment}\n\n"
                f'The comment refers to this passage:\n"{comment.quote}"\n\n'
                f"Current draft:\n{current_text}\n\n"
                f"Call apply_edit with:\n"
                f"- old_text: the exact passage to replace (use the quoted passage "
                f"or nearby context if needed)\n"
                f"- new_text: the improved version that implements the suggestion\n\n"
                f"Keep changes minimal and targeted."
            )

            response = await acompletion(
                model="anthropic/claude-sonnet-4-6",
                messages=[{"role": "user", "content": prompt}],
                tools=_APPROVE_TOOLS,
                tool_choice={"type": "function", "function": {"name": "apply_edit"}},
            )

            llm_msg = response.choices[0].message
            if llm_msg.tool_calls:
                tc = llm_msg.tool_calls[0]
                args = json.loads(tc.function.arguments)
                old_text = args.get("old_text", "")
                new_text = args.get("new_text", "")
                if old_text:
                    await self.send(
                        FocusEditApplied(
                            comment_id=msg.id,
                            old_text=old_text,
                            new_text=new_text,
                        )
                    )
        except Exception as e:
            logger.error("approve_comment LLM call failed: %s", e, exc_info=True)

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
                comment_msg = FocusCommentMsg(
                    id=c.id,
                    quote=c.quote,
                    start=c.start,
                    end=c.end,
                    comment=c.comment,
                    done=is_last,
                )
                # Store so we can look up on approve
                self._comment_store[c.id] = comment_msg
                await self.send(comment_msg)
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
