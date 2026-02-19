---
status: pending
priority: p1
issue_id: "024"
tags: [code-review, security, backend]
dependencies: []
---

# Internal exception messages forwarded to client

## Problem Statement

Raw Python exception messages are sent to the WebSocket client in error paths. LiteLLM, HTTP client, and database exceptions may contain API keys, internal hostnames, stack traces, and configuration values.

**Files:**
- `backend/src/proof_editor/agent/focus_handler.py`, lines 150-161
- `backend/src/proof_editor/agent/focus_agent.py`, lines 144-150

```python
# focus_handler.py
comment=f"Could not generate editorial comments: {e}"  # leaks exception

# focus_agent.py
content=f"Sorry, I encountered an error: {e}"  # leaks exception
```

## Findings

- **Flagged by**: Security Sentinel (F-2, HIGH)
- Exception messages from LiteLLM often contain API error responses with provider details
- A user who intentionally triggers errors (very long input, bad characters) receives this verbatim

## Proposed Solutions

### Option A: Static user-facing messages (Recommended)
```python
# focus_handler.py
except Exception as e:
    logger.error("Editorial analysis failed: %s", e, exc_info=True)
    await self.send(FocusCommentMsg(
        id="error", quote="", start=0, end=0,
        comment="Editorial analysis is temporarily unavailable.",
        done=True,
    ))

# focus_agent.py
except Exception as e:
    logger.error("Focus agent LLM call failed: %s", e, exc_info=True)
    await self.send(FocusChatResponse(
        content="I'm having trouble responding right now. Please try again.",
        done=True,
    ))
```
- **Pros**: Zero risk, 3-line change
- **Effort**: Small
- **Risk**: None

## Acceptance Criteria

- [ ] No `f"...{e}"` patterns in any user-facing message
- [ ] Full exception logged server-side with `exc_info=True`
- [ ] User sees static, non-leaking error message

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Security sentinel flagged as HIGH |
