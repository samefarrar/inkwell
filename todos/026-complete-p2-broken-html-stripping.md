---
status: pending
priority: p2
issue_id: "026"
tags: [code-review, security, backend]
dependencies: []
---

# Broken HTML stripping allows LLM prompt injection path

## Problem Statement

`FocusHandler._strip_html` uses `re.sub(r"<[^>]+>", "", html)` which fails on `>` inside content. A draft containing `<IGNORE PREVIOUS INSTRUCTIONS>` would leave `IGNORE PREVIOUS INSTRUCTIONS` in the LLM prompt. Also `<script>if (x > 0)</script>` leaves `{ alert(1) }` in the text.

**File:** `backend/src/proof_editor/agent/focus_handler.py`, lines 163-171

## Findings

- **Flagged by**: Security Sentinel (F-4, MEDIUM)
- The regex stops at the first `>` inside the "tag", leaving partial content
- This is a prompt injection vector into editorial.py and focus_agent.py

## Proposed Solutions

### Option A: Use stdlib HTMLParser (Recommended)
```python
from html.parser import HTMLParser

class _Stripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
    def handle_data(self, data: str) -> None:
        self._parts.append(data)
    def get_text(self) -> str:
        return " ".join(self._parts)

@staticmethod
def _strip_html(html: str) -> str:
    stripper = _Stripper()
    stripper.feed(html)
    return re.sub(r"\s+", " ", stripper.get_text()).strip()
```
- **Pros**: Zero-dependency, correct, handles script tags
- **Effort**: Small
- **Risk**: None

## Acceptance Criteria

- [ ] HTML stripping uses HTMLParser, not regex
- [ ] Script tag content is properly stripped
- [ ] `import re` and patterns moved to module level

## Work Log

| Date | Action | Learnings |
|------|--------|-----------|
| 2026-02-19 | Created from code review | Security sentinel flagged |
