---
status: pending
priority: p2
issue_id: "017"
tags: [code-review, performance, backend]
dependencies: []
---

# Style engine cache has no eviction — memory leak

## Problem Statement

`engine.py` uses a module-level `_cache: dict[str, list[StyleViolation]]` with no size limit or eviction. Long-running server will accumulate entries for every unique document analyzed.

**File:** `backend/src/proof_editor/style/engine.py`, lines 40-41

## Fix

Use `functools.lru_cache(maxsize=256)` on the `analyze` function, or add a simple size check:
```python
if len(_cache) > 256:
    _cache.clear()
```

## Acceptance Criteria

- [ ] Cache has bounded size with eviction

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | |
