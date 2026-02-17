<script lang="ts">
  import { tick } from 'svelte';
  import type { Draft, Highlight } from '$lib/stores/drafts.svelte';

  interface Props {
    draft: Draft;
    index: number;
    onhighlight?: (data: { start: number; end: number; sentiment: 'like' | 'flag' }) => void;
  }

  let { draft, index, onhighlight }: Props = $props();
  let bodyEl = $state<HTMLDivElement>();
  let textEl = $state<HTMLDivElement>();
  let popover = $state<{ x: number; y: number; start: number; end: number } | null>(null);

  $effect(() => {
    if (draft.streaming && draft.content && bodyEl) {
      tick().then(() => {
        if (bodyEl) bodyEl.scrollTop = bodyEl.scrollHeight;
      });
    }
  });

  /** Walk text nodes to compute a character offset relative to the container. */
  function getTextOffset(container: HTMLElement, node: Node, offset: number): number {
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
    let charCount = 0;
    let current = walker.nextNode();
    while (current) {
      if (current === node) return charCount + offset;
      charCount += current.textContent?.length ?? 0;
      current = walker.nextNode();
    }
    return charCount;
  }

  function handleMouseUp(e: MouseEvent) {
    // Don't dismiss popover when clicking its buttons
    if ((e.target as HTMLElement).closest('.highlight-popover')) return;

    if (!draft.complete || !textEl || !bodyEl) {
      popover = null;
      return;
    }

    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) {
      popover = null;
      return;
    }

    const range = sel.getRangeAt(0);
    if (!textEl.contains(range.startContainer) || !textEl.contains(range.endContainer)) {
      popover = null;
      return;
    }

    const rawStart = getTextOffset(textEl, range.startContainer, range.startOffset);
    const rawEnd = getTextOffset(textEl, range.endContainer, range.endOffset);
    const start = Math.min(rawStart, rawEnd);
    const end = Math.max(rawStart, rawEnd);
    if (start >= end) {
      popover = null;
      return;
    }

    const rect = range.getBoundingClientRect();
    const bodyRect = bodyEl.getBoundingClientRect();

    popover = {
      x: rect.left - bodyRect.left + rect.width / 2,
      y: rect.top - bodyRect.top + bodyEl.scrollTop - 8,
      start,
      end,
    };
  }

  function applyHighlight(sentiment: 'like' | 'flag') {
    if (!popover) return;
    onhighlight?.({ start: popover.start, end: popover.end, sentiment });
    window.getSelection()?.removeAllRanges();
    popover = null;
  }

  type Segment = { text: string; sentiment?: 'like' | 'flag' };

  function buildSegments(content: string, highlights: Highlight[]): Segment[] {
    if (!highlights.length) return [{ text: content }];

    const sorted = [...highlights].sort((a, b) => a.start - b.start);
    const segments: Segment[] = [];
    let pos = 0;

    for (const hl of sorted) {
      const s = Math.max(hl.start, pos);
      if (s > pos) segments.push({ text: content.slice(pos, s) });
      if (hl.end > s) segments.push({ text: content.slice(s, hl.end), sentiment: hl.sentiment });
      pos = Math.max(pos, hl.end);
    }

    if (pos < content.length) segments.push({ text: content.slice(pos) });
    return segments;
  }

  let segments = $derived(buildSegments(draft.content, draft.highlights));
</script>

<div
  class="draft-panel"
  class:streaming={draft.streaming}
  class:complete={draft.complete}
>
  <div class="panel-header">
    <div class="angle-name">
      {#if draft.complete}
        <span class="check">&#10003;</span>
      {/if}
      <span class="angle-text">{draft.angle || `Draft ${index + 1}`}</span>
    </div>
    <span class="word-count">
      {#if draft.streaming}
        <span class="streaming-dot"></span>
        {draft.wordCount} words
      {:else if draft.complete}
        {draft.wordCount} words
        {#if draft.highlights.length > 0}
          <span class="hl-count">
            &middot; {draft.highlights.length}
          </span>
        {/if}
      {/if}
    </span>
  </div>

  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="panel-body" bind:this={bodyEl} onmouseup={handleMouseUp}>
    {#if !draft.streaming && !draft.complete}
      <div class="skeleton">
        <div class="skeleton-line long"></div>
        <div class="skeleton-line medium"></div>
        <div class="skeleton-line long"></div>
        <div class="skeleton-line short"></div>
      </div>
    {:else if draft.streaming}
      <div class="draft-content streaming-text">
        {draft.content}<span class="ember-cursor"></span>
      </div>
    {:else}
      <div class="draft-content" bind:this={textEl}>
        {#each segments as seg}
          {#if seg.sentiment}
            <span class="hl hl-{seg.sentiment}">{seg.text}</span>
          {:else}{seg.text}{/if}
        {/each}
      </div>
    {/if}

    {#if popover}
      <div
        class="highlight-popover"
        style="left: {popover.x}px; top: {popover.y}px;"
      >
        <button class="hl-btn like" onclick={() => applyHighlight('like')}>
          &#9829; Like
        </button>
        <button class="hl-btn flag" onclick={() => applyHighlight('flag')}>
          &#9873; Flag
        </button>
      </div>
    {/if}
  </div>

  {#if draft.complete}
    <div class="panel-footer">
      <button class="focus-btn">Focus on this</button>
    </div>
  {/if}
</div>

<style>
  .draft-panel {
    display: flex;
    flex-direction: column;
    background: var(--paper);
    border: 1px solid var(--paper-border);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
    transition: border-color 0.4s ease;
    min-height: 0;
  }

  .draft-panel.streaming {
    border-color: var(--accent);
  }

  .draft-panel.complete {
    border-color: var(--paper-border);
  }

  /* Header */
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 20px;
    border-bottom: 1px solid var(--paper-border);
    background: var(--paper-surface);
    flex-shrink: 0;
  }

  .angle-name {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .angle-text {
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    font-size: 13px;
    font-variant: small-caps;
    letter-spacing: 0.08em;
    color: var(--ink);
  }

  .check {
    color: var(--success);
    font-size: 14px;
    animation: checkFadeIn 0.3s ease;
  }

  @keyframes checkFadeIn {
    from { opacity: 0; transform: scale(0.8); }
    to { opacity: 1; transform: scale(1); }
  }

  .word-count {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    color: var(--ink-muted);
  }

  .hl-count {
    color: var(--accent);
  }

  .streaming-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse 1.2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
  }

  /* Body */
  .panel-body {
    position: relative;
    flex: 1;
    padding: 20px 24px;
    overflow-y: auto;
    min-height: 0;
  }

  .draft-content {
    font-family: 'Newsreader', serif;
    font-size: 17px;
    line-height: 1.75;
    color: var(--ink);
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  .ember-cursor {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 8px var(--accent-glow), 0 0 16px var(--accent-glow);
    vertical-align: baseline;
    margin-left: 2px;
    animation: ember 1.5s ease-in-out infinite;
  }

  @keyframes ember {
    0%, 100% {
      opacity: 1;
      box-shadow: 0 0 8px var(--accent-glow), 0 0 16px var(--accent-glow);
    }
    50% {
      opacity: 0.6;
      box-shadow: 0 0 4px var(--accent-glow);
    }
  }

  /* Highlight marks */
  .hl {
    border-radius: 2px;
    padding: 1px 0;
    transition: background 0.2s;
  }

  .hl-like {
    background: rgba(74, 222, 128, 0.2);
    border-bottom: 2px solid rgba(74, 222, 128, 0.5);
  }

  .hl-flag {
    background: rgba(232, 115, 58, 0.15);
    border-bottom: 2px solid rgba(232, 115, 58, 0.4);
  }

  /* Highlight popover */
  .highlight-popover {
    position: absolute;
    transform: translate(-50%, -100%);
    display: flex;
    gap: 4px;
    padding: 4px 6px;
    background: var(--chrome);
    border: 1px solid var(--chrome-border);
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    z-index: 10;
    animation: popIn 0.15s ease-out;
  }

  @keyframes popIn {
    from { opacity: 0; transform: translate(-50%, -100%) scale(0.9); }
    to { opacity: 1; transform: translate(-50%, -100%) scale(1); }
  }

  .hl-btn {
    padding: 4px 10px;
    border: none;
    border-radius: 5px;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
  }

  .hl-btn.like {
    background: rgba(74, 222, 128, 0.15);
    color: #4ade80;
  }

  .hl-btn.like:hover {
    background: rgba(74, 222, 128, 0.3);
  }

  .hl-btn.flag {
    background: rgba(232, 115, 58, 0.15);
    color: var(--accent);
  }

  .hl-btn.flag:hover {
    background: rgba(232, 115, 58, 0.3);
  }

  /* Skeleton */
  .skeleton {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .skeleton-line {
    height: 14px;
    background: linear-gradient(
      90deg,
      var(--paper-surface) 25%,
      var(--paper-border) 50%,
      var(--paper-surface) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
  }

  .skeleton-line.long { width: 100%; }
  .skeleton-line.medium { width: 75%; }
  .skeleton-line.short { width: 50%; }

  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  /* Footer */
  .panel-footer {
    padding: 14px 20px;
    border-top: 1px solid var(--paper-border);
    display: flex;
    justify-content: flex-end;
    flex-shrink: 0;
  }

  .focus-btn {
    padding: 8px 20px;
    background: transparent;
    color: var(--accent);
    border: 1px solid var(--accent);
    border-radius: 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s, color 0.2s;
  }

  .focus-btn:hover {
    background: var(--accent);
    color: white;
  }
</style>
