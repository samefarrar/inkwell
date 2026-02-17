---
title: "feat: MVP AI Writing Partner"
type: feat
date: 2026-02-16
---

# MVP AI Writing Partner

## Overview

Build the complete MVP of the Proof Editor — a single web app (FastAPI + Svelte 5) where an AI writing partner interviews the user, generates 3 simultaneous drafts in different angles, lets the user highlight favorites across drafts, synthesizes a refined draft, and provides focused editing with inline Every Write Style Guide suggestions. The system compounds via a learning flywheel that stores feedback and style examples.

## Problem Statement

AI writing tools either generate slop (ChatGPT paste) or require complex setups (separate apps, copy-paste between tools). Writers need a single environment where the AI acts as a true collaborator: interviewing for real stories, showing its reasoning, generating multiple angles, and iterating based on what the writer actually likes — all in one place.

## Proposed Solution

A 5-screen web app with the workflow: Task Select → Interview → Three Drafts → Highlight → Focus Edit. All AI interaction uses LiteLLM tool calls, which the backend translates to typed WebSocket messages that the frontend renders as specific UI components (thought blocks, chat bubbles, draft panels, suggestion cards).

## Technical Approach

### Architecture

```
┌──────────────────────────────────────────────┐
│  Svelte 5 Frontend (SvelteKit + Vite)        │
│  ┌────────────────────────────────────┐      │
│  │ Screen Router (5 screens)          │      │
│  │ WebSocket Client (ws.ts)           │      │
│  │ TipTap Editors (draft panels)      │      │
│  │ Svelte Stores (shared state)       │      │
│  └────────────────────────────────────┘      │
└──────────────┬───────────────────────────────┘
               │ WebSocket (ws://localhost:8000/ws)
┌──────────────▼───────────────────────────────┐
│  FastAPI Backend                             │
│  ┌────────────────────────────────────┐      │
│  │ WebSocket Handler → Orchestrator   │      │
│  │ Interviewer (LiteLLM tool calls)   │      │
│  │ Draft Generator (3x concurrent)    │      │
│  │ Synthesizer (merge highlights)     │      │
│  │ Style Engine (rule-based checks)   │      │
│  │ Examples Loader (inspo/ folder)    │      │
│  └────────────────────────────────────┘      │
└──────────────┬───────────────────────────────┘
               │
┌──────────────▼───────────────────────────────┐
│  SQLite (via SQLModel)                       │
│  sessions, feedback, highlights, preferences │
└──────────────────────────────────────────────┘
```

### Implementation Phases

#### Phase 1: Project Scaffolding

Set up both projects with all dependencies, shared types, and a working "hello world" WebSocket connection.

**Backend tasks:**

- [ ] Initialize `backend/` with `uv init` and `pyproject.toml`
  - Dependencies: `fastapi`, `uvicorn[standard]`, `litellm`, `sqlmodel`, `httpx`, `python-frontmatter`
  - Dev dependencies: `pytest`, `pytest-anyio`, `ruff`, `mypy`
- [ ] Create `backend/src/proof_editor/__init__.py` and `main.py`
  - FastAPI app with CORS middleware (allow localhost:5173)
  - WebSocket endpoint at `/ws`
  - Health check at `GET /health`
- [ ] Create `backend/src/proof_editor/models/` with SQLModel schemas
  - `session.py`: `Session(id, task_type, topic, status, created_at)`
  - `feedback.py`: `Feedback(id, session_id, draft_index, text, replacement, accepted, rule_id, created_at)`
  - `highlight.py`: `Highlight(id, session_id, draft_index, start, end, sentiment, note, created_at)`
  - `preference.py`: `Preference(id, key, value, updated_at)`
- [ ] Create `backend/src/proof_editor/db.py`
  - SQLite engine setup (`data/proof_editor.db`)
  - `create_tables()` on startup
- [ ] Create shared WebSocket message types in `backend/src/proof_editor/ws_types.py`
  - Pydantic models for all client→server and server→client messages
  - Discriminated union via `type` field
- [ ] Add `.gitignore` (Python + Node + SQLite + .DS_Store)

**Frontend tasks:**

