---
status: pending
priority: p2
issue_id: "025"
tags: [code-review, backend, performance, concurrency]
dependencies: []
---

# No concurrency guard on focus.chat — interleaved LLM responses

## Problem Statement

The WebSocket receive loop processes `focus.chat` messages sequentially via `await`, but a user who sends two chat messages before the first LLM response completes causes two concurrent `_call_llm` coroutines that write to the shared `self.messages` list and both call `self.send()`. The conversation history becomes corrupted with interleaved tool call results.

**File:** `backend/src/proof_editor/agent/focus_handler.py`

## Findings

- **Flagged by**: Performance Oracle (P0)
- The WebSocket receive loop calls `await handle_focus_chat(msg)` — but the LLM call is awaited inside that, freeing the event loop for the next WS message if the user sends one quickly
- Both coroutines write to `FocusAgent.messages` simultaneously

## Proposed Solutions

### Option A: asyncio.Lock on FocusHandler (Recommended)
```python
import asyncio

# In __init__:
self._chat_lock = asyncio.Lock()

# In handle_chat:
async def handle_chat(self, msg: FocusChat) -> None:
    if self._chat_lock.locked():
        await self.send(ErrorMessage(message="Still processing previous message"))
        return
    async with self._chat_lock:
        # ... existing logic
```
- **Pros**: Simple, prevents corruption
- **Effort**: Small
- **Risk**: None

## Acceptance Criteria

- [ ] Only one chat LLM call runs at a time per session
- [ ] User gets clear feedback if they send during processing

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Performance oracle flagged as P0 |
