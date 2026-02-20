---
status: pending
priority: p2
issue_id: "029"
tags: [code-review, security, backend]
dependencies: []
---

# No length limits on LLM-bound user input

## Problem Statement

`FocusChat.message` has no `max_length` constraint. A user can send a WebSocket message with hundreds of thousands of characters, causing LLM API cost amplification and provider-side errors that may be leaked (see todo 024).

**File:** `backend/src/proof_editor/ws_types.py`

## Fix

```python
from pydantic import Field

class FocusChat(BaseModel):
    type: Literal["focus.chat"] = "focus.chat"
    message: str = Field(max_length=4000)
```

Also truncate `draft_content` before LLM calls:
```python
MAX_DRAFT_CHARS = 50_000
plain_text = plain_text[:MAX_DRAFT_CHARS]
```

## Acceptance Criteria

- [ ] `FocusChat.message` has `max_length=4000`
- [ ] Draft content truncated before LLM context

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Security sentinel flagged |
