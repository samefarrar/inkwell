---
status: pending
priority: p2
issue_id: "007"
tags: [code-review, simplicity, dry]
dependencies: []
---

# Duplicate INTERNAL_API_URL Across 5 Server Files

## Problem Statement

The constant `const INTERNAL_API_URL = env.INTERNAL_API_URL ?? 'http://localhost:8000'` is duplicated in 5 server-side files. Extract to a shared module.

## Findings

- **Flagged by**: Simplicity Reviewer
- **Files**:
  - `frontend/src/routes/api/[...path]/+server.ts` (line 12)
  - `frontend/src/routes/(marketing)/login/+page.server.ts` (line 5)
  - `frontend/src/routes/(marketing)/register/+page.server.ts` (line 5)
  - `frontend/src/routes/(app)/dashboard/+page.server.ts` (line 4)
  - `frontend/src/routes/(app)/session/[id]/+page.server.ts` (line 5)

## Proposed Solutions

### Option A: Extract to `$lib/server/config.ts` (Recommended)
```typescript
// src/lib/server/config.ts
import { env } from '$env/dynamic/private';
export const INTERNAL_API_URL = env.INTERNAL_API_URL ?? 'http://localhost:8000';
```
Then import from all 5 files.
- **Effort**: Small

## Acceptance Criteria

- [ ] Single `INTERNAL_API_URL` definition in `$lib/server/config.ts`
- [ ] All 5 files import from the shared module
- [ ] `npm run check` passes

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-18 | Created from code review | Simplicity reviewer flagged |
