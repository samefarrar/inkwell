# MVP Brainstorm — Proof Editor

**Date**: 2026-02-16
**Status**: Decided

## What We're Building

A single web app (no macOS Proof.app dependency) that is an AI writing partner. The user specifies a writing task, the AI interviews them one question at a time with visible reasoning, generates 3 drafts simultaneously in different angles, lets the user highlight favorites and flag problems across drafts, synthesizes a refined draft, and then provides a focused single-draft editing mode with inline style feedback.

The system compounds over time — every accepted/rejected suggestion, every highlighted favorite, and every uploaded writing example (e.g., Janan Ganesh articles in `inspo/`) feeds the learning flywheel.

## MVP Flow (5 Screens)

```
1. TASK SELECT  → Pick writing type (essay, review, newsletter, etc.) + topic
2. INTERVIEW    → Chat with AI. Visible "Thought" blocks show reasoning.
                  One question at a time. Sufficiency assessment after each answer.
3. THREE DRAFTS → 3 panels stream simultaneously (3 concurrent LLM calls).
                  Each panel is a TipTap editor — expandable, editable.
                  Labeled with angle name + word count.
4. HIGHLIGHT    → User highlights lines they like across all 3 drafts.
                  Flags sections to fix with notes.
                  Clicks "Synthesize" → AI merges favorites.
5. FOCUS        → "Focus on this" CTA on any draft → single full-width
                  TipTap editor with inline style suggestions, comments,
                  track-change UI. This IS the Proof-like editing experience.
```

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Architecture | Single web app (Svelte 5 + FastAPI) | No macOS dependency, self-contained |
| LLM client | LiteLLM from start | Unified tool use API, no migration later |
| Draft streaming | Simultaneous (3 concurrent calls) | Matches Spiral UX, core differentiator |
| Thought blocks | Visible from day one | Key differentiator, shows AI reasoning |
| Rich text editor | TipTap (ProseMirror) | Handles selection, highlights, suggestions, track changes |
| Style examples | Local folder (`inspo/`) | Backend reads on startup, no upload UI for MVP |
| Proof.app integration | Out of scope for MVP | Everything in our web UI |
| Web search | Built-in by model provider | No custom search infra |
| Cost optimization | Out of scope for MVP | Use best model (Claude), optimize later |
| App name | Decide later | Working name: proof_editor |

## MVP Scope

### In Scope
- Task selection (writing type + topic)
- Interview flow with visible thought blocks, one question at a time
- 3 simultaneous draft streams with angle labels and word counts
- Cross-draft highlighting (like/flag with notes)
- Draft synthesis from highlighted favorites
- "Focus on this" → single-draft editing with inline style suggestions
- Every Write Style Guide enforcement (key rules)
- Learning flywheel: store accepted/rejected suggestions, highlighted favorites
- Style examples from `inspo/` folder (Janan Ganesh articles)
- WebSocket communication (interview chat + draft streaming)

### Out of Scope
- macOS Proof.app bridge integration
- Cost optimization / cheap model routing
- Custom web search (use model provider built-in)
- File upload UI (articles go in `inspo/` manually)
- User accounts / authentication
- Deployment / hosting
- Mobile responsive design

## Tech Stack (Confirmed)

- **Backend**: Python 3.12+ / FastAPI / LiteLLM / SQLite + SQLModel
- **Frontend**: Svelte 5 (Runes) / TipTap (ProseMirror) / Vite
- **Real-time**: WebSockets
- **Package mgmt**: uv (never pip)
- **Linting**: ruff / mypy
- **Testing**: pytest + anyio

## Style Examples Strategy

Janan Ganesh articles will live in `inspo/`. On startup, the backend reads all files in `inspo/` and indexes them with basic metadata (filename as title, file content as text). These are injected as few-shot style examples in draft generation prompts. As the learning flywheel compounds, the system blends Ganesh-style patterns with the user's own accept/reject signals.

## Open Questions (Deferred)

1. **Interview question count** — Let the LLM decide sufficiency naturally (typically 2-4 questions). No hard limit for MVP.
2. **Draft angle selection** — LLM chooses task-appropriate angles. Could hard-code sensible defaults per task type if LLM choices are inconsistent.
3. **Highlight merging algorithm** — LLM-driven synthesis from highlighted text + flag notes. No algorithmic merging for MVP.
4. **Style rule confidence thresholds** — Start all rules at 1.0 confidence, decrease on rejection. Tune thresholds after real usage data.
