---
status: pending
priority: p2
issue_id: "014"
tags: [code-review, frontend, svelte]
dependencies: []
---

# ws-handler.ts bypasses updateLastChatContent store method

## Problem Statement

`ws-handler.ts` directly mutates `lastChat.content` and `lastChat.done` instead of using the existing `focus.updateLastChatContent()` method. This creates two divergent code paths for the same operation.

**File:** `frontend/src/lib/ws-handler.ts`, lines 120-123

## Fix

Use the store method:
```typescript
case 'focus.chat_response': {
    if (session.screen !== 'focus') break;
    const lastChat = focus.chatMessages[focus.chatMessages.length - 1];
    if (lastChat?.role === 'ai' && !lastChat.done) {
        focus.updateLastChatContent(lastChat.content + msg.content, msg.done);
    } else {
        focus.addChatMessage({ role: 'ai', content: msg.content, done: msg.done });
    }
    break;
}
```

## Acceptance Criteria

- [ ] ws-handler uses `focus.updateLastChatContent()` instead of direct mutation

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | |
