---
status: pending
priority: p1
issue_id: "002"
tags: [code-review, performance, security]
dependencies: []
---

# Database Session Held Open Across Await Boundary in Auth Endpoints

## Problem Statement

In `auth.py`, the `register` and `login` endpoints hold a SQLite database session open while awaiting `to_thread()` for Argon2id password hashing (100-200ms). During this time, the connection is idle but occupies a SQLite write lock, blocking other write requests.

## Findings

- **Flagged by**: Python Reviewer, Performance Oracle (2 agents)
- **register (line 61-74)**: Opens `with get_db() as db:`, then `await to_thread(pwd_hash.hash, ...)` inside — holds DB session for ~200ms
- **login (line 84-96)**: Opens `with get_db() as db:`, then `await to_thread(pwd_hash.verify, ...)` inside — holds DB session for ~200ms
- **Impact**: Under concurrent load, write requests queue behind each other. SQLite's busy_timeout of 5000ms means worst case 5s blocks.

## Proposed Solutions

### Option A: Hash before opening DB session (Recommended)
- Move `await to_thread(pwd_hash.hash, ...)` before `with get_db() as db:`
- For login: query user first, close DB, verify password, reopen if needed (or verify outside)
- **Pros**: DB session held only for the actual query+commit (~1ms)
- **Cons**: Login needs slight restructuring
- **Effort**: Small
- **Risk**: None

### Option B: Make endpoints `def` instead of `async def`
- FastAPI runs sync endpoints in threadpool, so blocking is acceptable
- **Pros**: Simpler — no need to restructure
- **Cons**: Loses the `await to_thread` pattern for Argon2; entire endpoint blocks a thread
- **Effort**: Small
- **Risk**: Low

## Recommended Action

Option A — hash/verify outside the DB context manager.

## Technical Details

**Affected files:**
- `backend/src/proof_editor/api/auth.py` (register: lines 58-78, login: lines 81-100)

## Acceptance Criteria

- [ ] `register` hashes password before opening DB session
- [ ] `login` does not hold DB session open during password verification
- [ ] Tests pass

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-18 | Created from code review synthesis | Python + Performance reviewers flagged |

## Resources

- PR #3: feat/saas-auth-payments-landing
