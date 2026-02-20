"""Pattern extractor — LLM 'What do you notice?' analysis on writing samples.

Analyzes a writer's StyleSamples to extract structured voice profile:
voice descriptors, structural signature, red flags, and strengths.
Stores results in the Preference table under namespaced keys.
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_EXTRACTOR_SYSTEM_PROMPT = """\
You are a writing coach studying a writer's body of work.
Your job is to identify the patterns, signature moves, and weaknesses
that characterize their writing.

Analyze the provided samples carefully, then use the extract_voice_profile
tool to report what you notice. Be specific and concrete — not generic advice,
but patterns that are *distinctly true* of this particular writer."""

_EXTRACTOR_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "extract_voice_profile",
            "description": "Report what you notice about this writer's patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "voice_descriptors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "3-5 short phrases describing the writer's distinctive voice"  # noqa: E501
                            " (e.g., 'Opens with a moment of friction',"
                            " 'Zooms out to cultural context before the thesis')"
                        ),
                    },
                    "structural_signature": {
                        "type": "string",
                        "description": (
                            "1-2 sentences on how this writer structures"
                            " a piece from opening to close"
                        ),
                    },
                    "red_flags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "2-4 specific recurring weaknesses or habits to watch "
                            "(e.g., 'Hedges conclusions with maybe/perhaps', "
                            "'Introductions meander before reaching the point')"
                        ),
                    },
                    "strengths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "2-3 specific patterns that consistently work well "
                            "and should be reinforced"
                        ),
                    },
                },
                "required": [
                    "voice_descriptors",
                    "structural_signature",
                    "red_flags",
                    "strengths",
                ],
            },
        },
    }
]


async def extract_patterns(samples: list) -> dict | None:  # list[StyleSample]
    """Run LLM analysis over StyleSamples and return a voice profile dict.

    Returns None if the LLM call fails or returns no tool call.
    """
    if not samples:
        logger.warning("extract_patterns: no samples provided")
        return None

    from litellm import acompletion

    # Build user message with all samples
    sample_blocks: list[str] = []
    for s in samples:
        title = s.title or "Untitled"
        content = s.content[:3000]  # cap per sample to control token usage
        sample_blocks.append(f"--- {title} ---\n{content}")

    user_content = (
        "Here are the writer's samples. Extract their voice profile.\n\n"
        + "\n\n".join(sample_blocks)
    )

    try:
        response = await acompletion(
            model="anthropic/claude-haiku-4-5-20251001",
            messages=[
                {"role": "system", "content": _EXTRACTOR_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            tools=_EXTRACTOR_TOOLS,
            tool_choice={
                "type": "function",
                "function": {"name": "extract_voice_profile"},
            },
        )
    except Exception as e:
        logger.error("Pattern extraction LLM call failed: %s", e)
        return None

    msg = response.choices[0].message
    if not msg.tool_calls:
        logger.warning("Pattern extraction: no tool call returned")
        return None

    tc = msg.tool_calls[0]
    if tc.function.name != "extract_voice_profile":
        return None

    try:
        return json.loads(tc.function.arguments)
    except (json.JSONDecodeError, AttributeError) as e:
        logger.warning("Pattern extraction: failed to parse tool args: %s", e)
        return None
