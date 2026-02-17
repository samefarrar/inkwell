---
title: "feat: Editorial Darkroom UI Redesign"
type: feat
date: 2026-02-17
---

# Editorial Darkroom UI Redesign

## Overview

Redesign the Proof Editor frontend from a generic light-theme scaffold into a distinctive, publication-grade "Editorial Darkroom" aesthetic. Dark workspace chrome frames warm paper-like reading surfaces. Streaming drafts feel alive. The interview feels intimate. Drafts feel like published writing, not AI output.

## Problem Statement

The current UI uses system fonts, a generic light grey palette, no entrance animations, hard-capped draft panel heights, and a standard chat-bubble interview layout. It functions correctly but looks like every other AI tool. For a *writing partner* — where the reading experience is the product — the interface needs to feel crafted.

## Proposed Solution

A complete frontend visual overhaul across 4 components + 1 new utility, touching 8 files total. No backend changes. No new dependencies beyond Google Fonts (loaded via `<link>`).

### Design Language

- **Chrome**: Dark workspace (#1a1a1e) for nav, backgrounds, interview
- **Paper**: Warm off-white (#faf8f5) for draft reading surfaces
- **Accent**: Refined orange (#e8733a) — less neon than current #f97316
- **Typography**: Outfit (geometric sans for UI) + Newsreader (editorial serif for draft content)
- **Motion**: Staggered entrance animations, smooth streaming, soft cursor glow

## Technical Approach

### Phase 1: Foundation (Typography + Color System)

**Files:**
- `frontend/src/routes/+layout.svelte` — Add Google Fonts `<link>` tag
- `frontend/src/routes/+page.svelte` — Rewrite `:root` CSS variables and global styles

**CSS Variable System:**

```css
:root {
  /* Chrome (dark workspace) */
  --chrome: #1a1a1e;
  --chrome-surface: #26262b;
  --chrome-border: #38383d;
  --chrome-text: #e4e4e7;
  --chrome-text-muted: #71717a;

  /* Paper (warm reading surfaces) */
  --paper: #faf8f5;
  --paper-surface: #f3f0eb;
  --paper-border: #e2ddd5;

  /* Ink (text on paper) */
  --ink: #2c2418;
  --ink-secondary: #7a7062;
  --ink-muted: #a8a090;

  /* Accent */
  --accent: #e8733a;
  --accent-glow: rgba(232, 115, 58, 0.15);
  --accent-soft: #f4a574;

  /* Semantic */
  --success: #4ade80;
  --thought-bg: #2d2822;
  --thought-border: #4a3f2f;
}
```

**Font Loading:**

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet" />
```

**Typography Assignment:**
- `font-family: 'Outfit', sans-serif` — UI elements, nav, labels, interview chat, buttons
- `font-family: 'Newsreader', serif` — Draft content, task selector headline, textarea (user's words)

**Global body:**
- Dark chrome background
- Outfit as default font
- `-webkit-font-smoothing: antialiased`

**Nav bar:**
- Dark chrome background, "Proof" logo in Outfit 700 with `letter-spacing: 0.02em`
- Connection indicator: small breathing green/red dot (CSS animation), no text label
- Subtle breadcrumb: `Task > Interview > Drafts` in chrome-text-muted, current step in accent

**Acceptance Criteria:**
- [ ] Google Fonts load with `font-display: swap`
- [ ] All CSS variables defined in `:root`
- [ ] Nav bar uses dark chrome, breathing dot for connection
- [ ] Breadcrumb shows current workflow step
- [ ] Body background is `--chrome`

### Phase 2: StreamBuffer Utility

**File:** `frontend/src/lib/stream-buffer.svelte.ts` (new)

The core streaming UX improvement. Instead of rendering each WebSocket chunk immediately (causing bursty text appearance), buffer tokens and drain at a constant rate for smooth typewriter effect.

**Design:**

```typescript
class StreamBuffer {
  private buffer = '';
  private target: { content: string };    // reactive $state reference
  private rafId: number | null = null;
  private charsPerFrame = 3;              // ~180 chars/sec at 60fps
  private onUpdate?: () => void;

  constructor(target: { content: string }, onUpdate?: () => void);
  push(text: string): void;               // called on each WS chunk
  flush(): void;                           // drain remaining instantly
  destroy(): void;                         // cancel rAF loop
}
```

**Behavior:**
- `push()` appends to internal buffer, starts rAF loop if not running
- Each animation frame: move `charsPerFrame` characters from buffer to `target.content`
- When buffer empties, stop the rAF loop
- `flush()` moves everything remaining to target instantly (used when stream ends)
- `destroy()` cancels any pending rAF

**Integration point:** `drafts.svelte.ts` creates a `StreamBuffer` per draft in `startDraft()`, calls `push()` in `appendChunk()`, and `flush()` + `destroy()` in `completeDraft()`.

**Acceptance Criteria:**
- [ ] Text appears at constant rate (~180 chars/sec) regardless of chunk timing
- [ ] No characters lost between buffer and rendered content
- [ ] `flush()` immediately renders remaining content when stream ends
- [ ] rAF loop properly cleaned up on destroy

### Phase 3: DraftPanel + DraftComparison Rewrite

**Files:**
- `frontend/src/lib/components/DraftPanel.svelte`
- `frontend/src/lib/components/DraftComparison.svelte`
- `frontend/src/lib/stores/drafts.svelte.ts`

This is the hero screen — three drafts on warm paper against dark chrome.

**DraftComparison layout:**
- Dark chrome background, full viewport height (`calc(100vh - topbar)`)
- Header: "Three angles on your {taskType}" in Outfit, centered
- Three-column CSS grid, `gap: 20px`, `padding: 24px 32px`
- Panels fill available height (no `max-height: 400px` — use `flex: 1; overflow-y: auto`)

**DraftPanel card:**
- Warm paper background (`--paper`)
- Subtle warm border (`--paper-border`)
- `border-radius: 16px` with `box-shadow: 0 2px 12px rgba(0,0,0,0.15)` (shadow pops on dark bg)
- Full height within grid cell

**Panel header:**
- Paper-surface background (`--paper-surface`)
- Angle name in `small-caps`, `letter-spacing: 0.08em`, Outfit 600
- Word count: live counting number + "words" in ink-muted
- During streaming: small pulsing orange dot next to word count

**Draft content (streaming):**
- Newsreader serif, `font-size: 17px`, `line-height: 1.75`
- `color: --ink`
- `white-space: pre-wrap` during streaming
- Ember cursor: small orange circle (`width: 8px; height: 8px; border-radius: 50%`) with a soft pulsing glow (`box-shadow: 0 0 8px var(--accent-glow)`) — replaces the blinking `|` pipe
- Auto-scroll during streaming

**Draft content (complete):**
- Split into `<p>` elements
- First paragraph (title): Newsreader 600, `font-size: 20px`, `--ink`
- Body paragraphs: Newsreader 400, `font-size: 17px`, `--ink`
- Nice paragraph spacing: `margin-bottom: 1em`

**Completion transition:**
- Ember cursor fades out (opacity transition)
- Panel border settles from accent to paper-border
- Subtle green checkmark icon fades in next to angle name in header

**Panel footer (when complete):**
- "Focus on this" button: outlined style on paper, accent color, hover fills

**Skeleton loading (before streaming starts):**
- Warm shimmer on paper background (not grey shimmer)

**Acceptance Criteria:**
- [ ] Dark background, full-height panels on warm paper
- [ ] Newsreader serif for all draft content
- [ ] StreamBuffer integrated — text streams smoothly
- [ ] Ember cursor (pulsing orange dot) during streaming
- [ ] No `max-height` cap — panels scroll independently
- [ ] Completion animation (cursor fade, border settle)
- [ ] Responsive: single column on narrow screens

### Phase 4: Interview Rewrite

**File:** `frontend/src/lib/components/Interview.svelte`

Replace the chat-bubble layout with a focused editorial conversation.

**Overall layout:**
- Dark chrome background
- Content area: max-width 680px, centered
- Generous vertical spacing between messages

**AI questions:**
- Left-aligned, no bubble
- Question text in Outfit 500, `font-size: 18px`, `color: --chrome-text`
- Small "WRITING PARTNER" label above in `text-transform: uppercase`, `letter-spacing: 0.08em`, `font-size: 11px`, `color: --accent`

**User answers:**
- Appear in a warm paper-colored block (not orange bubble)
- `background: --paper`, `border-radius: 12px`, `padding: 20px`
- Newsreader serif font (user's words = writing)
- Small "YOU" label in chrome-text-muted above

**Thought blocks:**
- Collapsible marginalia style
- `background: --thought-bg`, `border-left: 3px solid --thought-border`
- No rounded bubble — left-border accent style
- Summary label in Outfit, amber-tinted (`#d4a574`)
- Missing items as inline comma-separated text (not a bulleted list — more compact)
- Collapsed by default after the first one (first thought open, subsequent collapsed)

**Textarea:**
- Paper-colored background (`--paper`), Newsreader serif font
- Large: `min-height: 120px`, `resize: vertical`
- Rounded bottom corners, flat top (feels connected to the conversation above it)
- Send button: small, right-aligned below textarea, accent-colored, Outfit font

**Ready-to-draft bar:**
- Accent-colored banner spanning width
- "I have enough material" text + "Start Writing" button in white

**Progress indicator:**
- 5 small dots at top of interview (like Spiral reference), filled up to current question count
- Subtle, chrome-text-muted unfilled, accent filled

**Acceptance Criteria:**
- [ ] Dark background, no chat bubbles
- [ ] AI questions in Outfit, user answers on paper blocks in Newsreader
- [ ] Thought blocks as left-border marginalia, collapsed by default after first
- [ ] Paper-colored textarea with serif font
- [ ] Progress dots showing interview phase
- [ ] Auto-scroll on new messages

### Phase 5: TaskSelector Rewrite

**File:** `frontend/src/lib/components/TaskSelector.svelte`

The opening screen — "The Blank Page."

**Layout:**
- Dark chrome background with a radial spotlight gradient centered on the form:
  ```css
  background: radial-gradient(ellipse at center, rgba(232,115,58,0.04) 0%, transparent 70%);
  ```
- Content centered both vertically and horizontally (flex centering on `calc(100vh - topbar)`)

**Headline:**
- "What are we writing?" in Newsreader italic, `font-size: 40px`, `color: --chrome-text`
- Subtitle in Outfit 400, chrome-text-muted

**Task type selector:**
- **Pill buttons** (not a `<select>` dropdown) — horizontal row
- Each pill: `padding: 8px 20px`, `border-radius: 24px`, `border: 1px solid --chrome-border`
- Unselected: transparent bg, chrome-text-muted
- Selected: `background: --accent`, `color: white`, subtle glow shadow
- Transition: `background 0.2s, color 0.2s, box-shadow 0.2s`

**Topic input:**
- Large textarea (not a single-line input): `min-height: 80px`
- Paper-colored background, Newsreader serif font, warm border
- Placeholder text in ink-muted

**Start button:**
- Full-width, accent background, Outfit 600, `padding: 16px`
- Disabled state: low opacity
- Enabled: subtle glow pulse animation on box-shadow

**Entrance animation:**
- Elements stagger in with `opacity: 0 → 1` and `translateY(16px) → 0`
- Headline first (0ms delay), subtitle (80ms), pills (160ms), textarea (240ms), button (320ms)
- Use CSS `animation` with `animation-delay` for each element

**Acceptance Criteria:**
- [ ] Dark background with warm radial gradient spotlight
- [ ] Newsreader italic headline
- [ ] Pill buttons for task type (not dropdown)
- [ ] Paper-colored textarea with serif font
- [ ] Staggered entrance animation
- [ ] Full-width accent start button with glow pulse when enabled

### Phase 6: Nav + Transitions

**Files:**
- `frontend/src/routes/+page.svelte` — Screen transitions
- Navigation breadcrumb in topbar

**Screen transitions:**
- Wrap each screen in a container with CSS transitions
- On screen change: outgoing screen fades out (`opacity: 1 → 0`, 150ms), incoming fades in (`opacity: 0 → 1`, 200ms, 100ms delay)
- Use Svelte `{#key session.screen}` with `transition:fade` or CSS-only approach

**Breadcrumb:**
- Three steps in nav: `Task`, `Interview`, `Drafts`
- Separated by `>` in chrome-text-muted
- Past steps: chrome-text-muted
- Current step: accent color, font-weight 600
- Future steps: chrome-border color

**Acceptance Criteria:**
- [ ] Smooth fade transitions between screens
- [ ] Breadcrumb in nav shows workflow progress
- [ ] No layout shift during transitions

## Files Changed Summary

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/routes/+layout.svelte` | Edit | Add Google Fonts link tags |
| `frontend/src/routes/+page.svelte` | Edit | CSS variables, dark chrome, nav bar, transitions |
| `frontend/src/lib/stream-buffer.svelte.ts` | New | Smooth streaming utility |
| `frontend/src/lib/stores/drafts.svelte.ts` | Edit | Integrate StreamBuffer |
| `frontend/src/lib/components/DraftPanel.svelte` | Rewrite | Paper cards, serif, ember cursor |
| `frontend/src/lib/components/DraftComparison.svelte` | Rewrite | Full-height dark layout |
| `frontend/src/lib/components/Interview.svelte` | Rewrite | Conversation layout, marginalia thoughts |
| `frontend/src/lib/components/TaskSelector.svelte` | Rewrite | Pill buttons, spotlight, entrance anim |

## Dependencies

- Google Fonts (Outfit + Newsreader) — loaded via CDN `<link>`, no npm package
- No new npm dependencies

## Risks

- **Font loading flash**: Mitigated by `font-display: swap` and preconnect hints
- **StreamBuffer timing**: If rAF loop lags, text may appear slower — `flush()` on completion ensures no text is lost
- **Dark theme contrast**: Needs manual verification that all text meets WCAG AA contrast ratios on both chrome and paper surfaces

## References

- [Chrome DevTools: Best practices to render streamed LLM responses](https://developer.chrome.com/docs/ai/render-llm-responses)
- [Smashing Magazine: Design Patterns for AI Interfaces](https://www.smashingmagazine.com/2025/07/design-patterns-ai-interfaces/)
- [Upstash: Smooth Text Streaming](https://upstash.com/blog/smooth-streaming)
- Spiral reference screenshots: `Screenshot 2026-02-16 at 09.08.01.png`, `Screenshot 2026-02-16 at 09.08.07.png`
- Proof.app reference: `proof_ui.png`
