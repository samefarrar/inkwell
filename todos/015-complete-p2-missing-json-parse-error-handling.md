---
status: pending
priority: p2
issue_id: "015"
tags: [code-review, backend, error-handling]
dependencies: []
---

# Missing JSON parse error handling in FocusAgent._call_llm

## Problem Statement

`focus_agent.py` calls `json.loads(tc.function.arguments)` without try/except. `editorial.py` wraps the same pattern in `try/except (json.JSONDecodeError, KeyError)`. A malformed tool call from the LLM will crash the coroutine silently.

**File:** `backend/src/proof_editor/agent/focus_agent.py`, line 162

## Fix

Wrap in try/except matching the pattern in `editorial.py`.

## Acceptance Criteria

- [ ] `json.loads` in focus_agent._call_llm wrapped in try/except

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | |
