---
title: "feat: Focus Edit Mode with Agent Sidebar"
type: feat
status: active
date: 2026-02-19
deepened: 2026-02-19
---

# Focus Edit Mode with Agent Sidebar

## Enhancement Summary

**Deepened on:** 2026-02-19
**Review agents used:** architecture-strategist, code-simplicity-reviewer, kieran-typescript-reviewer, kieran-python-reviewer, performance-oracle, security-sentinel, pattern-recognition-specialist, julik-frontend-races-reviewer, agent-native-reviewer, framework-docs-researcher, best-practices-researcher

### Key Improvements
1. **Extract FocusHandler class** from orchestrator to prevent god-object growth (481→700+ LOC)
2. **Use ProseMirror Decorations** instead of TipTap Marks for suggestions — view-level overlays don't modify the document model
3. **Add character offsets** (`start`/`end`) to suggestions — quote-only anchoring is fragile after edits
4. **Editor-ready queue** + generation counter to prevent race conditions with WS messages arriving before TipTap mounts
5. **Simplify for MVP**: collapse rules into single `engine.py`, drop `FocusContentUpdate` (debounced re-analysis), drop `confidence` field, drop `FocusAnalysisDone` (use `done` flag on last message)
6. **Add `focus.exit` message** for clean state transition back to drafts
7. **Input validation**: max_length on all WS string fields, label regex validation
8. **Add `leaveFocus()` cleanup** method on focus store to prevent memory leaks

### New Considerations Discovered
- LLM prompt injection risk via focus agent chat — user content must go in user-role messages, not system prompt
- Cross-store dependency (focus→drafts) — pass draft content via component props, not store imports
- IME composition check — don't apply decorations while `editor.view.composing` is true
- Feedback model needs `action` (accept/reject/dismiss) and `feedback_type` (suggestion/comment) fields

## Overview

Build the focus editing screen — the final step of the Inkwell writing workflow. When a user clicks "Focus on this" on any draft, they enter a full-width TipTap editor with an AI agent sidebar that provides live editorial feedback: inline style suggestions (accept/reject), structural comments (dismiss), agent chat (back-and-forth with the AI), and web search. Inspired by Proof.app's collaboration model (see `screenshots/proof_ui.png`) and the side-writer layout (see `screenshots/ui_side_writer.png`).

## Problem Statement

The focus edit placeholder (`<p>Focus editing mode coming soon.</p>`) is the last unbuilt screen in the MVP workflow. Without it, users cannot refine a single draft with AI assistance after the highlight/synthesize loop. The entire value proposition — a writing partner that compounds over time — depends on this screen being where suggestions are accepted/rejected and the learning flywheel turns.

## Proposed Solution

A two-panel layout: **TipTap editor** (left, ~70%) + **Agent sidebar** (right, ~30%) with three tabs: Suggestions, Comments, and Chat.

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  Inkwell  │ session title                          │ word count  │
├───────────┴──────────────────────────────┬───────────────────────┤
│                                          │ Suggestions │ Comments│ Chat │
│                                          ├───────────────────────┤
│   Full-width TipTap editor               │                       │
│                                          │  - Style suggestion 1  │
│   "The Future of Writing"                │    "very" → (remove)   │
│                                          │    [Accept] [Reject]   │
│   Writing has always been a deeply       │                       │
│   human act. But as AI becomes a         │  - Style suggestion 2  │
│   collaborator, we need tools that       │    passive → active    │
│   preserve transparency about who        │    [Accept] [Reject]   │
│   wrote what.                            │                       │
│                                          │  - Editorial comment   │
│   [green underline: suggestion]          │    "Consider adding..." │
│   [yellow highlight: comment anchor]     │    [Dismiss]           │
│                                          │                       │
│                                          ├───────────────────────┤
│                                          │ ▸ Analyzing draft...   │
├──────────────────────────────────────────┴───────────────────────┤
│  Back to drafts                                    850 words     │
└──────────────────────────────────────────────────────────────────┘
```

### Two Types of AI Feedback (from Proof model)

1. **Inline Suggestions** — deterministic style rule violations. Green underline (insert), red strikethrough (delete). Accept applies the replacement; reject dismisses. Comes from the rule engine (<100ms).

2. **Editorial Comments** — LLM-generated structural feedback anchored to specific text. Categories: structure, voice, clarity, impact. Advisory only — user reads and edits manually. Comes from LLM pass (2-3s).

### Agent Chat (new, beyond original plan)

A chat interface in the sidebar where the user can ask the AI about the draft:
- "Make the intro more punchy"
- "Research the latest stats on AI writing tools"
- "What's missing from this argument?"

The AI sees the current editor content + interview context + style preferences. It can:
- Send text responses
- Trigger web searches (results appear inline in chat)
- Propose specific edits (which appear as inline suggestions in the editor)

## Technical Approach

### Architecture

```
Frontend                          Backend
────────                          ───────
FocusEditor.svelte ◄──WS──► Orchestrator → FocusHandler
  └─ FocusTipTap.svelte              ├─ style/engine.py (deterministic rules)
  │   └─ ProseMirror Decorations     ├─ style/editorial.py (LLM comments)
  └─ FocusSidebar.svelte             └─ agent/focus_agent.py (chat + search)
      └─ tabs: Suggestions/Comments/Chat
