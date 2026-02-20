---
status: pending
priority: p1
issue_id: "012"
tags: [code-review, backend, data-integrity]
dependencies: []
---

# Wrong feedback_type derivation in FocusHandler.handle_feedback

## Problem Statement

`handle_feedback` derives `feedback_type` from the `action` field alone, but this is semantically wrong. `dismiss` only applies to comments, but `accept`/`reject` apply to both suggestions AND comments. Every accept/reject is saved as `feedback_type = "suggestion"` even if it was a comment.

**File:** `backend/src/proof_editor/agent/focus_handler.py`, lines 69-70

```python
feedback_type = "comment" if msg.action == "dismiss" else "suggestion"
```

## Findings

- `FocusFeedbackMsg` has `id` and `action` but no `target_type` field
- The `id` field is the suggestion/comment UUID — could be used to look up the type
- This corrupts the feedback learning data, undermining the flywheel

## Proposed Solutions

### Option A: Add feedback_type to FocusFeedbackMsg (Recommended)
Add `feedback_type: Literal["suggestion", "comment"]` to the WS message so the frontend explicitly tells the backend what it's acting on.
- Pros: Explicit, no guessing
- Cons: Requires frontend change too
- Effort: Small
- Risk: Low

### Option B: Derive from action mapping
Map dismiss → comment, accept/reject → suggestion. This is the current logic but it's wrong for comment accept/reject if that ever becomes a feature.
- Pros: No WS change
- Cons: Semantically fragile
- Effort: Small
- Risk: Medium (will break if comments ever get accept/reject)

## Technical Details

- **Affected files:** `backend/src/proof_editor/agent/focus_handler.py`, `backend/src/proof_editor/ws_types.py`, `frontend/src/lib/ws.svelte.ts`, `frontend/src/lib/components/FocusSidebar.svelte`

## Acceptance Criteria

- [ ] Feedback records correctly identify whether they target a suggestion or comment
- [ ] Frontend sends explicit feedback_type in WS message

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Python reviewer flagged as blocking |
