"""Editorial comment generator — LLM-powered structural feedback.

Uses LiteLLM tool calls to generate 3-5 editorial comments about
structure, clarity, voice, and impact. Each comment is anchored to
a specific quote in the draft with character offsets.
"""

import json
import logging
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EditorialComment:
    id: str
    quote: str
    start: int
    end: int
    comment: str


_BASE_SYSTEM_PROMPT = """\
You are a senior editor reviewing a draft.{voice_section} Leave 3-5 editorial \
comments focused on structure, clarity, voice, and impact — NOT grammar or spelling.

Each comment should be anchored to a specific quote from the draft. \
Pick the most important improvements the writer should consider.

You MUST use the `leave_comment` tool for each comment. Do not respond \
with plain text — only use the tool."""


def _build_system_prompt(voice_profile_context: str) -> str:
    if voice_profile_context:
        voice_section = (
            f"\n\nYou know this writer's style well:\n{voice_profile_context}\n\n"
            "Tailor your feedback to their specific voice and known weaknesses."
        )
    else:
        voice_section = ""
    return _BASE_SYSTEM_PROMPT.format(voice_section=voice_section)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "leave_comment",
            "description": "Leave an editorial comment anchored to a specific quote.",
            "parameters": {
                "type": "object",
                "properties": {
                    "quote": {
                        "type": "string",
                        "description": (
                            "Exact text from the draft to "
                            "anchor this comment to (10-50 words)"
                        ),
                    },
                    "comment": {
                        "type": "string",
                        "description": "Your editorial feedback (1-3 sentences)",
                    },
                },
                "required": ["quote", "comment"],
            },
        },
    },
]


def _find_quote_position(text: str, quote: str) -> tuple[int, int]:
    """Find the start and end position of a quote in the text."""
    idx = text.find(quote)
    if idx >= 0:
        return idx, idx + len(quote)
    # Try case-insensitive
    lower_text = text.lower()
    lower_quote = quote.lower()
    idx = lower_text.find(lower_quote)
    if idx >= 0:
        return idx, idx + len(quote)
    logger.warning("Could not locate quote in text: %r", quote[:80])
    return 0, 0


async def generate_comments(
    text: str,
    interview_context: str = "",
    voice_profile_context: str = "",
) -> list[EditorialComment]:
    """Generate editorial comments for the given text.

    Returns a list of EditorialComment with quote anchors and positions.
    """
    from litellm import acompletion

    system_prompt = _build_system_prompt(voice_profile_context)

    user_content = f"Here is the draft to review:\n\n{text}"
    if interview_context:
        user_content += f"\n\nContext from the interview:\n{interview_context}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    try:
        response = await acompletion(
            model="anthropic/claude-sonnet-4-6",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
    except Exception as e:
        logger.error("Editorial LLM call failed: %s", e)
        return []

    comments: list[EditorialComment] = []
    msg = response.choices[0].message

    if msg.tool_calls:
        for tc in msg.tool_calls:
            if tc.function.name == "leave_comment":
                try:
                    args = json.loads(tc.function.arguments)
                    quote = args.get("quote", "")
                    comment_text = args.get("comment", "")
                    start, end = _find_quote_position(text, quote)
                    comments.append(
                        EditorialComment(
                            id=str(uuid.uuid4()),
                            quote=quote,
                            start=start,
                            end=end,
                            comment=comment_text,
                        )
                    )
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning("Failed to parse comment tool call: %s", e)

    return comments
