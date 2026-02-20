"""Draft synthesizer — generates 3 refined drafts from highlight feedback.

Analyzes which angles earned likes vs flags, keeps liked angles,
replaces heavily-flagged angles, and generates new drafts with
all highlights embedded as semantic XML tags.
"""

import asyncio
import logging
import re
from typing import Any

from fastapi import WebSocket

from proof_editor.drafting.prompts import ANGLE_INSTRUCTIONS, get_angles
from proof_editor.ws_types import DraftChunk, DraftComplete, DraftStart

logger = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def annotate_draft_with_highlights(
    content: str,
    highlights: list[dict[str, Any]],
) -> str:
    """Wrap highlighted spans in semantic XML tags.

    Tag mapping:
    - like + no label  → <good>text</good>
    - flag + no label  → <bad>text</bad>
    - like + label     → <good_label>text</good_label>
    - flag + label     → <label>text</label>
    """
    if not highlights:
        return content

    sorted_hl = sorted(highlights, key=lambda h: h["start"])
    parts: list[str] = []
    pos = 0

    for hl in sorted_hl:
        start = max(hl["start"], pos)
        if start > pos:
            parts.append(content[pos:start])

        end = hl["end"]
        if end <= start:
            continue

        text = content[start:end]
        sentiment = hl.get("sentiment", "like")
        label = hl.get("label", "")

        if label:
            if sentiment == "like":
                tag = f"good_{label}"
            else:
                tag = label
        else:
            tag = "good" if sentiment == "like" else "bad"

        parts.append(f"<{tag}>{text}</{tag}>")
        pos = end

    if pos < len(content):
        parts.append(content[pos:])

    return "".join(parts)


