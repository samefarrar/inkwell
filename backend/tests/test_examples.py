"""Tests for the examples loader."""

from pathlib import Path
from tempfile import TemporaryDirectory

from proof_editor.examples.loader import (
    Example,
    format_examples_for_prompt,
    load_examples,
)


def test_load_examples_from_directory() -> None:
    with TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        (p / "sample_essay.md").write_text("This is a sample essay about testing.")
        (p / "another_piece.txt").write_text("Another piece of writing here.")
        (p / "not_a_text.pdf").write_bytes(b"ignored")

        examples = load_examples(p)
        assert len(examples) == 2
        assert all(isinstance(e, Example) for e in examples)
        titles = [e.title for e in examples]
        assert "Another Piece" in titles
        assert "Sample Essay" in titles


def test_load_examples_missing_directory() -> None:
    examples = load_examples(Path("/nonexistent/path"))
    assert examples == []


def test_format_examples_empty() -> None:
    assert format_examples_for_prompt([]) == ""


def test_format_examples_includes_content() -> None:
    examples = [
        Example(title="Test", content="Hello world content", word_count=3),
    ]
    formatted = format_examples_for_prompt(examples)
    assert "Test" in formatted
    assert "Hello world content" in formatted
    assert "3 words" in formatted
