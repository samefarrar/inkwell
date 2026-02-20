---
status: pending
priority: p2
issue_id: "016"
tags: [code-review, cleanup]
dependencies: []
---

# Dead code cleanup across focus edit feature

## Problem Statement

Several unused/dead items identified across the codebase:

1. `_chat_history` in `FocusHandler.__init__` — initialized but never read/written (FocusAgent has its own `self.messages`)
2. `analysisGeneration` in `FocusStore` — incremented but never used for any decision logic
3. `addChatMessage` return value — method returns `FocusChatMessage` but no caller uses it
4. `getEditor()` export in `FocusTipTap.svelte` — exported but never called from outside (FocusSidebar is a sibling, not child)
5. `onTransaction` callback — `element = element` is a Svelte 4 reactivity hack, unnecessary with Svelte 5 runes
6. `chatScrollEl` — declared with `undefined!` non-null assertion but never used (no auto-scroll implemented)
7. `acceptSuggestion` parameters — `quote`, `replacement`, `start`, `end` accepted but unused (edit not applied to TipTap doc)
8. `import re` inside `_strip_html` — should be top-level import with pre-compiled patterns
9. `import uuid` inside `suggest_edit` branch — should be top-level import

## Fix

- Delete items 1-3
- Remove `onTransaction` callback (5)
- Either implement auto-scroll or remove `chatScrollEl` (6)
- Remove unused params from `acceptSuggestion`, add TODO comment for TipTap edit (7)
- Move imports to top of files (8, 9)
- Keep `getEditor()` export only if TipTap edit wiring is planned for this PR (4)

## Acceptance Criteria

- [ ] No unused attributes/variables/parameters in new code
- [ ] Imports at top of files

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Consolidated from both reviewers |
