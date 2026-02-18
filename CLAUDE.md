# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Proof Editor** is an AI writing partner — a single web app (Svelte 5 + FastAPI) where the user specifies a writing task, the AI interviews them to extract real stories/insights/experiences, generates 3 drafts simultaneously in different angles, lets the user highlight favorites across drafts, synthesizes a refined draft, and then provides a focused single-draft editing mode with inline style suggestions based on the Every Write Style Guide.

The system compounds — every interaction (interview answers, highlighted favorites, style feedback, accepted/rejected suggestions, uploaded writing examples from `inspo/`) feeds the learning flywheel to improve future output.

**MVP**: Self-contained web app. No macOS Proof.app dependency. TipTap (ProseMirror) handles all rich text editing, selection, highlighting, inline suggestions, and track changes within the browser.

## Tech Stack

- **Backend**: Python 3.12+ / FastAPI / LiteLLM (unified LLM API with tool use)
- **Frontend**: Svelte 5 (Runes) / TipTap (ProseMirror) / Vite
- **Real-time**: WebSockets (bi-directional for interview chat + draft streaming)
- **Storage**: SQLite + SQLModel (preferences, feedback, examples, interview history)
- **Proof.app integration**: deferred (MVP is self-contained web app; bridge client at localhost:9847 is future scope)
- **Package management**: uv (never pip)
- **Linting**: ruff check --fix && ruff format
- **Type checking**: mypy
- **Testing**: pytest with anyio for async

### Why LiteLLM

LiteLLM provides a unified OpenAI-compatible API across providers (Anthropic, OpenAI, etc.) with native tool use support. This gives us:
- **Tool use for structured outputs**: drafts, interview questions, sufficiency assessments all return as tool calls with typed schemas — the frontend renders them in a unified UI
- **Provider flexibility**: swap models without changing application code
- **Streaming with tools**: stream draft content while using tools for structured metadata (titles, word counts, angle labels)

## Architecture

```
proof_editor/
├── backend/
│   ├── src/proof_editor/
│   │   ├── api/              # FastAPI routes + WebSocket handlers
│   │   ├── agent/            # Writing partner agent (interview → draft → feedback loop)
│   │   │   ├── interviewer.py    # Targeted questioning to extract stories/insights
│   │   │   ├── hook_developer.py # Develops hooks from interview material
│   │   │   └── orchestrator.py   # Manages the interview → draft → refine workflow
│   │   ├── drafting/         # Multi-angle draft generation + synthesis
│   │   │   ├── generator.py      # Generates 3 drafts in task-appropriate angles
│   │   │   └── synthesizer.py    # Iterative 3-draft synthesis from highlight feedback
│   │   ├── bridge/           # Proof Editor HTTP bridge client (localhost:9847)
│   │   ├── style/            # Every Write Style Guide rule engine
│   │   ├── learning/         # Feedback flywheel (preferences, patterns, confidence)
│   │   └── examples/         # Writing sample ingestion + category management
│   ├── data/
│   │   ├── style_rules/      # Structured style guide rules
│   │   └── examples/         # Categorized writing samples
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/       # Svelte components
│   │   │   │   ├── Interview.svelte      # Chat-style interview UI
│   │   │   │   ├── DraftPanel.svelte     # Single TipTap draft with highlighting
│   │   │   │   ├── DraftComparison.svelte # 3-panel side-by-side view
│   │   │   │   └── TaskSelector.svelte   # Writing task specification
│   │   │   ├── stores/          # Svelte stores for cross-panel selection state
│   │   │   └── ws.ts            # WebSocket client
│   │   └── routes/              # SvelteKit pages
│   └── static/
├── EDITOR_DETAIL.md         # Proof bridge API reference (canonical)
└── proof_ui.png             # UI reference screenshot
```

### Writing Partner Workflow

The agent is not a "generate and done" tool — it's a conversational writing partner:

```
1. TASK       → User specifies: essay, newsletter, landing page, review, etc.
2. INTERVIEW  → AI asks ONE targeted question at a time:
                 → Assesses what it has vs what's missing (visible "Thought" block)
                 → Asks the single most impactful question to fill the gap
                 → User answers → AI re-assesses sufficiency
                 → Repeats until material is sufficient (typically 2-4 questions)
                 → AI does background research to supplement user info
3. DRAFT      → Generates 3 angles simultaneously via WebSocket:
                 → Each draft has: title, angle label, character count, word count
                 → Angles are task-appropriate (not always the same 3)
4. HIGHLIGHT  → User highlights lines they like across all 3 drafts
                 → Flags sections to fix with notes
                 → Adds custom labels via gear icon (e.g. "too_formal")
                 → Can delete accidental highlights via X button
                 → Can directly edit draft text (contenteditable)
5. SYNTHESIZE → AI generates 3 NEW refined drafts (not 1 merged draft)
                 → Keeps angles the user liked, replaces flagged angles
                 → All highlights fed as semantic XML tags in prompt
                 → User edits are reflected in the synthesis input
                 → Loop repeats: highlight → synthesize → 3 new drafts
                 → Continues until user clicks "Focus on this"
6. FOCUS      → User selects one draft to focus on
                 → Transitions to single-draft editing mode
7. FEEDBACK   → Proof style agent provides inline editorial suggestions
                 → User accepts/rejects → compounds into learning flywheel
```

### Interview Pattern (from Spiral reference)

The interviewer uses LiteLLM tool calls to structure each step. Critical design rules:

1. **One question at a time** — never dump a list of 5 questions. Ask the single most impactful question, wait for the answer, reassess.

2. **Visible reasoning** — each turn shows a "Thought" block: what the AI knows, what's missing, and why it's asking this specific question. The frontend renders these in a collapsible UI element.

3. **Sufficiency assessment** — after each answer, the AI evaluates whether it has enough material to write. It categorizes what it has (topic, occasion, specific details, sensory info, standout moments) and what's still missing.

4. **Background research** — once the interview has enough user material, the AI uses tool calls to search for supplementary context (e.g., restaurant awards, company background, topic research) before drafting.

5. **Task-appropriate angles** — the 3 draft angles adapt to the writing task:
   - Restaurant review: atmosphere-led, dish-led, recommendation-led
   - Essay: thesis-led, narrative-led, contrarian-led
   - Newsletter: insight-led, story-led, tactical-led
   - Landing page: benefit-led, social-proof-led, problem-led

### LiteLLM Tool Definitions

The agent uses tools for structured interaction with the frontend:

```python
# Interview tools
ask_question    → {"question": str, "context": str}  # renders as chat message
show_thought    → {"assessment": str, "missing": list[str], "sufficient": bool}
search_context  → {"query": str}  # background research before drafting

# Draft tools
create_draft    → {"title": str, "angle": str, "content": str, "word_count": int}
request_highlights → {}  # signals frontend to enter highlight mode

# Synthesis tools
synthesize_draft → {"content": str, "incorporated": list[str], "changed": list[str]}
send_to_proof    → {"content": str, "title": str}
```

### Key Subsystems

**Interviewer** (`agent/interviewer.py`): Conversational agent that asks ONE targeted question at a time to extract personal stories and develop the hook. Uses LiteLLM tool calls (`ask_question`, `show_thought`) so the frontend can render structured UI. Assesses sufficiency after each answer and does background research before triggering drafts.

**Draft Generator** (`drafting/generator.py`): Streams 3 drafts simultaneously over WebSocket via LiteLLM `create_draft` tool calls. Each draft is informed by: interview material, user's style preferences (from examples), learned patterns (from feedback history), and background research. Angles are task-appropriate.

**Synthesizer** (`drafting/synthesizer.py`): Generates 3 NEW refined drafts from highlight feedback. Annotates each previous draft with semantic XML tags (`<good>`, `<bad>`, `<custom_label>`) and streams 3 concurrent drafts via LiteLLM. Smart angle selection: keeps angles with more likes, replaces angles with more flags. Supports iterative rounds (highlight → synthesize → repeat).

**Bridge Client** (`bridge/`): Async httpx client wrapping Proof's localhost:9847 API. All edits go through suggestions (`POST /marks/suggest-replace`, etc.) and comments (`POST /marks/comment`). Always include `X-Agent-Id` header and `"by": "ai:proof-style"` in bodies. For full draft delivery, use `POST /rewrite`.

**Style Engine** (`style/`): Every Write Style Guide as composable, individually testable rules. Each rule returns `StyleViolation(rule_id, quote, replacement, explanation)`. Rule confidence adjusts based on accept/reject history.

**Learning Flywheel** (`learning/`): SQLite-backed storage for:
- Interview answers and extracted stories (reusable context)
- Highlighted favorites across drafts with custom labels (style signal)
- Drafts persisted per round (`Draft` model with `round` counter)
- User text edits tracked via `draft.edit` messages
- Accepted/rejected style suggestions (rule confidence)
- User-uploaded writing examples by category
- Derived voice/style preferences

**Examples** (`examples/`): Manages categorized writing samples (essays, newsletters, landing pages, etc.). Supports file upload (PDF, markdown, text). Used as few-shot examples for voice matching and style calibration.

## Proof Bridge API

