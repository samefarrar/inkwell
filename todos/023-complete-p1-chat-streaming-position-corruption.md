---
status: pending
priority: p1
issue_id: "023"
tags: [code-review, frontend, race-condition]
dependencies: []
---

# Chat streaming matches by position — concurrent sends corrupt messages

## Problem Statement

In `ws-handler.ts`, `focus.chat_response` appends content to "the last AI message that isn't done." If the user sends two chat messages before the first response finishes, the second placeholder bubble becomes "last", and remaining chunks from the first response get appended to the wrong bubble.

**File:** `frontend/src/lib/ws-handler.ts`, lines 120-127

```typescript
const lastChat = focus.chatMessages[focus.chatMessages.length - 1];
if (lastChat && lastChat.role === 'ai' && !lastChat.done) {
    lastChat.content += msg.content;  // appends to wrong bubble
    lastChat.done = msg.done;
}
```

## Findings

- **Flagged by**: Frontend Races Reviewer (P1)
- If user types fast and hits Enter twice, response chunks get redistributed across wrong bubbles
- The backend also has no concurrency guard (see todo 024)

## Proposed Solutions

### Option A: Disable send button during streaming + track active message (Recommended)
```typescript
// FocusStore:
activeChatMessage = $state<FocusChatMessage | null>(null);

// ws-handler.ts:
if (focus.activeChatMessage && !focus.activeChatMessage.done) {
    focus.activeChatMessage.content += msg.content;
    focus.activeChatMessage.done = msg.done;
    if (msg.done) focus.activeChatMessage = null;
}

// FocusSidebar.svelte:
<button disabled={!chatInput.trim() || !!focus.activeChatMessage}>
```
- **Pros**: Prevents the issue entirely
- **Effort**: Small
- **Risk**: None

## Acceptance Criteria

- [ ] Send button disabled while AI response is streaming
- [ ] Chat response chunks always append to the correct message
- [ ] No message content corruption on rapid sends

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Frontend races reviewer flagged |