def score_angles(
    drafts: list[dict[str, Any]],
    highlights: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Score each draft angle by likes vs flags.

    Returns list of {index, angle, likes, flags, score} sorted by index.
    """
    scores: list[dict[str, Any]] = []
    for i, draft in enumerate(drafts):
        draft_hl = [h for h in highlights if h["draft_index"] == i]
        likes = sum(1 for h in draft_hl if h.get("sentiment") == "like")
        flags = sum(1 for h in draft_hl if h.get("sentiment") == "flag")
        scores.append(
            {
                "index": i,
                "angle": draft.get("angle", f"Draft {i + 1}"),
                "likes": likes,
                "flags": flags,
                "score": likes - flags,
            }
        )
    return scores


def choose_angles(
    task_type: str,
    drafts: list[dict[str, Any]],
    highlights: list[dict[str, Any]],
) -> list[str]:
    """Choose 3 angles for synthesis: keep liked, replace flagged.

    Angles with more likes than flags are kept. Angles with more flags
    are replaced with new angles from the task type's angle pool.
    """
    scores = score_angles(drafts, highlights)
    all_angles = get_angles(task_type)
    current_angles = [d.get("angle", "") for d in drafts]

    # Angles to keep (score >= 0, i.e. at least as many likes as flags)
    kept: list[str] = []
    to_replace: list[int] = []
    for s in scores:
        if s["score"] >= 0:
            kept.append(s["angle"])
        else:
            to_replace.append(s["index"])

    # If nothing to replace, keep all original angles
    if not to_replace:
        return current_angles

    # Find replacement angles not already in use
    used = set(kept)
    available = [a for a in all_angles if a not in used]

    # If we run out of available angles, cycle through defaults
    defaults = ["Fresh-perspective", "Revised-approach", "Alternative-angle"]
    result = list(current_angles)
    replacement_idx = 0

    for idx in to_replace:
        if available:
            result[idx] = available.pop(0)
        elif replacement_idx < len(defaults):
            result[idx] = defaults[replacement_idx]
            replacement_idx += 1
        else:
            # Last resort: keep the original angle
            pass

    return result


SYNTHESIS_SYSTEM_PROMPT = """\
You are an expert writer refining a {task_type} about "{topic}" \
using the {angle} angle.

This is round {round} of synthesis. The reader highlighted parts \
of a previous draft to guide this revision.

PREVIOUS DRAFTS WITH READER FEEDBACK:
{annotated_drafts}

INTERVIEW MATERIAL:
{interview_summary}

KEY DETAILS:
{key_material}

{examples_context}

HIGHLIGHT LEGEND:
- <good>text</good> — Reader loved this. MUST keep or improve it.
- <bad>text</bad> — Reader flagged this. Rewrite or omit entirely.
- Custom tags like <too_formal> or <good_insightful> carry the \
label as guidance for what to fix or why it was liked.
- Unlabeled text is background — use freely.

INSTRUCTIONS:
- Write in the {angle} style: {angle_instruction}
- Target 300-500 words
- Incorporate ALL <good> passages (keep the essence, improve if possible)
- Fix or omit ALL <bad> passages
- Follow the Every Write Style Guide:
  * Oxford comma always
  * Em dash (—) with no spaces, max twice per paragraph
  * Active voice preferred
  * Cut filler words: "actually", "very", "just", "really"
- Do not use HTML tags or formatting. Output plain text only.
- Make it better than the previous round
- Include a title

Write the draft now. Output the title on the first line, \
then a blank line, then the body."""


class DraftSynthesizer:
    """Generates 3 refined drafts from highlighted feedback."""

    def __init__(
        self,
        task_type: str,
        topic: str,
        interview_summary: str,
        key_material: list[str],
        drafts: list[dict[str, Any]],
        highlights: list[dict[str, Any]],
        websocket: WebSocket,
        round_num: int = 1,
        examples_context: str = "",
    ) -> None:
        self.task_type = task_type
        self.topic = topic
        self.interview_summary = interview_summary
        self.key_material = key_material
        self.drafts = drafts
        self.highlights = highlights
        self.ws = websocket
        self.round_num = round_num
        self.examples_context = examples_context
        self.angles = choose_angles(task_type, drafts, highlights)

    def _build_annotated_drafts_block(self) -> str:
        """Build the annotated drafts block for the prompt."""
        parts: list[str] = []
        for i, draft in enumerate(self.drafts):
            draft_hl = [h for h in self.highlights if h["draft_index"] == i]
            annotated = annotate_draft_with_highlights(
                draft.get("content", ""), draft_hl
            )
            angle = draft.get("angle", f"Draft {i + 1}")
            parts.append(f"DRAFT {i + 1} ({angle}):\n{annotated}")
        return "\n\n---\n\n".join(parts)

    def _build_prompt(self, angle: str) -> str:
        """Build synthesis prompt for a single draft angle."""
        angle_instruction = ANGLE_INSTRUCTIONS.get(angle, "Write naturally.")
        key_material_str = "\n".join(f"- {item}" for item in self.key_material)
        annotated = self._build_annotated_drafts_block()

        return SYNTHESIS_SYSTEM_PROMPT.format(
            task_type=self.task_type,
            topic=self.topic,
            angle=angle,
            round=self.round_num,
            annotated_drafts=annotated,
            interview_summary=self.interview_summary,
            key_material=key_material_str,
            examples_context=self.examples_context,
            angle_instruction=angle_instruction,
        )

    async def synthesize(self) -> list[dict[str, Any]]:
        """Generate 3 synthesis drafts concurrently."""
        tasks = [self._generate_single(i, angle) for i, angle in enumerate(self.angles)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        drafts: list[dict[str, Any]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Synthesis draft %d failed: %s", i, result)
                drafts.append(
                    {
                        "title": f"Draft {i + 1} (Error)",
                        "angle": self.angles[i],
                        "content": f"Synthesis failed: {result}",
                        "word_count": 0,
                    }
                )
            else:
                drafts.append(result)

        return drafts

    async def _generate_single(self, draft_index: int, angle: str) -> dict[str, Any]:
        """Generate a single synthesis draft with streaming."""
        prompt = self._build_prompt(angle)

        await self.ws.send_text(
            DraftStart(
                draft_index=draft_index,
                title=f"{angle} Draft",
                angle=angle,
            ).model_dump_json()
        )

        full_content = ""

        try:
            from litellm import acompletion

            response = await acompletion(
                model="anthropic/claude-sonnet-4-6",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Write the draft now."},
                ],
                stream=True,
            )

            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    clean = _HTML_TAG_RE.sub("", delta.content)
                    if clean:
                        full_content += clean
                        await self.ws.send_text(
                            DraftChunk(
                                draft_index=draft_index,
                                content=clean,
                                done=False,
                            ).model_dump_json()
                        )

        except Exception as e:
            logger.error("Synthesis draft %d LLM error: %s", draft_index, e)
            full_content = f"[Synthesis failed: {e}]"
            await self.ws.send_text(
                DraftChunk(
                    draft_index=draft_index,
                    content=full_content,
                    done=False,
                ).model_dump_json()
            )

        lines = full_content.strip().split("\n")
        title = lines[0].strip("# ").strip() if lines else f"{angle} Draft"
        word_count = len(full_content.split())

        await self.ws.send_text(
            DraftChunk(
                draft_index=draft_index,
                content="",
                done=True,
            ).model_dump_json()
        )
        await self.ws.send_text(
            DraftComplete(
                draft_index=draft_index,
                word_count=word_count,
            ).model_dump_json()
        )

        return {
            "title": title,
            "angle": angle,
            "content": full_content,
            "word_count": word_count,
        }