Canonical reference: `EDITOR_DETAIL.md`. Key endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/windows` | GET | List open documents |
| `/state` | GET | Read document content, cursor, word count |
| `/marks/suggest-replace` | POST | Suggest replacing text |
| `/marks/suggest-insert` | POST | Suggest inserting after text |
| `/marks/suggest-delete` | POST | Suggest deleting text |
| `/rewrite` | POST | Bulk rewrite with automatic diff |
| `/marks/comment` | POST | Leave a comment on text |
| `/marks/reply` | POST | Reply to a comment thread |
| `/events/pending` | GET | Poll for user feedback events |
| `/presence` | POST | Set agent status in sidebar |

**Critical rules:**
- Never write markdown files directly — always use the bridge for provenance tracking
- Use `/state` `.content` (markdown) as source of truth, not `.plainText`
- For table edits, one cell at a time or `/rewrite` changes mode
- `"by": "ai:proof-style"` attributes edits in the provenance gutter

## Every Write Style Guide (Key Rules)

Full guide: `data/style_rules/`. Most impactful rules:

- **Title case** for headlines; sentence case everywhere else
- **Oxford comma** always (x, y, and z)
- **Em dash** (—) no spaces; max twice per paragraph
- **Active voice** preferred; flag passive constructions
- **Numbers**: spell out 1-9, numerals for 10+; numeral for percentages
- **Cut**: "actually," "very," "just" — typically deletable
- **Links**: 2-4 word hyperlink text; never "click here"
- **Companies** singular "it"; teams/people plural "they"
- **Fewer** for countable, **less** for quantities

## Build & Run Commands

```bash
# Backend
cd backend && uv sync
uv run python -m proof_editor          # Run the backend
uv run --frozen pytest                  # Run all tests
uv run --frozen pytest tests/test_style.py::test_oxford_comma -v  # Single test
uv run ruff check --fix && uv run ruff format  # Lint + format
uv run mypy src/                        # Type check

# Frontend
cd frontend && npm install
npm run dev                             # Dev server (Vite)
npm run build                           # Production build
npm run check                           # Svelte type checking
```

## WebSocket Protocol

The frontend ↔ backend communication uses WebSocket at `ws://localhost:8000/ws`.

The backend translates LiteLLM tool calls into typed WebSocket messages. The frontend renders each tool call as a specific UI component (thought block, chat message, draft panel, etc.).

```jsonc
// Client → Server
{"type": "task.select", "task_type": "essay", "topic": "..."}
{"type": "interview.answer", "answer": "..."}
{"type": "draft.highlight", "draft_index": 0, "start": 42, "end": 98, "sentiment": "like", "label": "insightful"}
{"type": "highlight.update", "draft_index": 0, "highlight_index": 1, "label": "too_formal"}
{"type": "highlight.remove", "draft_index": 0, "highlight_index": 2}
{"type": "draft.edit", "draft_index": 0, "content": "..."}
{"type": "draft.synthesize"}

// Server → Client (mapped from LiteLLM tool calls)
{"type": "thought", "assessment": "...", "missing": [...], "sufficient": false}
{"type": "interview.question", "question": "...", "context": "..."}
{"type": "search.result", "query": "...", "summary": "..."}
{"type": "draft.start", "draft_index": 0, "title": "...", "angle": "..."}
{"type": "draft.chunk", "draft_index": 0, "content": "...", "done": false}
{"type": "draft.complete", "draft_index": 0, "word_count": 452}
{"type": "status", "message": "Developing your hook..."}
```

### Synthesis XML Tag Convention

When synthesizing, each draft is annotated with highlights as semantic XML tags:

| sentiment | label | XML tag |
|---|---|---|
| like | (empty) | `<good>text</good>` |
| flag | (empty) | `<bad>text</bad>` |
| like | "insightful" | `<good_insightful>text</good_insightful>` |
| flag | "too_formal" | `<too_formal>text</too_formal>` |

The LLM is instructed to: incorporate `<good>` passages, rewrite/omit `<bad>` passages, and use custom labels as guidance.

### Frontend UI Mapping

| WebSocket message | Frontend component |
|---|---|
| `thought` | Collapsible orange "Thought" block (like Spiral) |
| `interview.question` | Chat bubble from AI |
| `interview.answer` (client) | Chat bubble from user |
| `search.result` | Inline context card |
| `draft.start` + `draft.chunk` | TipTap panel with streaming text (used for both initial drafts and synthesis) |
| `draft.highlight` (client) | Highlight popover (Like/Flag) + optional label |
| `highlight.update` (client) | Updates label on existing highlight via gear icon |
| `highlight.remove` (client) | Removes highlight via X button |
| `draft.edit` (client) | User's contenteditable text changes sent to backend |
| `draft.synthesize` (client) | Triggers 3 new drafts from highlight feedback |

## Style Rule Pattern

```python
class StyleViolation(BaseModel):
    rule_id: str
    quote: str          # exact text to find in document
    replacement: str    # suggested replacement
    explanation: str    # why this change improves the writing
    confidence: float   # 0.0-1.0, adjusted by learning flywheel
```

Rules are composable, independently testable, and their confidence is modified by the learning subsystem based on accept/reject history.