- [ ] Initialize `frontend/` with `npx sv create` (SvelteKit, TypeScript)
- [ ] Install dependencies: `@tiptap/core`, `@tiptap/starter-kit`, `@tiptap/extension-highlight`, `@tiptap/extension-collaboration`
- [ ] Create `frontend/src/lib/ws.ts` — WebSocket client
  - Connect to `ws://localhost:8000/ws`
  - Auto-reconnect with exponential backoff
  - Typed message send/receive matching backend ws_types
- [ ] Create `frontend/src/lib/stores/session.svelte.ts` — session state store (Runes)
  - Current screen, session data, drafts, highlights
- [ ] Create minimal route at `frontend/src/routes/+page.svelte`
  - Screen router based on session state
- [ ] Verify round-trip: frontend sends `task.select`, backend echoes acknowledgement

**Success criteria:** `uv run python -m proof_editor` starts backend, `npm run dev` starts frontend, WebSocket connects and messages flow both directions.

```python
# backend/src/proof_editor/ws_types.py
from pydantic import BaseModel
from typing import Literal

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
    note: str | None = None

class DraftSynthesize(BaseModel):
    type: Literal["draft.synthesize"] = "draft.synthesize"

class ThoughtMessage(BaseModel):
    type: Literal["thought"] = "thought"
    assessment: str
    missing: list[str]
    sufficient: bool

class InterviewQuestion(BaseModel):
    type: Literal["interview.question"] = "interview.question"
    question: str
    context: str

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

class StatusMessage(BaseModel):
    type: Literal["status"] = "status"
    message: str

# Focus mode messages (Phase 5)
class FocusEnter(BaseModel):
    type: Literal["focus.enter"] = "focus.enter"
    content: str  # draft content to edit
    source: Literal["draft", "synthesized"]
    draft_index: int | None = None

class FocusSuggestion(BaseModel):
    type: Literal["focus.suggestion"] = "focus.suggestion"
    id: str
    quote: str
    replacement: str
    explanation: str
    rule_id: str
    confidence: float

class FocusComment(BaseModel):
    type: Literal["focus.comment"] = "focus.comment"
    id: str
    quote: str
    comment: str
    category: Literal["structure", "voice", "clarity", "impact"]

class FocusFeedback(BaseModel):
    type: Literal["focus.feedback"] = "focus.feedback"
    id: str
    action: Literal["accept", "reject", "dismiss"]
```

#### Phase 2: Interview Flow

The core interaction loop — user enters task, AI interviews them one question at a time with visible reasoning.

**Backend tasks:**

- [ ] Create `backend/src/proof_editor/agent/orchestrator.py`
  - Manages session state machine: `task_select → interview → drafting → highlighting → focused`
  - Routes WebSocket messages to appropriate handler
  - Holds conversation history per session
- [ ] Create `backend/src/proof_editor/agent/interviewer.py`
  - System prompt: "You are an AI writing partner. Interview the user to extract real stories, insights, and experiences. Ask ONE question at a time. After each answer, assess what you know vs what's missing."
  - LiteLLM tool definitions:
    ```python
    tools = [
        {"type": "function", "function": {
            "name": "show_thought",
            "parameters": {
                "assessment": {"type": "string"},
                "missing": {"type": "array", "items": {"type": "string"}},
                "sufficient": {"type": "boolean"}
            }
        }},
        {"type": "function", "function": {
            "name": "ask_question",
            "parameters": {
                "question": {"type": "string"},
                "context": {"type": "string"}
            }
        }},
        {"type": "function", "function": {
            "name": "ready_to_draft",
            "parameters": {
                "summary": {"type": "string"},
                "key_material": {"type": "array", "items": {"type": "string"}}
            }
        }}
    ]
    ```
  - Process: receive answer → append to conversation → call LiteLLM → parse tool calls → send as WebSocket messages
  - When `ready_to_draft` is called, transition to drafting phase
- [ ] Create `backend/src/proof_editor/examples/loader.py`
  - On startup, read all `.md` and `.txt` files from `inspo/`
  - Store as list of `Example(title, content, word_count)`
  - Inject into interviewer system prompt as style reference
- [ ] Write tests: `tests/test_interviewer.py`
  - Test tool call parsing
  - Test sufficiency assessment triggers `ready_to_draft`
  - Test conversation history accumulation

**Frontend tasks:**

- [ ] Create `frontend/src/lib/components/TaskSelector.svelte`
  - Writing type dropdown: Essay, Review, Newsletter, Landing Page, Blog Post
  - Topic text input
  - "Start Interview" button → sends `task.select` over WebSocket
