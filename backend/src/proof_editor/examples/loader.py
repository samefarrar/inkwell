"""Examples loader — reads writing samples from inspo/ directory."""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

INSPO_DIR = Path(__file__).parent.parent.parent.parent.parent / "inspo"


@dataclass
class Example:
    title: str
    content: str
    word_count: int


def load_examples(directory: Path | None = None) -> list[Example]:
    """Load all .md and .txt files from the inspo directory."""
    inspo_dir = directory or INSPO_DIR
    examples: list[Example] = []

    if not inspo_dir.exists():
        logger.warning("Inspo directory not found: %s", inspo_dir)
        return examples

    for path in sorted(inspo_dir.iterdir()):
        if path.suffix in (".md", ".txt"):
            content = path.read_text(encoding="utf-8")
            title = path.stem.replace("_", " ").title()
            word_count = len(content.split())
            examples.append(
                Example(title=title, content=content, word_count=word_count)
            )
            logger.info("Loaded example: %s (%d words)", title, word_count)

    return examples


def format_examples_for_prompt(examples: list[Example]) -> str:
    """Format examples as context for LLM prompts."""
    if not examples:
        return ""

    parts = ["Here are writing examples to match the user's voice and style:\n"]
    for ex in examples:
        parts.append(f"--- {ex.title} ({ex.word_count} words) ---")
        # Truncate long examples to ~500 words for prompt efficiency
        words = ex.content.split()
        if len(words) > 500:
            parts.append(" ".join(words[:500]) + "\n[...truncated...]")
        else:
            parts.append(ex.content)
        parts.append("")

    return "\n".join(parts)
