"""Draft generator — creates 3 concurrent drafts in different angles."""

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

from proof_editor.drafting.prompts import build_draft_prompt, get_angles
from proof_editor.examples.loader import format_examples_for_prompt, load_examples
from proof_editor.ws_types import DraftChunk, DraftComplete, DraftStart

logger = logging.getLogger(__name__)


class DraftGenerator:
    """Generates 3 drafts concurrently, streaming each over WebSocket."""

    def __init__(
        self,
        task_type: str,
        topic: str,
        interview_summary: str,
        key_material: list[str],
        websocket: WebSocket,
    ) -> None:
        self.task_type = task_type
        self.topic = topic
        self.interview_summary = interview_summary
        self.key_material = key_material
        self.ws = websocket
        self.angles = get_angles(task_type)

        examples = load_examples()
        self.examples_context = format_examples_for_prompt(examples)

    async def generate(self) -> list[dict[str, Any]]:
        """Generate 3 drafts concurrently, streaming each over WebSocket.

        Returns list of draft dicts with title, angle, content, word_count.
        """
        tasks = [self._generate_single(i, angle) for i, angle in enumerate(self.angles)]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        drafts: list[dict[str, Any]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Draft %d failed: %s", i, result)
                drafts.append(
                    {
                        "title": f"Draft {i + 1} (Error)",
                        "angle": self.angles[i],
                        "content": f"Generation failed: {result}",
                        "word_count": 0,
                    }
                )
            else:
                drafts.append(result)

        return drafts

    async def _generate_single(self, draft_index: int, angle: str) -> dict[str, Any]:
        """Generate a single draft with streaming."""
        prompt = build_draft_prompt(
            task_type=self.task_type,
            topic=self.topic,
            angle=angle,
            interview_summary=self.interview_summary,
            key_material=self.key_material,
            examples_context=self.examples_context,
        )

        # Send draft.start
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
                model="anthropic/claude-sonnet-4-20250514",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Write the draft now."},
                ],
                stream=True,
            )

            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_content += delta.content
                    await self.ws.send_text(
                        DraftChunk(
                            draft_index=draft_index,
                            content=delta.content,
                            done=False,
                        ).model_dump_json()
                    )

        except Exception as e:
            logger.error("Draft %d LLM error: %s", draft_index, e)
            full_content = f"[Draft generation requires ANTHROPIC_API_KEY. Error: {e}]"
            await self.ws.send_text(
                DraftChunk(
                    draft_index=draft_index,
                    content=full_content,
                    done=False,
                ).model_dump_json()
            )

        # Extract title from first line
        lines = full_content.strip().split("\n")
        title = lines[0].strip("# ").strip() if lines else f"{angle} Draft"

        word_count = len(full_content.split())

        # Send completion
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
