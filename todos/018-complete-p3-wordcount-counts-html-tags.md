---
status: pending
priority: p3
issue_id: "018"
tags: [code-review, frontend, quality]
dependencies: []
---

# wordCount getter counts HTML tags as words

## Problem Statement

`focus.wordCount` splits `this.content` (which is TipTap HTML like `<p>Hello world</p>`) on whitespace. HTML tags inflate the count.

**File:** `frontend/src/lib/stores/focus.svelte.ts`, lines 55-57

## Fix

Strip HTML before counting:
```typescript
get wordCount(): number {
    const text = this.content.replace(/<[^>]+>/g, ' ');
    return text.split(/\s+/).filter(Boolean).length;
}
```

## Acceptance Criteria

- [ ] Word count reflects actual words, not HTML tags

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | |
