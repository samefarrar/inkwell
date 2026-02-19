---
status: pending
priority: p2
issue_id: "006"
tags: [code-review, performance, database]
dependencies: []
---

# Missing Index on feedback.session_id

## Problem Statement

The `Feedback` model's `session_id` foreign key column does not have `index=True`, unlike every other model with a `session_id` FK (Draft, Highlight, InterviewMessage). Queries filtering feedback by session will do a full table scan.

## Findings

- **Flagged by**: Performance Oracle
- **File**: `backend/src/proof_editor/models/feedback.py` (lines 11-14)
- **Current code**: `sa_column=Column(Integer, ForeignKey("session.id", ondelete="CASCADE"), nullable=False)` — no `index=True`

## Proposed Solutions

### Option A: Add index=True (Recommended)
```python
session_id: int = Field(
    sa_column=Column(
        Integer,
        ForeignKey("session.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
)
```
- **Effort**: Small (1 line)

## Acceptance Criteria

- [ ] `feedback.session_id` has `index=True`
- [ ] DB schema recreated (schema version bump)
- [ ] Tests pass

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-18 | Created from code review | Performance reviewer flagged |
