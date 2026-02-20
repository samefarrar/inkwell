---
status: pending
priority: p3
issue_id: "019"
tags: [code-review, frontend, style]
dependencies: []
---

# Hardcoded colors break theming

## Problem Statement

`FocusSidebar.svelte` uses hardcoded `#ef4444` (red) and `#d4622e` (accent hover) instead of CSS variables. Rest of codebase uses `var(--accent)`, `var(--success)`, etc.

**Files:** `frontend/src/lib/components/FocusSidebar.svelte`, lines 303-307, 356-361, 538

## Fix

Replace with CSS variables: `var(--error)` or `var(--destructive)` for red, `var(--accent-hover)` for the hover state.

## Acceptance Criteria

- [ ] No hardcoded color values in new components

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | |
