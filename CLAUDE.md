# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Inkwell** is an AI writing partner — a web app (Svelte 5 + FastAPI) where the user specifies a writing task, the AI interviews them to extract real stories/insights/experiences, generates 3 drafts simultaneously in different angles, lets the user highlight favorites across drafts, synthesizes refined drafts, and then provides a focused single-draft editing mode with inline style suggestions.

The system compounds — every interaction (interview answers, highlighted favorites, style feedback, accepted/rejected suggestions, uploaded writing examples) feeds the learning flywheel to improve future output.

## Tech Stack

- **Backend**: Python 3.12+ / FastAPI / LiteLLM (unified LLM API with tool use)
- **Frontend**: Svelte 5 (Runes) / SvelteKit / TipTap (ProseMirror) / Vite 7
- **Real-time**: WebSockets (bi-directional for interview chat + draft streaming)
- **Storage**: SQLite + SQLModel (sessions, drafts, highlights, interview history, style preferences)
- **File storage**: Google Cloud Storage (voice recordings, PDF uploads)
- **Package management**: `uv` (backend, never pip), `npm` (frontend)
- **Linting**: `ruff check --fix && ruff format`
- **Type checking**: `mypy`
- **Testing**: `pytest` with `anyio` for async

## Build & Run Commands

```bash
# Both servers (recommended)
./dev start          # Start backend + frontend
./dev stop           # Stop both
./dev restart        # Restart both
./dev status         # Check running state
./dev logs           # Tail both logs
./dev logs backend   # Tail backend only

# Backend only
cd backend && uv sync
uv run python -m proof_editor                          # Run server (port 8000)
uv run --frozen pytest                                 # Run all tests
uv run --frozen pytest tests/test_websocket.py -v      # Single test file
uv run ruff check --fix && uv run ruff format          # Lint + format
uv run mypy src/                                       # Type check

# Frontend only
cd frontend && npm install
npm run dev                    # Dev server (port 5173)
npm run build                  # Production build
npm run check                  # Svelte type checking
```

## Architecture

```
inkwell/
├── backend/
│   ├── src/proof_editor/
│   │   ├── main.py              # FastAPI app, WebSocket handler, route mounting
│   │   ├── db.py                # SQLite engine + table creation
│   │   ├── storage.py           # GCS file storage (voice, PDFs)
│   │   ├── ws_types.py          # Pydantic models for all WS message types
│   │   ├── api/
│   │   │   ├── sessions.py      # REST: session CRUD + history
│   │   │   ├── styles.py        # REST: writing style CRUD
│   │   │   └── voice.py         # REST: voice transcription + PDF upload
│   │   ├── agent/
│   │   │   ├── orchestrator.py  # Main workflow state machine
│   │   │   └── interviewer.py   # Targeted questioning via LiteLLM tools
│   │   ├── drafting/
│   │   │   ├── generator.py     # 3 simultaneous draft generation
│   │   │   └── synthesizer.py   # Iterative synthesis from highlight feedback
│   │   ├── models/              # SQLModel database models
│   │   │   ├── session.py       # Writing sessions
│   │   │   ├── draft.py         # Drafts (with round tracking)
│   │   │   ├── highlight.py     # User highlights on drafts
│   │   │   ├── interview_message.py  # Interview chat history
│   │   │   ├── style.py         # Writing style preferences
│   │   │   ├── feedback.py      # Style suggestion feedback
│   │   │   └── preference.py    # User preferences
│   │   ├── style/               # Style guide rule engine
│   │   ├── learning/            # Feedback flywheel
│   │   └── examples/            # Writing sample management
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── config.ts            # API base URLs
│   │   │   ├── ws.svelte.ts         # WebSocket client (Svelte 5 runes)
│   │   │   ├── stream-buffer.svelte.ts  # Typewriter streaming effect
│   │   │   ├── audio-capture.svelte.ts  # Microphone audio capture
│   │   │   ├── transcription.svelte.ts  # Voice transcription client
│   │   │   ├── components/
│   │   │   │   ├── TaskSelector.svelte    # Home screen / task input card
│   │   │   │   ├── Interview.svelte       # Chat-style interview UI
│   │   │   │   ├── DraftComparison.svelte # 3-panel side-by-side drafts
│   │   │   │   ├── DraftPanel.svelte      # Single draft with highlighting
│   │   │   │   ├── Sidebar.svelte         # Session history + navigation
│   │   │   │   ├── StyleManager.svelte    # Style preferences list
│   │   │   │   ├── StyleEditor.svelte     # Style preference editor
│   │   │   │   └── VoiceButton.svelte     # Voice input button
│   │   │   └── stores/
│   │   │       ├── session.svelte.ts      # Session + interview state
│   │   │       ├── drafts.svelte.ts       # Draft content + highlights
│   │   │       └── styles.svelte.ts       # Writing style state
│   │   └── routes/
│   │       ├── +layout.svelte
│   │       ├── +page.svelte               # Main app shell
│   │       └── +page.ts
│   └── static/
│       └── pcm-recorder-processor.js      # AudioWorklet for voice capture
├── inspo/                   # Writing samples for voice matching
├── docs/
│   ├── brainstorms/
│   └── plans/
├── dev                      # Dev server manager script
├── EDITOR_DETAIL.md         # Proof bridge API reference (future scope)
└── CLAUDE.md
```

## Writing Partner Workflow

```
1. TASK       → User specifies: essay, newsletter, landing page, review, etc.
2. INTERVIEW  → AI asks ONE targeted question at a time:
                 → Shows visible "Thought" block (assessment, missing info, sufficiency)
                 → Asks the single most impactful question to fill the gap
                 → User answers (text or voice) → AI re-assesses
                 → Repeats until material is sufficient (typically 2-4 questions)
                 → AI does background research to supplement user info
3. DRAFT      → Generates 3 angles simultaneously via WebSocket
                 → Each draft has: title, angle label, word count
                 → Angles are task-appropriate
4. HIGHLIGHT  → User highlights lines they like across all 3 drafts
                 → Flags sections to fix with notes
                 → Adds custom labels (e.g. "too_formal")
                 → Can directly edit draft text
5. SYNTHESIZE → AI generates 3 NEW refined drafts from highlight feedback
                 → Highlights encoded as semantic XML tags in prompt
                 → Loop repeats: highlight → synthesize → 3 new drafts
6. FOCUS      → User selects one draft (coming soon)
7. FEEDBACK   → Inline editorial suggestions (coming soon)
```

## WebSocket Protocol

Frontend ↔ backend communication uses WebSocket at `ws://localhost:8000/ws`.

```jsonc
// Client → Server
{"type": "task.select", "task_type": "essay", "topic": "..."}
{"type": "interview.answer", "answer": "..."}
{"type": "draft.highlight", "draft_index": 0, "start": 42, "end": 98, "sentiment": "like", "label": "insightful"}
{"type": "highlight.update", "draft_index": 0, "highlight_index": 1, "label": "too_formal"}
{"type": "highlight.remove", "draft_index": 0, "highlight_index": 2}
{"type": "draft.edit", "draft_index": 0, "content": "..."}
{"type": "draft.synthesize"}
{"type": "session.resume", "session_id": 1}
{"type": "session.cancel"}

// Server → Client
{"type": "thought", "assessment": "...", "missing": [...], "sufficient": false}
{"type": "interview.question", "question": "...", "context": "..."}
{"type": "search.result", "query": "...", "summary": "..."}
{"type": "ready_to_draft", "summary": "...", "key_material": [...]}
{"type": "draft.start", "draft_index": 0, "title": "...", "angle": "..."}
{"type": "draft.chunk", "draft_index": 0, "content": "...", "done": false}
{"type": "draft.complete", "draft_index": 0, "word_count": 452}
{"type": "status", "message": "Developing your hook..."}
{"type": "error", "message": "..."}
```

### Synthesis XML Tag Convention

When synthesizing, each draft is annotated with highlights as semantic XML tags:

| sentiment | label | XML tag |
|---|---|---|
| like | (empty) | `<good>text</good>` |
| flag | (empty) | `<bad>text</bad>` |
| like | "insightful" | `<good_insightful>text</good_insightful>` |
| flag | "too_formal" | `<too_formal>text</too_formal>` |

## REST API Endpoints

| Path | Method | Purpose |
|---|---|---|
| `/health` | GET | Health check |
| `/api/sessions` | GET | List all sessions |
| `/api/sessions/{id}` | GET | Get session with interview, drafts, highlights |
| `/api/voice/transcribe` | POST | Transcribe audio (multipart upload) |
| `/api/voice/upload-pdf` | POST | Upload PDF to GCS |
| `/api/styles` | GET | List writing styles |
| `/api/styles` | POST | Create writing style |
| `/api/styles/{id}` | GET/PUT/DELETE | Style CRUD |

## Key Design Decisions

- **Svelte 5 Runes**: All stores use `$state()` and `$derived()` — no legacy `writable()`/`readable()` stores
- **WebSocket for workflow, REST for CRUD**: The interview/draft loop is real-time over WS; sessions, styles, and file uploads use REST
- **LiteLLM tool calls**: The AI agent uses structured tool calls (`ask_question`, `show_thought`, `create_draft`) that the backend translates into typed WS messages
- **Round-based drafts**: Each synthesis cycle creates a new round. Drafts are stored with a `round` counter for history navigation
- **Session persistence**: Full session state (interview messages, drafts per round, highlights) is persisted to SQLite and can be resumed

## Server Environment

- **Backend**: port 8300 (prod), 8301 (staging), dev on 8000
- **Frontend**: port 8310 (prod), 8311 (staging), dev on 5173
- **Dev port range**: 8322–8399
- See `~/.claude/rules/server.md` for full Hetzner server config
