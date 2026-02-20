---
status: pending
priority: p1
issue_id: "011"
tags: [code-review, frontend, svelte]
dependencies: []
---

# $effect fires multiple times for focus.enter WS message

## Problem Statement

`FocusEditor.svelte` uses `$effect` to send `focus.enter` to the backend, but `$effect` tracks reactive dependencies and re-runs whenever `focus.selectedDraftIndex` changes — not just on mount. This can send duplicate `focus.enter` messages, triggering redundant style analysis and editorial LLM calls.

**File:** `frontend/src/lib/components/FocusEditor.svelte`, lines 15-19

```svelte
$effect(() => {
    if (focus.selectedDraftIndex >= 0) {
        ws.send({ type: 'focus.enter', draft_index: focus.selectedDraftIndex });
    }
});
```

## Findings

- `$effect` in Svelte 5 is dependency-tracked, not mount-only
- Component may be re-created by `{#key session.screen}` block in page routes
- Each extra `focus.enter` triggers a full LLM analysis pass ($$$)

## Proposed Solutions

### Option A: Use onMount instead (Recommended)
```svelte
import { onMount } from 'svelte';

onMount(() => {
    if (focus.selectedDraftIndex >= 0) {
        ws.send({ type: 'focus.enter', draft_index: focus.selectedDraftIndex });
    }
});
```
- Pros: Exactly-once semantics, idiomatic Svelte
- Cons: None
- Effort: Small
- Risk: Low

## Technical Details

- **Affected files:** `frontend/src/lib/components/FocusEditor.svelte`

## Acceptance Criteria

- [ ] `focus.enter` sent exactly once per focus session entry
- [ ] No duplicate WS messages when component re-renders

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | TS reviewer flagged as P1 bug |
