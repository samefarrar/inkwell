"""Interviewer — conversational agent that extracts stories and insights.

Asks ONE targeted question at a time, shows reasoning via thought blocks,
and assesses sufficiency after each answer.
"""

import json
import logging
from typing import Any

from fastapi import WebSocket

from proof_editor.examples.loader import (
    format_examples_for_prompt,
    load_examples,
)
from proof_editor.ws_types import (
    InterviewQuestion,
    ReadyToDraft,
    StatusMessage,
    ThoughtMessage,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are an AI writing partner. Your job is to interview the user \
to extract real stories, insights, and experiences for a \
{task_type} about "{topic}".

RULES:
1. Ask ONE question at a time — never dump a list of questions.
2. Ask the single most impactful question to fill the gap.
3. Before each question, assess what you know vs what's missing.
4. After each answer, evaluate whether you have enough material.
5. Typically 2-4 questions are sufficient. Don't over-interview.

You MUST use the provided tools for ALL responses.

For each turn, call tools in this order:
1. ALWAYS call `show_thought` first
2. Then EITHER:
   - Call `ask_question` if you need more material
   - Call `ready_to_draft` if you have enough material

{examples_context}"""

_SHOW_THOUGHT_DESC = (
    "Show your reasoning about what material you have "
    "and what's missing. ALWAYS call this first."
)
_SUFFICIENT_DESC = "Whether you have enough material to write a compelling draft"
_ASK_DESC = "Ask the user a single targeted question to gather writing material."
_CTX_DESC = "Brief context for why you're asking this question"

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "show_thought",
            "description": _SHOW_THOUGHT_DESC,
            "parameters": {
                "type": "object",
                "properties": {
                    "assessment": {
                        "type": "string",
                        "description": "What you know so far",
                    },
                    "missing": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "What info is still missing",
                    },
                    "sufficient": {
                        "type": "boolean",
                        "description": _SUFFICIENT_DESC,
                    },
                },
                "required": ["assessment", "missing", "sufficient"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_question",
            "description": _ASK_DESC,
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question to ask",
                    },
                    "context": {
                        "type": "string",
                        "description": _CTX_DESC,
                    },
                },
                "required": ["question", "context"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ready_to_draft",
            "description": "Signal that you have enough material.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Summary of material gathered",
                    },
                    "key_material": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key stories and details",
                    },
                },
                "required": ["summary", "key_material"],
            },
        },
    },
]


class Interviewer:
    """Manages the interview conversation with the user."""

    def __init__(
        self,
        task_type: str,
        topic: str,
        websocket: WebSocket,
    ) -> None:
        self.task_type = task_type
        self.topic = topic
        self.ws = websocket
        self.messages: list[dict[str, Any]] = []

        examples = load_examples()
        examples_context = format_examples_for_prompt(examples)

        self.system_prompt = SYSTEM_PROMPT.format(
            task_type=task_type,
            topic=topic,
            examples_context=examples_context,
        )

    async def start(self) -> None:
        """Begin the interview — send the first question."""
        self.messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (f"I want to write a {self.task_type} about: {self.topic}"),
            },
        ]
        await self._call_llm()

    async def process_answer(self, answer: str) -> dict[str, Any]:
        """Process user's answer and continue the interview."""
        self.messages.append({"role": "user", "content": answer})
        return await self._call_llm()

    async def _call_llm(self) -> dict[str, Any]:
        """Call LiteLLM and process tool calls."""
        try:
            from litellm import acompletion

            response = await acompletion(
                model="anthropic/claude-sonnet-4-20250514",
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as e:
            logger.error("LLM call failed: %s", e)
            await self.ws.send_text(
                StatusMessage(
                    message=(f"LLM error: {e}. Set ANTHROPIC_API_KEY to enable.")
                ).model_dump_json()
            )
            return {}

        result: dict[str, Any] = {}
        msg = response.choices[0].message
        self.messages.append(msg.model_dump())

        if msg.tool_calls:
            for tc in msg.tool_calls:
                fn = tc.function.name
                args = json.loads(tc.function.arguments)

                if fn == "show_thought":
                    await self._handle_thought(tc.id, args)
                elif fn == "ask_question":
                    await self._handle_question(tc.id, args)
                elif fn == "ready_to_draft":
                    result = await self._handle_ready(tc.id, args)

            # Continue if only thought was shown
            names = [tc.function.name for tc in msg.tool_calls]
            if (
                "show_thought" in names
                and "ask_question" not in names
                and "ready_to_draft" not in names
            ):
                return await self._call_llm()

        return result

    async def _handle_thought(self, tool_id: str, args: dict[str, Any]) -> None:
        await self.ws.send_text(
            ThoughtMessage(
                assessment=args["assessment"],
                missing=args.get("missing", []),
                sufficient=args.get("sufficient", False),
            ).model_dump_json()
        )
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_id,
                "content": "Thought displayed to user.",
            }
        )

    async def _handle_question(self, tool_id: str, args: dict[str, Any]) -> None:
        await self.ws.send_text(
            InterviewQuestion(
                question=args["question"],
                context=args.get("context", ""),
            ).model_dump_json()
        )
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_id,
                "content": "Question shown. Waiting for answer.",
            }
        )

    async def _handle_ready(self, tool_id: str, args: dict[str, Any]) -> dict[str, Any]:
        summary = args.get("summary", "")
        key_material = args.get("key_material", [])

        await self.ws.send_text(
            ReadyToDraft(
                summary=summary,
                key_material=key_material,
            ).model_dump_json()
        )
        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_id,
                "content": "Transitioning to drafting.",
            }
        )
        return {
            "ready_to_draft": True,
            "summary": summary,
            "key_material": key_material,
        }
