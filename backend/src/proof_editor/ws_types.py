"""WebSocket message types — shared between backend handlers and frontend."""

from typing import Literal

from pydantic import BaseModel

# --- Client → Server ---


class TaskSelect(BaseModel):
    type: Literal["task.select"] = "task.select"
    task_type: str
    topic: str


class InterviewAnswer(BaseModel):
    type: Literal["interview.answer"] = "interview.answer"
    answer: str


class DraftHighlight(BaseModel):
    type: Literal["draft.highlight"] = "draft.highlight"
    draft_index: int
    start: int
    end: int
    sentiment: Literal["like", "flag"]
    label: str | None = None
    note: str | None = None


class HighlightUpdate(BaseModel):
    type: Literal["highlight.update"] = "highlight.update"
    draft_index: int
    highlight_index: int  # position in the highlights array
    label: str  # new custom label (snake_cased)


class HighlightRemove(BaseModel):
    type: Literal["highlight.remove"] = "highlight.remove"
    draft_index: int
    highlight_index: int


class DraftEdit(BaseModel):
    type: Literal["draft.edit"] = "draft.edit"
    draft_index: int
    content: str


class DraftSynthesize(BaseModel):
    type: Literal["draft.synthesize"] = "draft.synthesize"


class SessionResume(BaseModel):
    type: Literal["session.resume"] = "session.resume"
    session_id: int


class SessionCancel(BaseModel):
    type: Literal["session.cancel"] = "session.cancel"


# --- Server → Client ---


class ThoughtMessage(BaseModel):
    type: Literal["thought"] = "thought"
    assessment: str
    missing: list[str]
    sufficient: bool


class InterviewQuestion(BaseModel):
    type: Literal["interview.question"] = "interview.question"
    question: str
    context: str


class SearchResultMessage(BaseModel):
    type: Literal["search.result"] = "search.result"
    query: str
    summary: str


class ReadyToDraft(BaseModel):
    type: Literal["ready_to_draft"] = "ready_to_draft"
    summary: str
    key_material: list[str]


class DraftStart(BaseModel):
    type: Literal["draft.start"] = "draft.start"
    draft_index: int
    title: str
    angle: str


class DraftChunk(BaseModel):
    type: Literal["draft.chunk"] = "draft.chunk"
    draft_index: int
    content: str
    done: bool


class DraftComplete(BaseModel):
    type: Literal["draft.complete"] = "draft.complete"
    draft_index: int
    word_count: int


class DraftSynthesized(BaseModel):
    type: Literal["draft.synthesized"] = "draft.synthesized"
    content: str
    sent_to_proof: bool = False


class StatusMessage(BaseModel):
    type: Literal["status"] = "status"
    message: str


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    message: str


# Discriminated union for parsing incoming messages
ClientMessage = (
    TaskSelect
    | InterviewAnswer
    | DraftHighlight
    | HighlightUpdate
    | HighlightRemove
    | DraftEdit
    | DraftSynthesize
    | SessionResume
    | SessionCancel
)

ServerMessage = (
    ThoughtMessage
    | InterviewQuestion
    | SearchResultMessage
    | ReadyToDraft
    | DraftStart
    | DraftChunk
    | DraftComplete
    | DraftSynthesized
    | StatusMessage
    | ErrorMessage
)
