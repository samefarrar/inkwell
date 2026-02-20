---
status: pending
priority: p1
issue_id: "022"
tags: [code-review, frontend, svelte, race-condition]
dependencies: []
---

# `done` flag lost in pending queue — analyzing spinner runs forever

## Problem Statement

When editorial comments arrive before TipTap mounts, they are queued in `FocusStore.pendingQueue`. The `QueuedMessage` type does not carry the `done` flag for comments. When the queue is flushed, `analyzing` is never set to `false`, so the "Analyzing draft..." spinner runs indefinitely.

**File:** `frontend/src/lib/stores/focus.svelte.ts`

The `QueuedMessage` type:
```typescript
type QueuedMessage =
    | { kind: 'suggestion'; data: FocusSuggestion }
    | { kind: 'comment'; data: FocusComment };
    // No 'done' on the comment variant
```

`addComment` sets `analyzing = false` when `done=true` at queue time, but `flushPendingQueue` never checks it:
```typescript
private flushPendingQueue(): void {
    for (const item of this.pendingQueue) {
        if (item.kind === 'suggestion') {
            this.suggestions = [...this.suggestions, item.data];
        } else {
            this.comments = [...this.comments, item.data];
            // BUG: done flag never handled here
        }
    }
}
```

## Findings

- **Flagged by**: Frontend Races Reviewer (P1)
- **Severity**: HIGH — user-visible forever-spinner when backend is fast and editor is slow to mount
- The `addComment` method does set `analyzing = false` at queue time (line 98), which is a partial mitigation — but it depends on timing

## Proposed Solutions

### Option A: Add `done` flag to QueuedMessage (Recommended)
```typescript
type QueuedMessage =
    | { kind: 'suggestion'; data: FocusSuggestion }
    | { kind: 'comment'; data: FocusComment; done: boolean };

// in addComment:
this.pendingQueue.push({ kind: 'comment', data: comment, done });

// in flushPendingQueue:
} else {
    this.comments = [...this.comments, item.data];
    if (item.done) this.analyzing = false;
}
```
- **Pros**: Clean, explicit
- **Effort**: Small
- **Risk**: None

## Acceptance Criteria

- [ ] `QueuedMessage` comment variant carries `done: boolean`
- [ ] `flushPendingQueue` checks `done` and sets `analyzing = false`
- [ ] Also batch array assignments (1 assignment per type, not N)

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Frontend races reviewer found this |
