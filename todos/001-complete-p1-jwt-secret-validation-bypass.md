---
status: pending
priority: p1
issue_id: "001"
tags: [code-review, security]
dependencies: []
---

# JWT Secret Validation Bypassed in Token Creation and WebSocket Auth

## Problem Statement

The `_get_secret_key()` function in `auth_deps.py` correctly validates that `JWT_SECRET_KEY` is at least 32 characters. However, two other code paths read the secret directly via `os.environ.get("JWT_SECRET_KEY", "")` with no validation:

1. `_create_token()` in `auth.py` line 34 — signs JWTs with potentially empty secret
2. WebSocket endpoint in `main.py` line 118 — verifies JWTs with potentially empty secret

If `JWT_SECRET_KEY` is unset, tokens are signed with an empty string, allowing any attacker to forge valid tokens.

## Findings

- **Flagged by**: Python Reviewer, Security Sentinel, Architecture Strategist (3 agents independently)
- **Severity**: HIGH — auth bypass if env var missing
- **auth.py:34**: `secret = os.environ.get("JWT_SECRET_KEY", "")` — no validation
- **main.py:118**: `secret = os.environ.get("JWT_SECRET_KEY", "")` — no validation
- **auth_deps.py:16-21**: `_get_secret_key()` correctly validates — but only used in `get_current_user()`
- **Lifespan validates at startup** (main.py:60-65), so in practice the empty-string path requires the lifespan to be bypassed (e.g., during testing)

## Proposed Solutions

### Option A: Reuse `_get_secret_key()` everywhere (Recommended)
- Import and call `_get_secret_key()` from `auth_deps.py` in both `auth.py` and `main.py`
- **Pros**: Single source of truth, consistent validation
- **Cons**: None
- **Effort**: Small (3 lines changed)
- **Risk**: None

### Option B: Module-level constant set at startup
- In `auth_deps.py`, export a module-level `JWT_SECRET` set during lifespan
- **Pros**: Single lookup, no repeated os.environ calls
- **Cons**: Module-level state, harder to test
- **Effort**: Medium
- **Risk**: Low

## Recommended Action

Option A — simplest fix.

## Technical Details

**Affected files:**
- `backend/src/proof_editor/api/auth.py` (line 34)
- `backend/src/proof_editor/main.py` (line 118)
- `backend/src/proof_editor/auth_deps.py` (import target)

## Acceptance Criteria

- [ ] `_create_token()` uses `_get_secret_key()` instead of `os.environ.get()`
- [ ] WS endpoint uses `_get_secret_key()` instead of `os.environ.get()`
- [ ] No direct `os.environ.get("JWT_SECRET_KEY")` calls remain except in `_get_secret_key()` and lifespan validation
- [ ] Tests pass

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-18 | Created from code review synthesis | 3 agents independently flagged this |

## Resources

- PR #3: feat/saas-auth-payments-landing
