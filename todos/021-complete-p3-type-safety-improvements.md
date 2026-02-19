---
status: pending
priority: p3
issue_id: "021"
tags: [code-review, backend, type-safety]
dependencies: []
---

# Type safety improvements

## Problem Statement

Several typing gaps across the focus edit feature:

1. `send` typed as `Any` in FocusHandler, FocusAgent, Orchestrator — should be a Protocol
2. `action` and `feedback_type` on Feedback model are `str | None` — should be `Literal`
3. `drafts` passed as `list[dict[str, Any]]` — should be a TypedDict
4. Silent `(0, 0)` fallback in `_find_quote_position` — should log a warning

## Acceptance Criteria

- [ ] `send` has a typed Protocol or Callable signature
- [ ] Feedback model fields use Literal types
- [ ] Quote position fallback logs a warning

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Low priority, doesn't affect runtime |
