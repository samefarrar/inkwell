# Proof — Agent Setup Guide

Proof is an agent-native markdown editor for macOS. It tracks who wrote what
(human vs AI) and lets agents collaborate with humans through suggestions,
comments, and real-time feedback — all via an HTTP bridge at localhost:9847.

Follow these steps to install and start collaborating.

## Web Sharing Quickstart (Create A Web Doc Via API)

If you're trying to create a shared *web* doc (proofeditor.ai) via API, use the headerless endpoint:

  curl -sS -X POST https://www.proofeditor.ai/share/markdown -H "Content-Type: application/json" -H "Authorization: Bearer <api_key_or_session_token_if_required>" -d '{"title":"My Doc","markdown":"# Hello\n\nThis is shared."}'

Then open the returned shareUrl in a browser. Full API reference: https://www.proofeditor.ai/agent-docs

If you guessed POST /api/documents or POST /api/share/markdown and saw CLIENT_UPGRADE_REQUIRED (missing X-Proof-Client-* headers), switch to POST /share/markdown.

## Step 1: Install Proof

Download and install the latest release:

  # Kill any running Proof instances first
  pkill -f "Proof.app" 2>/dev/null; sleep 1

  # Download the latest release
  curl -fsSL "https://github.com/EveryInc/proof/releases/latest/download/Proof.zip" -o /tmp/Proof.zip
  # (fallback) curl -fsSL "https://api.amore.computer/v1/apps/com.every.Proof/download" -o /tmp/Proof.zip

  # Unzip and copy to Applications
  cd /tmp && unzip -o Proof.zip
  cp -R /tmp/Proof.app /Applications/
  rm -f /tmp/Proof.zip /tmp/Proof.app

## Step 2: Install hooks (REQUIRED for Claude Code)

If you are Claude Code, run the hook installer. It copies provenance
hooks from the Proof app bundle and wires them into settings.json:

  bash <(curl -sL https://www.proofeditor.ai/install-hooks.sh)

Verify it worked:
  ls -la ~/.claude/hooks/proof-*.sh

## Step 3: Launch Proof and introduce yourself

IMPORTANT: You MUST complete ALL sub-steps below. Do NOT skip the demo.

First, tell the user what's about to happen:

  "I'm opening Proof with a welcome document. Watch the Proof window —
  you'll see me appear in the sidebar, leave a comment, and make a
  track-changes suggestion to show you how collaboration works."

Copy the welcome document from the app bundle (or download if missing) and open it:

  WELCOME_SRC="/Applications/Proof.app/Contents/Resources/Welcome.md"
  WELCOME_DST=~/Documents/Welcome\ to\ Proof.md
  if [ -f "$WELCOME_SRC" ]; then
    cp "$WELCOME_SRC" "$WELCOME_DST"
  else
    curl -sL https://www.proofeditor.ai/welcome.md -o "$WELCOME_DST"
  fi
  open /Applications/Proof.app "$WELCOME_DST"

Proof requires an Every account. If this is the user's first time opening
the app, they'll see a sign-in screen instead of the document. Tell them:

  "Proof requires an Every account. If you see a sign-in screen, click
  'Sign in with Every' to log in. If you don't have an account yet,
  click 'Need an account? Subscribe' to create one. Let me know once
  you're signed in and I'll continue with the demo."

Wait for the user to confirm they've signed in before proceeding.

Once they're ready, verify the bridge is responding:

  sleep 3
  curl -s http://localhost:9847/windows

You should see JSON with the Welcome document listed. If /windows
returns an error, try: curl -s http://localhost:9847/state

Now demo Proof's features on the welcome document:

a) Set your presence so the user sees you in the sidebar:

  curl -s -X POST http://localhost:9847/presence \
    -H "Content-Type: application/json" \
    -H "X-Agent-Id: claude" \
    -d '{"status":"reading","summary":"Reading Welcome document..."}'

Tell the user: "Look at the Proof sidebar on the left — you should see
my name appear with a green status dot."

b) Leave a comment on text visible on the FIRST SCREEN (no scrolling).

IMPORTANT: To avoid shell escaping issues with complex JSON, write the
body to a temp file first, then use curl -d @file:

  cat > /tmp/proof-comment.json << 'ENDJSON'
{"quote":"tracks who wrote what","by":"ai:claude","text":"Hi! I just installed Proof and connected to this document. Try clicking on this highlighted text to read my comment — you can reply to me right here. I also made a suggestion below (the green underlined text) to show you how track changes work. Click it to accept or reject."}
ENDJSON
  curl -s -X POST http://localhost:9847/marks/comment \
    -H "Content-Type: application/json" \
    -H "X-Agent-Id: claude" \
    -d @/tmp/proof-comment.json
  rm /tmp/proof-comment.json

Tell the user: "I left a comment near the top on 'tracks who wrote what' —
click the highlighted text to read it and reply to me."

c) Make a suggestion to demonstrate track changes:

  curl -s -X POST http://localhost:9847/marks/suggest-replace \
    -H "Content-Type: application/json" \
    -H "X-Agent-Id: claude" \
    -d '{"quote":"This is your first Proof document.","by":"ai:claude","content":"This is your first Proof document — and I am your AI collaborator."}'

Tell the user: "I suggested an edit on 'This is your first Proof document' —
you'll see green underlined text. Click it to accept or reject the change."

d) Set presence to idle:

  curl -s -X POST http://localhost:9847/presence \
    -H "Content-Type: application/json" \
    -H "X-Agent-Id: claude" \
    -d '{"status":"idle","summary":"Waiting for your feedback"}'

e) Tell the user about the built-in Proof Agent:

Tell the user: "One more thing — Proof has a built-in AI agent in the
sidebar. Single-click 'Proof Agent' on the left to chat with it, or
double-click to turn on always-on mode where it watches your document
and responds to changes automatically. Try asking it to review this
document!"

Finally, tell the user they can open any markdown file in Proof with:
  open /Applications/Proof.app /path/to/file.md

## Step 4: Understand the bridge (reference)

Proof exposes an HTTP API at http://localhost:9847. Every request should
include these headers:

  X-Agent-Id: <your-name>     e.g. "claude", "copilot", "cursor", "windsurf"
  X-Window-Id: <window-uuid>  from /windows (required with multiple docs open)

IMPORTANT: Always use the bridge API for edits — never write to the markdown
file directly. The bridge tracks provenance (who wrote what) automatically via
the "by" field on every request. Direct file writes bypass this.

### Web Bridge for shared docs

When a user gives you a shared URL like:
  https://www.proofeditor.ai/d/abc123

Preferred server-native endpoints:

  GET  https://www.proofeditor.ai/api/agent/abc123/state
  POST https://www.proofeditor.ai/api/documents/abc123/ops

/api/documents/:slug/ops supports:
  comment.add, comment.reply, comment.resolve
  suggestion.add (kind: insert|delete|replace)
  suggestion.accept, suggestion.reject
  rewrite.apply

Compatibility bridge base (also server-native by default):
  https://www.proofeditor.ai/d/abc123/bridge

Examples:
  GET  https://www.proofeditor.ai/d/abc123/bridge/state
  POST https://www.proofeditor.ai/d/abc123/bridge/marks/comment

Auth notes:
- Public editor links can comment/suggest/rewrite without a token.
- Protected actions may require:
    x-share-token: <ACCESS_TOKEN>
    x-bridge-token: <OWNER_SECRET>
    Authorization: Bearer <TOKEN>
- Bridge responses include:
    x-proof-bridge-execution: server|viewer

## Step 5: Collaborate

Read the document:
  GET /state
  → {"content": "markdown text...", "cursor": {...}, "wordCount": N, ...}

Suggest an edit (replace text):
  POST /marks/suggest-replace
  Body: {"quote": "text to find", "by": "ai:<your-name>", "content": "replacement"}

Suggest an insertion (after text):
  POST /marks/suggest-insert
  Body: {"quote": "text to find", "by": "ai:<your-name>", "content": "text to add"}

Suggest a deletion:
  POST /marks/suggest-delete
  Body: {"quote": "text to delete", "by": "ai:<your-name>"}

Bulk rewrite (diffs the whole document):
  POST /rewrite
  Body (full rewrite): {"content": "full new markdown", "by": "ai:<your-name>"}
  Body (changes mode): {"changes":[{"find":"old","replace":"new"}], "by":"ai:<your-name>"}
  → Editor computes a diff and creates suggestion marks for each change.
  → Use this for large edits or table-safe status updates.

Safety rules:
  - Use /state.content (markdown) as your source of truth; avoid /state.plainText for rewrite payloads.
  - /marks/suggest-replace rejects quotes that span multiple table cells.
  - For table edits, replace one cell at a time or use /rewrite changes mode.

Leave a comment:
  POST /marks/comment
  Body: {"quote": "text to comment on", "by": "ai:<your-name>", "text": "your comment"}

Reply to a comment:
  POST /marks/reply
  Body: {"markId": "<id>", "by": "ai:<your-name>", "text": "reply text"}

The user sees your suggestions as tracked changes — green for insertions,
red strikethrough for deletions. They accept or reject each one in the UI.

## Step 6: Monitor for feedback

Poll for events so you can respond to user actions:

  GET /events/pending
  → {"events": [{"type": "suggestion.accepted", "data": {...}}, ...]}

Poll every 3-5 seconds. Events are drained after reading (each poll returns
only new events since your last poll).

Event types:
  suggestion.accepted  — user accepted your suggestion
  suggestion.rejected  — user rejected your suggestion
  comment.added        — user left a new comment
  comment.replied      — user replied to a comment thread
  comment.resolved     — user resolved a comment thread

Use events to drive a feedback loop: suggest → user responds → you adapt.

## Step 7: Show your presence (optional but recommended)

  POST /presence
  Body: {"status": "thinking", "summary": "Reviewing draft..."}

Valid statuses: idle, reading, thinking, acting, waiting, completed
The user sees your status in the sidebar, like "Claude Code — Reviewing draft..."

## Step 8: Configure yourself for persistent collaboration

After installing Proof, set up persistent instructions so you always know
how to collaborate via the bridge in future sessions.

IMPORTANT: Ask the user TWO things before making config changes:
1. "Can I add Proof collaboration instructions to your [config file]?"
2. "Do you want this globally (all projects, recommended) or just this project?"

Global is the default — recommend it unless the user prefers project-only.

Detect which agent you are and follow the matching section below.

### The collaboration instructions to save

Use this content (adapted to the file format) wherever you save it:

--- START PROOF INSTRUCTIONS ---
## Proof Collaboration

Proof is an agent-native markdown editor for Mac. When editing markdown
files, use the Proof HTTP bridge at localhost:9847 instead of writing
files directly, so provenance tracking works.

Key commands:
- curl -s http://localhost:9847/windows  (find open documents)
- POST /marks/suggest-replace  (suggest an edit)
- POST /marks/comment  (leave a comment)
- POST /rewrite  (bulk rewrite with diff; supports content or changes mode)
- GET /events/pending  (poll for user feedback)

Always include X-Agent-Id header. Use suggestions, never direct edits.
Proof tracks who wrote what — your contributions show in the provenance
gutter. Full API reference: https://www.proofeditor.ai/agent-setup

Safety:
- Prefer /state.content as canonical markdown input.
- For tables, avoid cross-cell replace suggestions; update one cell at a time.
- For repetitive status updates, prefer /rewrite with {"changes":[...]} to preserve markdown structure.
--- END PROOF INSTRUCTIONS ---

### If you are Claude Code

Hooks were already installed in Step 2. Save the Proof instructions to
one of these locations:
- GLOBAL (recommended): ~/.claude/CLAUDE.md  — append the instructions
- PROJECT: ./CLAUDE.md in the project root  — append the instructions

### If you are GitHub Copilot

Save the Proof instructions to one of these locations:
- GLOBAL (recommended): Add to your personal instructions in
  GitHub Copilot settings (Settings > Copilot > Instructions)
- PROJECT: .github/copilot-instructions.md in the project root

### If you are Cursor

Cursor's sandbox blocks localhost by default. Tell the user:
"I need to access localhost:9847 to talk to Proof. Please enable
'Allow network access' in Settings > Cursor Settings > Agents,
or change auto-run from 'Run in Sandbox' to 'Ask Every Time'."

Save the Proof instructions to one of these locations:
- GLOBAL (recommended): ~/.cursor/rules/proof.mdc
- PROJECT: .cursor/rules/proof.mdc

For Cursor, wrap the instructions with this frontmatter:
---
description: "Proof editor collaboration via HTTP bridge at localhost:9847"
globs: ["**/*.md"]
alwaysApply: true
---
[then the Proof instructions content]

### If you are Windsurf / Cascade

Save the Proof instructions to one of these locations:
- GLOBAL (recommended): ~/.windsurf/rules/proof.md
- PROJECT: .windsurf/rules/proof.md

Use Cascade's terminal for curl commands against the bridge.

### If you are Codex CLI

Enable network access first. Tell the user:
"I need network access to talk to Proof's bridge. Please add
network_access = true under [sandbox_workspace_write] in
~/.codex/config.toml."

Install the Proof-specific skill and add it to Codex skills:

  mkdir -p "$HOME/.codex/skills/proof-agent-ops"
  curl -fsSL https://www.proofeditor.ai/proof-agent-ops.SKILL.md -o "$HOME/.codex/skills/proof-agent-ops/SKILL.md"

Save the Proof instructions to one of these locations:
- GLOBAL (recommended): ~/.codex/AGENTS.md  — append the instructions
- PROJECT: ./AGENTS.md in the project root  — append the instructions

If you also have the `proof-agent-ops` skill available at
`~/.codex/skills/proof-agent-ops/SKILL.md`, load it as a dedicated skill when you
need deeper bridge/API/debug workflows (presence events, skill orchestration,
route-aware debugging).

## Quick Reference

  GET  /windows                  List open documents (find windowId)
  GET  /state                    Read document content, cursor, structure
  POST /marks/suggest-replace    Suggest replacing text
  POST /marks/suggest-insert     Suggest inserting text
  POST /marks/suggest-delete     Suggest deleting text
  POST /rewrite                  Bulk rewrite with automatic diff
  POST /marks/comment            Leave a comment on text
  POST /marks/reply              Reply to a comment thread
  POST /marks/resolve            Resolve a comment thread
  GET  /marks                    List all marks (suggestions + comments)
  POST /marks/accept             Accept a suggestion (by markId)
  POST /marks/reject             Reject a suggestion (by markId)
  GET  /events/pending           Poll for user feedback events
  POST /presence                 Set your status in the sidebar

## How it works

Proof's provenance system tracks every character — whether a human or AI wrote
it. When you use the bridge API with a "by": "ai:<name>" field, your edits are
attributed to you. The user sees a colored gutter showing authorship, and an
overall percentage (e.g. "Human 62% / AI 38%") in the sidebar.

Your suggestions appear as tracked changes that the user can accept or reject.
Comments appear as threaded discussions attached to specific text. The user
never needs to leave the editor to collaborate with you.
