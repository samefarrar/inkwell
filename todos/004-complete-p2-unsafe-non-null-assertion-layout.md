---
status: pending
priority: p2
issue_id: "004"
tags: [code-review, typescript, type-safety]
dependencies: []
---

# Unsafe Non-Null Assertion in (app)/+layout.server.ts

## Problem Statement

The `(app)/+layout.server.ts` uses `locals.user!` (non-null assertion) instead of a proper type guard. While the hooks.server.ts redirect should prevent unauthenticated access, the `!` assertion silently suppresses TypeScript's safety check. If the redirect guard has a bug, `null` propagates as `User` causing runtime crashes in all app pages.

## Findings

- **Flagged by**: TypeScript Reviewer
- **File**: `frontend/src/routes/(app)/+layout.server.ts` (line 4)
- **Current code**: `return { user: locals.user! };`
- **Impact**: If hooks guard fails, every `data.user.name` / `data.user.plan` access crashes

## Proposed Solutions

### Option A: Add runtime guard with redirect (Recommended)
```typescript
export const load: LayoutServerLoad = ({ locals }) => {
    if (!locals.user) redirect(303, '/login');
    return { user: locals.user };
};
```
- TypeScript narrows `locals.user` to `User` after the guard
- **Effort**: Small (3 lines)

## Acceptance Criteria

- [ ] Non-null assertion `!` removed from `(app)/+layout.server.ts`
- [ ] Replaced with proper null check + redirect
- [ ] `npm run check` passes

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-18 | Created from code review | TypeScript reviewer flagged |
