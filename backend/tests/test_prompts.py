"""Tests for draft prompt generation."""

from proof_editor.drafting.prompts import build_draft_prompt, get_angles


def test_get_angles_known_types() -> None:
    assert len(get_angles("essay")) == 3
    assert len(get_angles("review")) == 3
    assert len(get_angles("newsletter")) == 3
    assert len(get_angles("landing_page")) == 3
    assert len(get_angles("blog_post")) == 3


def test_get_angles_unknown_falls_back_to_essay() -> None:
    assert get_angles("unknown_type") == get_angles("essay")


def test_build_draft_prompt_includes_material() -> None:
    prompt = build_draft_prompt(
        task_type="essay",
        topic="AI writing tools",
        angle="Thesis-led",
        interview_summary="User discussed AI writing partners",
        key_material=["personal experience", "industry trends"],
        examples_context="",
    )
    assert "AI writing tools" in prompt
    assert "Thesis-led" in prompt
    assert "personal experience" in prompt
    assert "industry trends" in prompt