- [ ] Create `frontend/src/lib/components/Interview.svelte`
  - Chat-style layout: messages scroll down
  - AI messages: rendered from `interview.question` WebSocket messages
  - User messages: text input → sends `interview.answer`
  - Thought blocks: collapsible orange panel from `thought` messages
    - Shows assessment text, bulleted missing items, "sufficient" badge
  - Status messages: inline gray text from `status` messages
  - "Start Writing" button appears when AI signals `ready_to_draft`

**Success criteria:** User enters "restaurant review of Burnt Orange Brighton", AI asks 2-3 targeted questions with visible thought blocks, then signals ready to draft.

#### Phase 3: Three Simultaneous Drafts

Generate 3 drafts in different angles, streaming all simultaneously over WebSocket.

**Backend tasks:**

- [ ] Create `backend/src/proof_editor/drafting/generator.py`
  - `generate_drafts(session, interview_material, examples) -> AsyncGenerator`
  - Determines 3 task-appropriate angles based on task type:
    ```python
    ANGLE_MAP = {
        "review": ["Atmosphere-led", "Subject-led", "Recommendation-led"],
        "essay": ["Thesis-led", "Narrative-led", "Contrarian-led"],
        "newsletter": ["Insight-led", "Story-led", "Tactical-led"],
        "landing_page": ["Benefit-led", "Social-proof-led", "Problem-led"],
        "blog_post": ["Personal-led", "How-to-led", "Opinion-led"],
    }
    ```
  - Launches 3 concurrent LiteLLM `acompletion()` calls with streaming
  - Each call gets: interview material, style examples from `inspo/`, angle-specific instructions
  - Streams chunks as `draft.chunk` messages, sends `draft.start` before and `draft.complete` after
  - Uses `asyncio.gather()` to run all 3 concurrently
- [ ] Create draft prompt template in `backend/src/proof_editor/drafting/prompts.py`
  - Includes: interview summary, key material, style examples, angle instruction, Every Write Style Guide rules
  - Target: 300-500 words per draft (configurable)
- [ ] Wire into orchestrator: when `ready_to_draft` fires → start 3 draft streams
- [ ] Write tests: `tests/test_generator.py`
  - Test angle selection by task type
  - Test concurrent streaming (mock LiteLLM responses)

**Frontend tasks:**

- [ ] Create `frontend/src/lib/components/DraftPanel.svelte`
  - TipTap editor instance (read-only during streaming, editable after)
  - Header: angle label + word count (updates as chunks arrive)
  - Expand button: click to view full-width
  - Content streams in as `draft.chunk` messages arrive
  - Loading state: skeleton/shimmer while waiting for `draft.start`
- [ ] Create `frontend/src/lib/components/DraftComparison.svelte`
  - 3-column layout with `DraftPanel` instances
  - Responsive: side-by-side on desktop
  - Shows progress indicators while streaming
  - Transition from interview screen when first `draft.start` arrives
- [ ] Create `frontend/src/lib/stores/drafts.svelte.ts`
  - Stores 3 draft objects: `{title, angle, content, wordCount, streaming, complete}`
  - Updates on `draft.start`, `draft.chunk`, `draft.complete` messages

**Success criteria:** After interview completes, 3 draft panels appear and stream simultaneously. Each shows angle label, word count, and full draft content.

#### Phase 4: Highlighting + Synthesis

Cross-draft highlighting and AI-driven synthesis of favorites.

**Backend tasks:**

- [ ] Create `backend/src/proof_editor/drafting/synthesizer.py`
  - `synthesize(session, drafts, highlights, flags) -> str`
  - Builds a prompt with:
    - All 3 draft contents
    - Highlighted sections marked as "USER LIKES THIS"
    - Flagged sections marked as "USER WANTS THIS FIXED: [note]"
    - Instruction: "Write a new draft that incorporates the highlighted sections and addresses the flagged issues"
  - Single LiteLLM call (not streaming for MVP — the result replaces the drafts view)
  - Returns synthesized draft content
- [ ] Store highlights in SQLite for the learning flywheel
  - `Highlight(session_id, draft_index, start, end, text, sentiment, note)`
- [ ] Wire into orchestrator: on `draft.synthesize` → run synthesizer → send result