focus.svelte.ts (store)
```

### Research Insights — Architecture

**Extract FocusHandler** (from architecture + python reviewers): The orchestrator is already 481 lines. Adding 4+ focus handlers would push it past 700. Extract a `FocusHandler` class (matching the `Interviewer` pattern) that the orchestrator delegates to.

**ProseMirror Decorations over TipTap Marks** (from performance + simplicity reviewers): TipTap Marks modify the document model. ProseMirror Decorations are view-level overlays — they don't touch the document, making them ideal for transient suggestions that will be accepted/rejected. Use `DecorationSet` with `Decoration.inline()`.

**Character offsets** (from performance + frontend-races reviewers): Quote-only anchoring breaks after edits shift positions. The style engine should return `start`/`end` character offsets. Use `quote` for validation (confirm the text at that offset matches), fall back to `text.indexOf(quote)` if offsets are stale.

**Editor-ready queue** (from frontend-races reviewer): WS messages may arrive before TipTap mounts. Queue suggestions/comments until `editorReady` flag is true, then flush.

### Implementation Phases

#### Phase 1: Frontend Shell — TipTap Editor + Sidebar Layout

Get the screen rendering with the selected draft loaded in TipTap. No backend integration yet.

**Frontend tasks:**

- [ ] Create `frontend/src/lib/stores/focus.svelte.ts` — Focus mode store
  - `selectedDraftIndex: number` — which draft was selected
  - `content: string` — current editor content (synced with TipTap)
  - `suggestions: FocusSuggestion[]` — pending inline suggestions
  - `comments: FocusComment[]` — pending editorial comments
  - `chatMessages: FocusChatMessage[]` — agent chat history
  - `analysisGeneration: number` — incremented each analysis pass (for stale response detection)
  - `analyzing: boolean` — derived from `analysisGeneration` tracking
  - `editorReady: boolean` — gate for applying decorations (prevents race with TipTap mount)
  - `pendingQueue: Array` — queued messages received before editor mount
  - `enterFocus(draftIndex: number, draftContent: string)` — **value-copy** draft content (no cross-store dependency), trigger analysis
  - `leaveFocus()` — full cleanup: clear suggestions, comments, chat, reset state
  - `acceptSuggestion(id: string)` / `rejectSuggestion(id: string)`
  - `dismissComment(id: string)`
  - `addChatMessage(role, content)`
  - `flushPendingQueue()` — called when `editorReady` becomes true

- [ ] Create `frontend/src/lib/components/FocusEditor.svelte` — Main focus screen
  - Two-panel layout: editor (left) + sidebar (right)
  - Top bar: "Back to drafts" link, session title, word count
  - Bottom bar: word count, analysis status indicator
  - CSS: `--paper` background on editor, `--chrome` on sidebar
  - Max content width ~680px (centered in the editor panel) for readable line lengths

- [ ] Create `frontend/src/lib/components/FocusTipTap.svelte` — TipTap editor wrapper
  - Initialize TipTap v3 with: `StarterKit`, `Highlight`
  - Use `$effect` + `createSubscriber` pattern for reactive TipTap updates
  - Load content from `focus.content` on mount, set `focus.editorReady = true` after mount
  - Minimal toolbar: bold, italic, H1/H2/H3, bullet list, ordered list, link
  - Sync content changes back to store via `onTransaction` (debounced)
  - Font: Newsreader serif, `--ink` color, `--paper` background
  - Phase 2: ProseMirror `DecorationSet` for suggestions (green underline) and comments (yellow highlight) — NOT TipTap Marks
  - Check `editor.view.composing` before applying decorations (IME safety)

- [ ] Create `frontend/src/lib/components/FocusSidebar.svelte` — Sidebar shell
  - Three tabs: Suggestions (count badge), Comments (count badge), Chat
  - Tab switching with active indicator
  - CSS: `--chrome` background, scrollable content area

- [ ] Wire into page routes — replace the focus placeholder in both:
  - `frontend/src/routes/(app)/session/new/+page.svelte`
  - `frontend/src/routes/(app)/session/[id]/+page.svelte`
  - Import and render `<FocusEditor />` when `session.screen === 'focus'`

- [ ] Wire `goToFocus()` to populate the focus store
  - `DraftComparison.svelte`'s `handleFocus(draftIndex)` should: read `drafts.drafts[draftIndex].content`, then call `focus.enterFocus(draftIndex, content)` (value-copy, no cross-store import in focus store), then `session.goToFocus()`

**Success criteria:** Clicking "Focus on this" renders a TipTap editor with the draft content and an empty sidebar with 3 tabs. User can edit text. "Back to drafts" calls `focus.leaveFocus()` and returns to highlighting. No backend calls yet.

#### Phase 2: Backend Style Engine + WS Messages

Build the deterministic style rule engine and wire it to the frontend via WebSocket.

**Backend tasks:**

- [ ] Add focus mode WS message types to `backend/src/proof_editor/ws_types.py`:
  ```python
  # Client → Server (3 types)
  class FocusEnter(BaseModel):
      type: Literal["focus.enter"] = "focus.enter"
      draft_index: int

  class FocusExit(BaseModel):
      type: Literal["focus.exit"] = "focus.exit"

  class FocusChat(BaseModel):
      type: Literal["focus.chat"] = "focus.chat"
      message: str = Field(max_length=5000)

  class FocusFeedback(BaseModel):
      type: Literal["focus.feedback"] = "focus.feedback"
      id: str
      action: Literal["accept", "reject", "dismiss"]

  # Server → Client (4 types — reuse existing SearchResult for web search)
  class FocusSuggestion(BaseModel):
      type: Literal["focus.suggestion"] = "focus.suggestion"
      id: str
      quote: str        # exact text to match (validation)
      start: int        # character offset start
      end: int          # character offset end
      replacement: str  # what to replace it with ("" for deletion)
      explanation: str
      rule_id: str      # rule name or "agent" for chat-suggested edits

  class FocusComment(BaseModel):
      type: Literal["focus.comment"] = "focus.comment"
      id: str
      quote: str        # exact text anchor
      start: int
      end: int
      comment: str
      done: bool = False  # True on last comment (replaces FocusAnalysisDone)

  class FocusChatResponse(BaseModel):
      type: Literal["focus.chat_response"] = "focus.chat_response"
      content: str
      done: bool
  # Reuse existing SearchResultMessage for focus.search_result
  # Dropped: FocusContentUpdate (no debounced re-analysis for MVP)
  # Dropped: FocusAnalysisDone (done flag on last FocusComment)
  # Dropped: confidence field (meaningless for regex rules)
  ```

- [ ] Create `backend/src/proof_editor/style/engine.py` — Style rule engine (all rules in one file)
  - `analyze(text: str) -> list[StyleViolation]`
  - Pre-compiled regex patterns at module level
  - Returns violations with `start`/`end` character offsets + `quote` for validation
  - Each violation: `id` (uuid), `quote`, `start`, `end`, `replacement`, `explanation`, `rule_id`
  - Rules: filler words, passive voice, Oxford comma — all in one file (no `rules/` directory)
  - Content hashing to skip redundant analysis on identical text

- [ ] Create `backend/src/proof_editor/agent/focus_handler.py` — FocusHandler class (extracted from orchestrator)
  - `__init__(self, send, session_state)` — takes send callback and session state reference
  - `handle_enter(msg: FocusEnter)` — set state to "focused", run style engine, kick off editorial LLM
  - `handle_exit(msg: FocusExit)` — clean up, set state back to "highlighting"
  - `handle_feedback(msg: FocusFeedback)` — persist to Feedback model with `action` + `feedback_type` fields
  - `handle_chat(msg: FocusChat)` — delegate to focus_agent (Phase 4)
  - Matches existing `Interviewer` class extraction pattern

- [ ] Add thin orchestrator delegation in `backend/src/proof_editor/agent/orchestrator.py`:
  - Create `FocusHandler` instance on `focus.enter`
  - Route `focus.*` messages to handler
  - Wire into main message dispatch

- [ ] Update Feedback model in `backend/src/proof_editor/models/feedback.py`:
  - Add `action: str` field (accept/reject/dismiss)
  - Add `feedback_type: str` field (suggestion/comment)

- [ ] Update `backend/src/proof_editor/main.py` WebSocket handler to route new message types

**Frontend tasks:**

- [ ] Add focus message types to `frontend/src/lib/ws.svelte.ts` (ServerMessage + ClientMessage unions)
  - Add exhaustive switch default in ws-handler.ts: `default: const _exhaustive: never = msg;`

- [ ] Add focus message handling to `frontend/src/lib/ws-handler.ts`:
  - Guard all focus messages: `if (session.screen !== 'focus') return;`
  - `focus.suggestion` → queue if `!focus.editorReady`, else `focus.addSuggestion(data)`
  - `focus.comment` → queue if `!focus.editorReady`, else `focus.addComment(data)`
  - `focus.comment` with `done: true` → `focus.analyzing = false`
  - `focus.chat_response` → append to chat messages
  - Reuse existing `search.result` handler for web search results in chat

- [ ] Create ProseMirror Decoration plugin for suggestions:
  - `SuggestionPlugin` — uses `DecorationSet` with `Decoration.inline()` positioned via `start`/`end` offsets
  - Green underline CSS class for insertions, red strikethrough for deletions
  - Validate offset text matches `quote`, fall back to `text.indexOf(quote)` if stale
  - On click: sidebar scrolls to and highlights the corresponding suggestion card
  - Accept: `editor.chain().deleteRange({from: start, to: end}).insertContentAt(start, replacement).run()`, remove decoration, send `focus.feedback` (accept) via WS
  - Reject: remove decoration, send `focus.feedback` (reject) via WS
  - Do NOT apply decorations while `editor.view.composing` (IME safety)

- [ ] Build `SuggestionsTab` in sidebar (inline in FocusSidebar, no separate component):
  - List of pending suggestions with quote snippet, rule name, [Accept] [Reject] buttons
  - Count badge on tab header
  - Click item → scroll editor to the suggestion position

- [ ] Wire `focus.enter` — when entering focus mode, send `focus.enter` message to backend

**Success criteria:** Entering focus mode triggers style analysis. Filler words, passive voice, and Oxford comma violations appear as inline suggestions (ProseMirror Decorations). User can accept/reject. Feedback persists to DB.

#### Phase 3: LLM Editorial Comments

Add the LLM-powered editorial comment pass.

**Backend tasks:**

- [ ] Create `backend/src/proof_editor/style/editorial.py` — LLM editorial comments (renamed from editor.py to avoid confusion)
  - `generate_comments(text: str, interview_context: str) -> AsyncGenerator[EditorialComment]`
  - LiteLLM call with system prompt: "You are a senior editor. Read this draft and leave 3-5 editorial comments focused on structure, clarity, voice, and impact — not grammar. Anchor each comment to a specific quote."
  - Tool call pattern (like interviewer): `leave_comment(quote, comment)` tool
  - Streams comments as they arrive (each tool call = one comment sent immediately)
  - Last comment sent with `done: True` flag
  - Uses interview context to verify draft used user's stories
  - User content goes in user-role message (not system prompt) to mitigate prompt injection

- [ ] Wire into orchestrator: after style engine runs, kick off editorial LLM pass
  - Style suggestions stream immediately (instant)
  - Editorial comments stream after (2-3s latency)
  - Send `focus.analysis_done` when both complete

**Frontend tasks:**

- [ ] Add comment Decorations to ProseMirror plugin — subtle yellow highlight via `Decoration.inline()` with `start`/`end` offsets
  - Click scrolls to comment card in sidebar
  - Dismiss removes decoration, sends `focus.feedback` (dismiss)

- [ ] Build `CommentsTab` in sidebar (inline in FocusSidebar):
  - List of editorial comments with quote snippet, comment preview
  - Click → scroll to commented text in editor
  - [Dismiss] button per comment

**Success criteria:** After entering focus mode, 3-5 editorial comments appear after a brief delay. Comments are anchored to specific text via decorations. User can dismiss.

#### Phase 4: Agent Chat + Web Search

Add the interactive chat in the sidebar — the user can converse with the AI about their draft.

**Backend tasks:**

- [ ] Create `backend/src/proof_editor/agent/focus_agent.py` — Focus chat agent
  - LiteLLM tool-call pattern (same as interviewer)
  - System prompt: "You are an editorial collaborator working on this draft. You can see the current text, the interview context, and the user's style preferences. Help them improve their writing."
  - Tools:
    - `send_response(text)` — send a chat message
    - `suggest_edit(quote, replacement, explanation)` — create an inline suggestion
    - `web_search(query)` — search the web for information
  - Maintains conversation history for the focus session
  - Has access to: current editor content, interview summary, key material, style preferences

- [ ] Wire into orchestrator:
  - `handle_focus_chat(msg: FocusChat)` — pass to focus agent, stream response
  - Responses stream as `focus.chat_response` chunks
  - Search results sent as `focus.search_result`
  - Edit suggestions sent as `focus.suggestion` (same as style engine ones, but with `rule_id: "agent"`)

**Frontend tasks:**

- [ ] Build `ChatTab` in sidebar:
  - Chat message list (user messages + AI responses)
  - Text input at bottom with send button
  - AI responses stream with typewriter effect (reuse StreamBuffer)
  - Search results render inline in chat (query + summary)
  - Agent-suggested edits appear as suggestions in the editor AND as a chat message ("I've suggested an edit on '...'")

- [ ] Wire `focus.chat` — send user chat messages to backend via WS

**Success criteria:** User can chat with the AI about their draft. AI can suggest edits (which appear inline) and search the web. Conversation flows naturally.

## Alternative Approaches Considered

1. **REST endpoint instead of WS for analysis** — Rejected. The existing WS infrastructure is well-suited for streaming suggestions/comments incrementally. REST would require polling or SSE.

2. **Separate TipTap Collaboration extension for suggestions** — Rejected for MVP. Custom marks with manual positioning are simpler. Collaboration extension adds complexity for multi-user editing we don't need yet.

3. **Category filter pills (grammar, spelling, style, etc.)** — Rejected per original plan. The two-type split (Suggestions vs Comments) matches how human editors work. No need for granular categorization.

4. **Re-run editorial comments on every edit** — Rejected. Too expensive. Style engine re-runs on edits (instant, deterministic). Editorial comments only run on initial analysis or explicit user request via chat.

## Acceptance Criteria

### Functional Requirements

- [ ] "Focus on this" transitions from draft comparison to TipTap editor + sidebar
- [ ] TipTap loads the selected draft content, is fully editable
- [ ] Style engine detects filler words, passive voice, Oxford comma violations
- [ ] Suggestions appear inline (ProseMirror Decorations: green underline / red strikethrough) and in sidebar
- [ ] Accept replaces text, reject dismisses — both persist feedback to DB (with action + feedback_type)
- [ ] Editorial comments appear as yellow highlight decorations
- [ ] Comments show in sidebar, clicking scrolls to anchor in editor
- [ ] Dismiss removes comment and persists feedback
- [ ] Agent chat allows conversational interaction about the draft
- [ ] AI can suggest edits via chat (appear as inline suggestions with `rule_id: "agent"`)
- [ ] AI can web search and show results in chat
- [ ] Word count updates in real-time
- [ ] "Back to drafts" calls `leaveFocus()` (cleanup) and returns to highlighting screen
- [ ] `focus.exit` message sent to backend on exit

### Non-Functional Requirements

- [ ] Style engine runs in <100ms
- [ ] Editorial comments arrive within 5s of entering focus mode
- [ ] Chat responses begin streaming within 1s
- [ ] Editor feels responsive at all times (no blocking during analysis)
- [ ] Follows existing design system (paper/chrome/ink/accent variables)

## Dependencies & Prerequisites

- TipTap v3 packages already installed (`@tiptap/core`, `@tiptap/starter-kit`, `@tiptap/extension-highlight`, `@tiptap/pm`)
- WebSocket infrastructure fully functional
- `Feedback` model already defined in DB schema
- `goToFocus()` already exists in session store
- Focus screen placeholder already exists in both page routes
- Orchestrator has "focused" state defined (just no handler)

## References & Research

### Internal References

- Original plan Phase 5: `docs/plans/2026-02-16-feat-mvp-ai-writing-partner-plan.md:341-443`
- Brainstorm: `docs/brainstorms/2026-02-16-mvp-brainstorm.md`
- Orchestrator: `backend/src/proof_editor/agent/orchestrator.py`
- WS types: `backend/src/proof_editor/ws_types.py`
- WS handler: `frontend/src/lib/ws-handler.ts`
- Session store: `frontend/src/lib/stores/session.svelte.ts`
- Drafts store: `frontend/src/lib/stores/drafts.svelte.ts`
- Feedback model: `backend/src/proof_editor/models/feedback.py`
- Design system: `frontend/src/routes/+layout.svelte` (CSS variables)
- Proof UI reference: `screenshots/proof_ui.png`
- Side-writer reference: `screenshots/ui_side_writer.png`
