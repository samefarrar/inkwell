---
status: pending
priority: p2
issue_id: "005"
tags: [code-review, typescript, security]
dependencies: []
---

# Unsafe JWT Payload Casts in hooks.server.ts

## Problem Statement

In `hooks.server.ts`, JWT payload fields are cast with `as string` and `as User['plan']` without runtime validation. If the JWT payload structure changes or a token has unexpected claims, these casts silently pass invalid data.

## Findings

- **Flagged by**: TypeScript Reviewer
- **File**: `frontend/src/hooks.server.ts` (lines 14-18)
- **Current code**:
  ```ts
  email: payload.email as string,
  name: payload.name as string,
  plan: payload.plan as User['plan']
  ```
- **Impact**: If payload is missing `email`/`name`/`plan`, app renders `undefined` values

## Proposed Solutions

### Option A: Add runtime validation (Recommended)
```typescript
const email = payload.email;
const name = payload.name;
const plan = payload.plan;
if (typeof email !== 'string' || typeof name !== 'string' || typeof plan !== 'string') {
    event.locals.user = null;
    event.cookies.delete('access_token', { path: '/' });
    return resolve(event);  // or just continue with null user
}
event.locals.user = { id: Number(payload.sub), email, name, plan: plan as User['plan'] };
```
- **Effort**: Small

## Acceptance Criteria

- [ ] JWT payload fields validated at runtime before assignment
- [ ] Invalid payload gracefully handled (user set to null, cookie cleared)
- [ ] `npm run check` passes

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-18 | Created from code review | TypeScript reviewer flagged |
