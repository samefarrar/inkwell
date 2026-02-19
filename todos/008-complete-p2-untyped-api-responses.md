---
status: pending
priority: p2
issue_id: "008"
tags: [code-review, typescript, type-safety]
dependencies: []
---

# Untyped API Responses in Dashboard and Session Loaders

## Problem Statement

The dashboard and session page loaders call `res.json()` which returns `any`. The templates access fields like `.id`, `.task_type`, `.status` with zero type safety. If the backend changes a field name, nothing catches it at build time.

## Findings

- **Flagged by**: TypeScript Reviewer
- **Files**:
  - `frontend/src/routes/(app)/dashboard/+page.server.ts` (line 16-17): `const sessions = await res.json();`
  - `frontend/src/routes/(app)/session/[id]/+page.server.ts` (line 17): `const sessionData = await res.json();`

## Proposed Solutions

### Option A: Define interfaces and type the responses (Recommended)
```typescript
interface SessionSummary {
    id: number;
    task_type: string;
    topic: string;
    status: string;
    draft_count: number;
    created_at: string;
}
const sessions: SessionSummary[] = await res.json();
```
- **Effort**: Small

## Acceptance Criteria

- [ ] Dashboard loader has typed session response
- [ ] Session loader has typed session detail response
- [ ] `npm run check` passes

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-18 | Created from code review | TypeScript reviewer flagged |
