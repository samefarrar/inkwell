---
status: pending
priority: p2
issue_id: "013"
tags: [code-review, frontend, tiptap]
dependencies: []
---

# setEditorReady() called before TipTap's onCreate fires

## Problem Statement

`FocusTipTap.svelte` calls `focus.setEditorReady()` synchronously after `new Editor()`, but the editor's first render may not have completed. When ProseMirror decorations are added later, this will cause decorations to be applied to a potentially unstable document.

**File:** `frontend/src/lib/components/FocusTipTap.svelte`, lines 12-32

## Proposed Solutions

Use TipTap's `onCreate` callback:
```typescript
editor = new Editor({
    ...
    onCreate: () => {
        focus.setEditorReady();
    },
});
```

- Effort: Small
- Risk: Low

## Acceptance Criteria

- [ ] `setEditorReady()` called in TipTap `onCreate` callback, not after constructor

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | TS reviewer flagged |
