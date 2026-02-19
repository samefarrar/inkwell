---
status: pending
priority: p3
issue_id: "020"
tags: [code-review, backend, quality]
dependencies: []
---

# Magic string sentinels in FocusCommentMsg

## Problem Statement

`focus_handler.py` sends `id="none"` and `id="error"` as sentinel values for empty/error cases. These magic strings appear as visible comment cards in the sidebar. Cleaner: send `done=True` with empty fields, or handle in frontend.

**File:** `backend/src/proof_editor/agent/focus_handler.py`, lines 139-161

## Fix

For no-comments case, send only the done signal:
```python
await self.send(FocusCommentMsg(id="", quote="", start=0, end=0, comment="", done=True))
```
Frontend should check for empty comment and not render a card.

## Acceptance Criteria

- [ ] No magic string IDs in WS messages
- [ ] Empty comment case handled cleanly

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | |
