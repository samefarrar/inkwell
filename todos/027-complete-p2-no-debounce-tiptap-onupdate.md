---
status: pending
priority: p2
issue_id: "027"
tags: [code-review, frontend, performance]
dependencies: []
---

# No debounce on TipTap onUpdate — full HTML serialization per keystroke

## Problem Statement

`FocusTipTap.svelte` calls `focus.content = e.getHTML()` on every keystroke. This serializes the entire ProseMirror document to HTML, writes to reactive state, and triggers the `wordCount` getter (which also splits the full HTML string). On a 3,000-word document this is significant churn.

Also: `onTransaction` callback (`element = element`) is a Svelte 4 reactivity hack that does nothing in Svelte 5 runes mode. It fires on every ProseMirror transaction (cursor moves, selection changes) for zero effect.

**File:** `frontend/src/lib/components/FocusTipTap.svelte`, lines 22-29

## Fix

1. Add 300ms debounce to `onUpdate`
2. Remove the `onTransaction` callback entirely
3. Convert `wordCount` getter to strip HTML before counting

## Acceptance Criteria

- [ ] `onUpdate` debounced to 300ms
- [ ] `onTransaction` callback removed
- [ ] Timer cleared in `onDestroy`

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Performance oracle + frontend races reviewer |
