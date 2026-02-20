---
status: pending
priority: p2
issue_id: "028"
tags: [code-review, backend, state-management]
dependencies: []
---

# FocusHandler re-entry without cleanup — stale results sent to new session

## Problem Statement

`handle_focus_enter` allows re-entry from `"focused"` state (switching drafts). The old `FocusHandler` is silently replaced, but any running `_run_editorial_analysis` coroutine from the old handler continues to execute and sends stale `FocusCommentMsg` events from draft A while the user is viewing draft B.

**File:** `backend/src/proof_editor/agent/orchestrator.py`, lines 486-502

## Fix

Add a `_cancelled` flag to `FocusHandler`. Set it before replacing the handler.

```python
# In handle_focus_enter:
if self._focus_handler is not None:
    self._focus_handler.cancel()
self._focus_handler = FocusHandler(...)
```

## Acceptance Criteria

- [ ] Old handler's in-flight coroutines do not send messages after replacement
- [ ] Cancellation flag checked before every `send` in FocusHandler

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Security + architecture reviewers |