**Frontend tasks:**

- [ ] Add highlighting to `DraftPanel.svelte`
  - TipTap `Highlight` extension for marking text
  - Two highlight modes:
    - Green highlight: "I like this" (sentiment: "like")
    - Red/orange highlight: "Fix this" (sentiment: "flag", with note input)
  - Toolbar appears on text selection: [Like] [Flag] buttons
  - Each highlight sends `draft.highlight` message to backend
- [ ] Create `frontend/src/lib/stores/highlights.svelte.ts`
  - Cross-panel highlight state: list of `{draft_index, start, end, text, sentiment, note}`
  - Count of highlights shown in UI
- [ ] Add "Synthesize" button to `DraftComparison.svelte`
  - Appears after at least 1 highlight exists
  - Shows count: "Synthesize from 5 highlights"
  - Sends `draft.synthesize` → shows loading state → receives synthesized draft
- [ ] Add "Focus on this" button to each `DraftPanel.svelte`
  - Appears after drafts are complete (even without highlighting)
  - Transitions to the focused editing screen with that draft's content

**Success criteria:** User can highlight text in green (like) or flag in orange (fix) across all 3 drafts, click "Synthesize", and receive a merged draft. Alternatively, click "Focus on this" on any single draft.

#### Phase 5: Focused Editing — Editorial Collaborator

Single-draft full-width editor modeled on the **Proof.app collaboration pattern** (see `proof_ui.png`), NOT the grammar-checker model from `editor_inspiration.tsx`. The AI acts as an editorial collaborator that makes two types of contributions:

1. **Inline Suggestions** (track-change style): Specific text replacements for rule-based style guide violations. Green underline for insertions, red strikethrough for deletions. User accepts or rejects each one. These come from the deterministic style engine.

2. **Editorial Comments**: Structural, advisory feedback anchored to specific text. "Consider adding a concrete example here", "This transition is abrupt — try connecting to the previous paragraph", "Show, don't tell". These come from an LLM editorial pass. The user reads them and edits manually — they're guidance, not find-and-replace.

**Design principle:** No category filter pills (grammar, spelling, punctuation, style, clarity). Instead, a clean sidebar split: **Suggestions** (actionable, accept/reject) and **Comments** (advisory, dismiss when addressed). This matches how a human editor works — they either mark up specific changes OR leave notes in the margin.

**Backend tasks:**

- [ ] Create `backend/src/proof_editor/style/engine.py`
  - `analyze(text: str) -> list[StyleViolation]`
  - Deterministic, rule-based checks against Every Write Style Guide
  - Returns structured violations: `quote`, `replacement`, `explanation`, `rule_id`, `confidence`
  - Fast — runs in <100ms, no LLM call
- [ ] Create `backend/src/proof_editor/style/rules/` with individual rule modules:
  - `oxford_comma.py`: detect missing Oxford commas
  - `passive_voice.py`: flag passive constructions
  - `filler_words.py`: flag "actually", "very", "just", "really"
  - `numbers.py`: spell out 1-9, numerals for 10+
  - `em_dash.py`: check spacing, max 2 per paragraph
  - `title_case.py`: check headline formatting
  - `active_links.py`: flag "click here" link text
- [ ] Create `backend/src/proof_editor/style/editor.py` — LLM-driven editorial comments
  - `generate_comments(text: str, interview_context: str, style_examples: list[str]) -> list[EditorialComment]`
  - LiteLLM call with system prompt: "You are a senior editor at a writing publication. Read this draft and leave 3-5 editorial comments. Focus on structure, clarity, voice, and impact — not grammar or spelling (those are handled separately). Anchor each comment to a specific quote from the text."
  - Returns: `EditorialComment(quote: str, comment: str, category: Literal["structure", "voice", "clarity", "impact"])`
  - Uses interview context to check: did the draft actually use the user's stories? Is the hook compelling?
- [ ] Create REST endpoint `POST /api/analyze`
  - Accepts document text + session_id
  - Returns `{"suggestions": list[StyleViolation], "comments": list[EditorialComment]}`
  - Style violations are instant (rule engine); editorial comments may take 2-3s (LLM call)
  - Supports streaming: send suggestions immediately, then comments when LLM finishes
