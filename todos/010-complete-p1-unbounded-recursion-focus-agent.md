---
status: pending
priority: p1
issue_id: "010"
tags: [code-review, security, performance]
dependencies: []
---

# Unbounded recursion in FocusAgent._call_llm

## Problem Statement

`FocusAgent._call_llm()` calls itself recursively when the LLM uses `web_search` without `send_response`. If the LLM keeps calling `web_search` in a loop, this will recurse until stack overflow, crashing the WebSocket handler and potentially the server.

**File:** `backend/src/proof_editor/agent/focus_agent.py`, lines 237-238

```python
if needs_continuation and not has_response:
    await self._call_llm()  # unbounded recursion
```

## Findings

- No depth guard on recursive call
- LLM tool calls are non-deterministic — can't guarantee `send_response` is ever called
- Same issue: `suggest_edit` branch does NOT set `needs_continuation = True`, so if LLM only calls `suggest_edit`, no follow-up text response is sent to the user

## Proposed Solutions

### Option A: Add depth parameter with hard cap (Recommended)
```python
MAX_CONTINUATION_DEPTH = 5

async def _call_llm(self, depth: int = 0) -> None:
    if depth >= MAX_CONTINUATION_DEPTH:
        await self.send(FocusChatResponse(content="I reached my search limit.", done=True))
        return
    ...
    if needs_continuation and not has_response:
        await self._call_llm(depth + 1)
```
- Pros: Simple, preserves existing pattern
- Cons: Still recursive (but bounded)
- Effort: Small
- Risk: Low

### Option B: Convert to iterative loop
```python
async def _call_llm(self) -> None:
    for _ in range(MAX_ITERATIONS):
        response = await self._single_llm_call()
        if not response.needs_continuation:
            break
```
- Pros: No recursion at all
- Cons: More refactoring
- Effort: Medium
- Risk: Low

## Recommended Action

Option A — simplest fix that addresses the issue.

Also: add `needs_continuation = True` after the `suggest_edit` branch so the LLM gets a follow-up turn to explain the suggestion.

## Technical Details

- **Affected files:** `backend/src/proof_editor/agent/focus_agent.py`
- **Components:** FocusAgent._call_llm

## Acceptance Criteria

- [ ] Recursion bounded to MAX_CONTINUATION_DEPTH (e.g. 5)
- [ ] `suggest_edit` sets `needs_continuation = True`
- [ ] Graceful message sent to user when limit reached

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Python reviewer flagged as blocking |

## Resources

- PR: focus-edit branch
