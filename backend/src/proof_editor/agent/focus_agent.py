"""Focus Agent — conversational AI collaborator for draft editing.

Handles chat messages in focus mode. Can respond with text,
suggest edits (which appear as inline suggestions), and search the web.
"""

import json
import logging
import uuid
from typing import Any

from proof_editor.agent.search import SearchResult, create_search_provider
from proof_editor.ws_types import (
    FocusChatResponse,
    FocusSuggestion,
    SearchResultMessage,
)

logger = logging.getLogger(__name__)

MAX_CONTINUATIONS = 5

SYSTEM_PROMPT = """\
You are an editorial collaborator helping improve a draft. You can see the \
current text, interview context, and key material.

Help the writer improve their work by answering questions, suggesting edits, \
and searching the web for supporting information.

You MUST use the provided tools for ALL responses. Do not send plain text.

Tools available:
- `send_response`: Send a text response to the writer
- `suggest_edit`: Suggest a specific text replacement in the draft
- `web_search`: Search the web for information

Always call `send_response` at least once per turn."""

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "send_response",
            "description": "Send a text response to the writer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Your response text",
                    },
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_edit",
            "description": "Suggest a specific text edit in the draft.",
            "parameters": {
                "type": "object",
                "properties": {
                    "quote": {
                        "type": "string",
                        "description": "Exact text to replace in the draft",
                    },
                    "replacement": {
                        "type": "string",
                        "description": "The replacement text",
                    },
                    "explanation": {
                        "type": "string",
                        "description": (
                            "Brief explanation of why this edit improves the draft"
                        ),
                    },
                },
                "required": ["quote", "replacement", "explanation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information to support the draft.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


class FocusAgent:
    """Manages the focus chat conversation."""

    def __init__(
        self,
        send: Any,
        draft_content: str,
        interview_summary: str,
        key_material: list[str],
    ) -> None:
        self.send = send
        self.draft_content = draft_content
        self.interview_summary = interview_summary
        self.key_material = key_material
        self.search_provider = create_search_provider()
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Here is the current draft:\n\n{draft_content}\n\n"
                    f"Interview context: {interview_summary}\n\n"
                    f"Key material: {json.dumps(key_material)}"
                ),
            },
        ]

    async def handle_message(self, user_message: str) -> None:
        """Process a chat message from the user."""
        self.messages.append({"role": "user", "content": user_message})
        await self._call_llm()

    async def _call_llm(self, depth: int = 0) -> None:
        """Call LiteLLM and process tool calls."""
        if depth >= MAX_CONTINUATIONS:
            await self.send(
                FocusChatResponse(
                    content="I reached my search limit. Here's what I found so far.",
                    done=True,
                )
            )
            return

        try:
            from litellm import acompletion

            response = await acompletion(
                model="anthropic/claude-sonnet-4-6",
                messages=self.messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as e:
            logger.error("Focus agent LLM call failed: %s", e, exc_info=True)
            await self.send(
                FocusChatResponse(
                    content="I'm having trouble responding. Please try again.",
                    done=True,
                )
            )
            return

        msg = response.choices[0].message
        self.messages.append(msg.model_dump())

        if msg.tool_calls:
            needs_continuation = False
            has_response = False

            for tc in msg.tool_calls:
                fn = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("Failed to parse tool call arguments: %s", e)
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": f"Error parsing arguments: {e}",
                        }
                    )
                    needs_continuation = True
                    continue

                if fn == "send_response":
                    text = args.get("text", "")
                    await self.send(FocusChatResponse(content=text, done=True))
                    has_response = True
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": "Response sent to user.",
                        }
                    )

                elif fn == "suggest_edit":
                    quote = args.get("quote", "")
                    replacement = args.get("replacement", "")
                    explanation = args.get("explanation", "")

                    start = self.draft_content.find(quote)
                    end = start + len(quote) if start >= 0 else 0
                    if start < 0:
                        logger.warning(
                            "Could not locate quote in draft: %r", quote[:50]
                        )
                        start = 0

                    await self.send(
                        FocusSuggestion(
                            id=str(uuid.uuid4()),
                            quote=quote,
                            start=start,
                            end=end,
                            replacement=replacement,
                            explanation=explanation,
                            rule_id="agent",
                        )
                    )
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": (
                                f"Edit suggestion created for: '{quote[:50]}...'"
                            ),
                        }
                    )
                    needs_continuation = True

                elif fn == "web_search":
                    query = args.get("query", "")
                    results: list[SearchResult] = await self.search_provider.search(
                        query
                    )

                    if results:
                        formatted = "\n\n".join(
                            f"**{r.title}** ({r.url})\n{r.snippet}" for r in results
                        )
                        summary = (
                            f"Found {len(results)} results "
                            f"for '{query}':\n\n{formatted}"
                        )
                    else:
                        summary = f"No results found for '{query}'."

                    await self.send(SearchResultMessage(query=query, summary=summary))
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": summary,
                        }
                    )
                    needs_continuation = True

            # If tools were called but no text response sent, continue for follow-up
            if needs_continuation and not has_response:
                await self._call_llm(depth + 1)
        elif msg.content:
            # Fallback: if LLM sent plain text instead of using tools
            await self.send(FocusChatResponse(content=msg.content, done=True))
