---
status: pending
priority: p1
issue_id: "003"
tags: [code-review, performance, architecture]
dependencies: []
---

# Sync Database I/O in async def Endpoints Blocks Event Loop

## Problem Statement

All REST endpoints in `sessions.py`, `styles.py`, and `auth.py` are declared as `async def` but perform synchronous SQLite I/O via `with get_db() as db:`. This blocks the uvicorn event loop thread, preventing it from serving concurrent requests (including WebSocket messages).

## Findings

- **Flagged by**: Performance Oracle, Architecture Strategist (2 agents)
- **sessions.py**: All endpoints are `async def` with sync DB
- **styles.py**: All endpoints are `async def` with sync DB
- **auth.py**: `register`, `login`, `logout`, `me` — all `async def`
- **Impact at scale**: With 10+ concurrent users, p99 response times spike as REST and WS block each other
- **Note**: `get_current_user` is already `def` (correct) — FastAPI runs it in threadpool

## Proposed Solutions

### Option A: Change `async def` to `def` (Recommended)
- Remove `async` keyword from all endpoints that only do sync DB work
- FastAPI automatically runs `def` endpoints in a threadpool
- For `register`/`login`: they use `await to_thread()`, so keep them `async` but restructure per todo 002
- **Pros**: Simplest fix, correct by FastAPI convention
- **Cons**: `register`/`login` need to stay `async` for the `to_thread` calls
- **Effort**: Small (keyword changes + remove unnecessary `await`)
- **Risk**: None

### Option B: Wrap DB calls in `asyncio.to_thread()`
- Keep `async def`, wrap all DB operations in `await to_thread(lambda: ...)`
- **Pros**: Keeps async keyword consistent
- **Cons**: More verbose, harder to read
- **Effort**: Medium
- **Risk**: Low

## Recommended Action

Option A — change non-async endpoints to `def`.

## Technical Details

**Affected files:**
- `backend/src/proof_editor/api/sessions.py` (all endpoints)
- `backend/src/proof_editor/api/styles.py` (all endpoints)
- `backend/src/proof_editor/api/auth.py` (logout, me)

## Acceptance Criteria

- [ ] Endpoints that only do sync DB work use `def` not `async def`
- [ ] `register` and `login` stay `async def` (they use `to_thread`)
- [ ] Tests pass
- [ ] WebSocket messages are not blocked by concurrent REST requests

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-18 | Created from code review synthesis | Performance + Architecture reviewers flagged |

## Resources

- PR #3: feat/saas-auth-payments-landing
- FastAPI docs: sync vs async endpoints