- [ ] Add WebSocket messages for focus mode:
  ```python
  class FocusSuggestion(BaseModel):
      type: Literal["focus.suggestion"] = "focus.suggestion"
      id: str
      quote: str
      replacement: str
      explanation: str
      rule_id: str
      confidence: float

  class FocusComment(BaseModel):
      type: Literal["focus.comment"] = "focus.comment"
      id: str
      quote: str
      comment: str
      category: str

  class FocusFeedback(BaseModel):
      type: Literal["focus.feedback"] = "focus.feedback"
      id: str
      action: Literal["accept", "reject", "dismiss"]
  ```
- [ ] Write tests: `tests/test_style/` with one test file per rule
  - Test positive and negative cases for each rule
  - Test confidence filtering
  - Test editorial comment parsing

**Frontend tasks:**

- [ ] Create `frontend/src/lib/components/FocusEditor.svelte`
  - Full-width TipTap editor (editable), clean writing-focused layout
  - Load content from selected/synthesized draft
  - Minimal toolbar: bold, italic, headers, lists, link (no font picker, no color picker)
  - Word count in footer, authorship indicator (like Proof's "Human 62% / AI 38%")
  - TipTap extensions needed:
    - `@tiptap/extension-collaboration` (for suggestion marks — track-change decorations)
    - Custom `suggestion` mark: renders as green underline (insert) or red strikethrough (delete)
    - Custom `comment` mark: renders as subtle highlight with margin indicator
- [ ] Create `frontend/src/lib/components/SuggestionMark.svelte`
  - Inline decoration in the editor for style suggestions
  - On hover/click: tooltip shows original → replacement + explanation + [Accept] [Reject]
  - Accept: applies replacement in TipTap, removes mark, sends `focus.feedback` (accept)
  - Reject: removes mark, sends `focus.feedback` (reject)
  - Styling: green underline for insertions, red strikethrough for deletions (matches Proof)
- [ ] Create `frontend/src/lib/components/CommentMark.svelte`
  - Subtle yellow/orange highlight on the quoted text
  - Clicking opens a margin popover (right side) showing the editorial comment
  - Comment shows: category tag (structure/voice/clarity/impact) + comment text
  - [Dismiss] button removes the comment, sends `focus.feedback` (dismiss)
  - No accept/reject — these are advisory, user acts on them manually
- [ ] Create `frontend/src/lib/components/FocusSidebar.svelte`
  - Right sidebar with two tabs: **Suggestions** and **Comments**
  - **Suggestions tab**: list of pending style suggestions
    - Each item: quote snippet (truncated), rule name, [Accept] [Reject]
    - Count badge on tab header
    - Clicking an item scrolls to and highlights the suggestion in the editor
  - **Comments tab**: list of editorial comments
    - Each item: quote snippet, category tag, comment preview
    - Clicking scrolls to the commented text
    - [Dismiss] button per comment
  - No category filter pills — just the two-tab split
- [ ] Trigger analysis:
  - On entering focus mode: auto-run style engine (instant) + editorial LLM (async)
  - On idle: debounced re-analysis after user stops typing for 3 seconds (style engine only — editorial comments don't re-run on every keystroke)
  - After accepting/rejecting a suggestion: re-run style engine on changed paragraph only

**Success criteria:** User clicks "Focus on this", sees a clean full-width editor that feels like Proof. Green-underlined suggestions appear inline for style guide violations (accept/reject). Yellow-highlighted comments appear for structural editorial guidance (read and dismiss). Sidebar shows both lists. Feels like working with a human editor, not a grammar checker.

#### Phase 6: Learning Flywheel

Persist all feedback signals and use them to improve future sessions.

**Backend tasks:**

- [ ] Create `backend/src/proof_editor/learning/flywheel.py`
  - `record_feedback(session_id, rule_id, accepted: bool, quote, replacement)`
  - `get_rule_confidence(rule_id) -> float` — based on accept/reject ratio
  - `get_style_preferences() -> dict` — aggregated from all feedback
  - `get_highlighted_favorites() -> list[str]` — text the user has liked across sessions
- [ ] Create `backend/src/proof_editor/learning/context_builder.py`
  - Builds LLM context from accumulated data:
    - Style examples from `inspo/`
    - User's highlighted favorites (most-liked phrases/structures)
    - Derived writing preferences (e.g., "user prefers short sentences", "user likes concrete details")
  - Injected into interviewer and draft generator prompts
- [ ] Integrate into style engine: filter violations below confidence threshold (0.3)
- [ ] Integrate into draft generator: include context from flywheel in prompts
- [ ] Write tests: `tests/test_flywheel.py`
  - Test confidence calculation
  - Test preference aggregation

**Frontend tasks:**

- [ ] Ensure all accept/reject/dismiss actions send `focus.feedback` to backend
  - Suggestion accept/reject: feeds rule confidence in the style engine
  - Comment dismiss: signals which editorial feedback categories the user engages with
- [ ] Show learning indicator somewhere subtle (e.g., "Learning from your preferences" in footer)

**Success criteria:** After using the app for multiple sessions, draft quality improves because the system incorporates past highlights and feedback. Style suggestions respect learned confidence (frequently-rejected rules have lower confidence and appear less).

## Acceptance Criteria

### Functional Requirements

- [ ] User can specify a writing task (type + topic) and start an interview
- [ ] AI interviews with visible thought blocks and one question at a time
- [ ] 3 drafts stream simultaneously with angle labels and word counts
- [ ] User can highlight text they like (green) and flag text to fix (orange + note) across all 3 drafts
- [ ] "Synthesize" merges highlighted favorites into a new draft
- [ ] "Focus on this" opens single-draft editor modeled on Proof.app editorial experience
- [ ] **Inline suggestions**: track-change style (green underline / red strikethrough) for style guide violations, with accept/reject
- [ ] **Editorial comments**: LLM-generated structural feedback anchored to text, with dismiss
- [ ] **Focus sidebar**: two-tab split (Suggestions / Comments), clicking items scrolls to location in editor
- [ ] Accept/reject/dismiss actions persist as feedback to the learning flywheel
- [ ] Style examples from `inspo/` are loaded and used in draft generation
- [ ] Learning flywheel stores feedback and adjusts future behavior

### Non-Functional Requirements

- [ ] Backend starts with `uv run python -m proof_editor`
- [ ] Frontend starts with `npm run dev`
- [ ] WebSocket connection auto-reconnects on drop
- [ ] Draft streaming feels responsive (chunks arrive visibly)
- [ ] Style analysis returns within 500ms for documents under 2000 words

### Quality Gates

- [ ] All style rules have unit tests
- [ ] WebSocket message types are shared between backend type definitions and frontend TypeScript types
- [ ] `ruff check` and `ruff format` pass
- [ ] `mypy` passes on backend

## Dependencies & Prerequisites

- Python 3.12+ with `uv` installed
- Node.js 20+ with `npm`
- Anthropic API key (set as `ANTHROPIC_API_KEY` env var — used by LiteLLM)
- Writing examples in `inspo/` folder (Janan Ganesh articles)

## Risk Analysis & Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| TipTap + Svelte 5 integration issues | High | Use `@tiptap/core` directly with Svelte's `onMount`; avoid framework-specific wrappers if buggy |
| 3 concurrent LLM streams overwhelm WebSocket | Medium | Rate-limit chunks (batch every 100ms); test with slow connections |
| Cross-panel highlighting UX complexity | High | Start with simple text selection → button click; avoid drag-across-panels for MVP |
| LiteLLM tool call parsing fragility | Medium | Validate all tool call responses with Pydantic; fallback to raw text on parse failure |
| Style rule false positives annoy users | Low | Start with high-confidence rules only; learning flywheel naturally suppresses bad rules |

## References

### Internal
- Brainstorm: `docs/brainstorms/2026-02-16-mvp-brainstorm.md`
- Architecture: `CLAUDE.md`
- Proof API: `EDITOR_DETAIL.md` (deferred for MVP)
- Style inspiration: `editor_inspiration.tsx` (React reference for suggestion UI)
- Writing examples: `inspo/janan_ganesh_essay.md`, `inspo/janan_ganesh_essay_pol.md`

### External
- [TipTap docs](https://tiptap.dev/docs)
- [Svelte 5 Runes](https://svelte.dev/docs/svelte/$state)
- [LiteLLM tool use](https://docs.litellm.ai/docs/completion/function_call)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [Every Write Style Guide](https://github.com/EveryInc/compound-engineering-plugin/blob/main/plugins/compound-engineering/skills/every-style-editor/references/EVERY_WRITE_STYLE.md)
