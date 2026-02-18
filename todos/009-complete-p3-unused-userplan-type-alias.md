---
status: pending
priority: p3
issue_id: "009"
tags: [code-review, simplicity]
dependencies: []
---

# Unused UserPlan Type Alias

## Problem Statement

`UserPlan` type alias in `frontend/src/lib/types/user.ts` (line 8) is defined but never used anywhere in the codebase.

## Findings

- **Flagged by**: Simplicity Reviewer
- **File**: `frontend/src/lib/types/user.ts` (line 8)
- **Code**: `export type UserPlan = User['plan'];`

## Proposed Solutions

### Option A: Remove it (Recommended)
Delete line 8. If needed later, `User['plan']` is self-documenting inline.
- **Effort**: Small (1 line)

## Acceptance Criteria

- [ ] `UserPlan` type alias removed
- [ ] No imports of `UserPlan` exist
- [ ] `npm run check` passes

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-18 | Created from code review | Simplicity reviewer flagged |
