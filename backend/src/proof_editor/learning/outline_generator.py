"""Outline generator — LLM structural node generation from interview material.

Analyzes interview summary and key material to propose a structural skeleton
for the piece. Returns a list of OutlineNodeData objects the user can reorder.
"""

import json
import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)

_OUTLINE_SYSTEM_PROMPT = """\
You are a writing coach helping a writer structure their piece before they draft.

You have the interview material in front of you. Propose a structural outline
as a sequence of nodes. Each node is a building block of the piece — a Hook,
a Story, a Point, Evidence, etc.

Be grounded: each node's description should reference the actual material
from the interview, not generic placeholders.

Use the generate_outline tool. Aim for 5-8 nodes."""

_OUTLINE_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "generate_outline",
            "description": "Propose a structural outline for the piece.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "node_type": {
                                    "type": "string",
                                    "enum": [
                                        "hook",
                                        "context",
                                        "thesis",
                                        "story",
                                        "point",
                                        "evidence",
                                        "complication",
                                        "insight",
                                        "closing",
                                    ],
                                },
                                "description": {
                                    "type": "string",
                                    "description": (
                                        "1-2 sentences describing what this section"
                                        " covers, grounded in the interview material"
                                    ),
                                },
                            },
                            "required": ["node_type", "description"],
                        },
                        "minItems": 4,
                        "maxItems": 10,
                    }
                },
                "required": ["nodes"],
            },
        },
    }
]


async def generate_outline(
    task_type: str,
    topic: str,
    interview_summary: str,
    key_material: list[str],
    structural_signature: str = "",
) -> list[dict[str, str]]:
    """Generate structural outline nodes from interview material.

    Returns a list of dicts with id, node_type, and description.
    Falls back to a minimal default outline on failure.
    """
    from litellm import acompletion

    key_material_str = "\n".join(f"- {item}" for item in key_material)

    user_content = (
        f"Task type: {task_type}\nTopic: {topic}\n\n"
        f"Interview summary:\n{interview_summary}\n\n"
        f"Key material:\n{key_material_str}"
    )

    if structural_signature:
        user_content += f"\n\nThis writer's typical structure: {structural_signature}"

    try:
        response = await acompletion(
            model="anthropic/claude-haiku-4-5-20251001",
            messages=[
                {"role": "system", "content": _OUTLINE_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            tools=_OUTLINE_TOOLS,
            tool_choice={"type": "function", "function": {"name": "generate_outline"}},
        )
    except Exception as e:
        logger.error("Outline generation LLM call failed: %s", e)
        return _default_outline(task_type)

    msg = response.choices[0].message
    if not msg.tool_calls:
        logger.warning("Outline generation: no tool call returned")
        return _default_outline(task_type)

    tc = msg.tool_calls[0]
    try:
        args = json.loads(tc.function.arguments)
        nodes = args.get("nodes", [])
        return [
            {
                "id": str(uuid.uuid4()),
                "node_type": n["node_type"],
                "description": n["description"],
            }
            for n in nodes
            if "node_type" in n and "description" in n
        ]
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        logger.warning("Outline generation: failed to parse tool args: %s", e)
        return _default_outline(task_type)


def _default_outline(task_type: str) -> list[dict[str, str]]:
    """Minimal fallback outline when LLM call fails."""
    defaults = {
        "essay": [
            ("hook", "Open with a moment or observation that sparked this piece"),
            ("context", "Zoom out to the broader significance"),
            ("thesis", "State the core argument"),
            ("point", "First supporting point with evidence"),
            ("complication", "Complicate or challenge the thesis"),
            ("closing", "Reframe with a takeaway"),
        ],
        "newsletter": [
            ("hook", "Lead with a surprising insight or personal moment"),
            ("context", "Why this matters now"),
            ("story", "The story or case study"),
            ("insight", "The lesson extracted"),
            ("closing", "What the reader can do with this"),
        ],
    }
    nodes = defaults.get(task_type, defaults["essay"])
    return [
        {"id": str(uuid.uuid4()), "node_type": nt, "description": desc}
        for nt, desc in nodes
    ]
