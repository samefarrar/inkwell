"""Tests for WebSocket message types."""

from proof_editor.ws_types import (
    DraftChunk,
    DraftComplete,
    DraftStart,
    ErrorMessage,
    InterviewAnswer,
    InterviewQuestion,
    StatusMessage,
    TaskSelect,
    ThoughtMessage,
)


def test_task_select_serialization() -> None:
    msg = TaskSelect(task_type="essay", topic="AI writing")
    data = msg.model_dump()
    assert data["type"] == "task.select"
    assert data["task_type"] == "essay"
    assert data["topic"] == "AI writing"


def test_interview_answer_serialization() -> None:
    msg = InterviewAnswer(answer="I visited last Tuesday")
    assert msg.model_dump()["type"] == "interview.answer"


def test_thought_message() -> None:
    msg = ThoughtMessage(
        assessment="User wants to write about a restaurant",
        missing=["specific dishes", "atmosphere details"],
        sufficient=False,
    )
    data = msg.model_dump()
    assert data["type"] == "thought"
    assert len(data["missing"]) == 2
    assert data["sufficient"] is False


def test_interview_question() -> None:
    msg = InterviewQuestion(
        question="What dishes stood out?",
        context="Need specific food details",
    )
    assert msg.model_dump()["type"] == "interview.question"


def test_draft_messages() -> None:
    start = DraftStart(draft_index=0, title="Test", angle="Thesis-led")
    assert start.model_dump()["type"] == "draft.start"

    chunk = DraftChunk(draft_index=0, content="Hello ", done=False)
    assert chunk.model_dump()["done"] is False

    complete = DraftComplete(draft_index=0, word_count=42)
    assert complete.model_dump()["type"] == "draft.complete"


def test_status_and_error() -> None:
    status = StatusMessage(message="Working...")
    assert status.model_dump()["type"] == "status"

    error = ErrorMessage(message="Something broke")
    assert error.model_dump()["type"] == "error"
