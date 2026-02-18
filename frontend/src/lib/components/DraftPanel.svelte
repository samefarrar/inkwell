<script lang="ts">
  import { tick } from 'svelte';
  import type { Draft, Highlight } from '$lib/stores/drafts.svelte';

  interface Props {
    draft: Draft;
    index: number;
    onhighlight?: (data: { start: number; end: number; sentiment: 'like' | 'flag' }) => void;
    onremove?: (highlightIndex: number) => void;
    onlabelchange?: (highlightIndex: number, label: string) => void;
    onedit?: (content: string) => void;
    onfocus?: () => void;
  }

  let { draft, index, onhighlight, onremove, onlabelchange, onedit, onfocus }: Props = $props();
  let bodyEl = $state<HTMLDivElement>();
  let textEl = $state<HTMLDivElement>();
  let popover = $state<{ x: number; y: number; start: number; end: number } | null>(null);
  let labelPopover = $state<{ highlightIndex: number; x: number; y: number } | null>(null);
  let labelInput = $state('');
  let hoveredHighlight = $state<number | null>(null);
  /** True while user is typing — suppresses reactive DOM rebuild of segments. */
  let userEditing = false;

  $effect(() => {
    if (draft.streaming && draft.content && bodyEl) {
      tick().then(() => {
        if (bodyEl) bodyEl.scrollTop = bodyEl.scrollHeight;
      });
    }
  });

  /** Filter that skips text nodes inside .hl-label and .hl-controls (non-content UI). */
  const contentTextFilter: NodeFilter = {
    acceptNode(n: Node): number {
      const parent = (n as Text).parentElement;
      if (parent?.closest('.hl-label, .hl-controls')) {
        return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    }
  };

  /** Walk only content text nodes (skipping labels/controls) to get a character offset. */
  function getTextOffset(container: HTMLElement, node: Node, offset: number): number {
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, contentTextFilter);
    let charCount = 0;
    let current = walker.nextNode();
    while (current) {
      if (current === node) return charCount + offset;
      charCount += current.textContent?.length ?? 0;
      current = walker.nextNode();
    }
    return charCount;
  }

  /** Read only content text from the contenteditable, skipping label/control UI text. */
  function getContentText(): string {
    if (!textEl) return '';
    const walker = document.createTreeWalker(textEl, NodeFilter.SHOW_TEXT, contentTextFilter);
    let text = '';
    let current = walker.nextNode();
    while (current) {
      text += current.textContent ?? '';
      current = walker.nextNode();
    }
    return text;
  }

  function handleMouseUp(e: MouseEvent) {
    // Don't dismiss popover when clicking its buttons
    if ((e.target as HTMLElement).closest('.highlight-popover')) return;
    if ((e.target as HTMLElement).closest('.label-popover')) return;
    if ((e.target as HTMLElement).closest('.hl-controls')) return;

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

  function handleRemove(highlightIndex: number) {
    onremove?.(highlightIndex);
    hoveredHighlight = null;
  }

  function openLabelPopover(highlightIndex: number, e: MouseEvent) {
    e.stopPropagation();
    const rect = (e.target as HTMLElement).getBoundingClientRect();
    const bodyRect = bodyEl!.getBoundingClientRect();
    labelInput = draft.highlights[highlightIndex]?.label ?? '';
    labelPopover = {
      highlightIndex,
      x: rect.left - bodyRect.left + rect.width / 2,
      y: rect.bottom - bodyRect.top + bodyEl!.scrollTop + 4,
    };
  }

  function submitLabel() {
    if (labelPopover === null) return;
    const snaked = labelInput.trim().toLowerCase().replace(/\s+/g, '_');
    onlabelchange?.(labelPopover.highlightIndex, snaked);
    labelPopover = null;
    labelInput = '';
  }

  function handleLabelKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault();
      submitLabel();
    } else if (e.key === 'Escape') {
      labelPopover = null;
      labelInput = '';
    }
  }

  /** Handle contenteditable input for draft editing. */
  function handleInput() {
    if (!textEl) return;
    const newContent = getContentText();
    if (newContent !== draft.content) {
      userEditing = true;
      onedit?.(newContent);
      // Clear after Svelte's microtask rendering cycle completes
      requestAnimationFrame(() => { userEditing = false; });
    }
  }

  type Segment = {
    text: string;
    sentiment?: 'like' | 'flag';
    label?: string;
    highlightIndex?: number;
  };

  function buildSegments(content: string, highlights: Highlight[]): Segment[] {
    if (!highlights.length) return [{ text: content }];

    const sorted = highlights
      .map((hl, idx) => ({ ...hl, originalIndex: idx }))
      .sort((a, b) => a.start - b.start);
    const segments: Segment[] = [];
    let pos = 0;

    for (const hl of sorted) {
      const s = Math.max(hl.start, pos);
      if (s > pos) segments.push({ text: content.slice(pos, s) });
      if (hl.end > s) {
        segments.push({
          text: content.slice(s, hl.end),
          sentiment: hl.sentiment,
          label: hl.label,
          highlightIndex: hl.originalIndex,
        });
      }
      pos = Math.max(pos, hl.end);
    }

    if (pos < content.length) segments.push({ text: content.slice(pos) });
    return segments;
  }

  let segments = $state<Segment[]>([]);

  $effect(() => {
    // Re-read reactive deps so Svelte tracks them
    const content = draft.content;
    const highlights = draft.highlights;
    // Skip DOM rebuild when the user is actively typing —
    // the contenteditable DOM already has the correct text.
    if (!userEditing) {
      segments = buildSegments(content, highlights);
    }
  });
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
      <div
        class="draft-content"
        bind:this={textEl}
        contenteditable="true"
        oninput={handleInput}
        role="textbox"
        tabindex="0"
      >
        {#each segments as seg}
          {#if seg.sentiment !== undefined && seg.highlightIndex !== undefined}
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <span
              class="hl hl-{seg.sentiment}"
              onmouseenter={() => (hoveredHighlight = seg.highlightIndex!)}
              onmouseleave={() => (hoveredHighlight = null)}
            >
              {#if seg.label}
                <span class="hl-label">{seg.label}</span>
              {/if}
              {seg.text}
              {#if hoveredHighlight === seg.highlightIndex}
                <span class="hl-controls">
                  <button
                    class="hl-ctrl-btn"
                    title="Set label"
                    onclick={(e) => openLabelPopover(seg.highlightIndex!, e)}
                  >&#9881;</button>
                  <button
                    class="hl-ctrl-btn remove"
                    title="Remove highlight"
                    onclick={() => handleRemove(seg.highlightIndex!)}
                  >&#10005;</button>
                </span>
              {/if}
            </span>
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

    {#if labelPopover}
      <div
        class="label-popover"
        style="left: {labelPopover.x}px; top: {labelPopover.y}px;"
      >
        <input
          type="text"
          class="label-input"
          placeholder="e.g. Too Formal"
          bind:value={labelInput}
          onkeydown={handleLabelKeydown}
        />
        <button class="label-submit" onclick={submitLabel}>Set</button>
      </div>
    {/if}
  </div>

  {#if draft.complete}
    <div class="panel-footer">
      <button class="focus-btn" onclick={() => onfocus?.()}>Focus on this</button>
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
    outline: none;
  }

  .draft-content[contenteditable="true"]:focus {
    box-shadow: inset 0 0 0 2px rgba(232, 115, 58, 0.15);
    border-radius: 4px;
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
    position: relative;
  }

  .hl-like {
    background: rgba(74, 222, 128, 0.2);
    border-bottom: 2px solid rgba(74, 222, 128, 0.5);
  }

  .hl-flag {
    background: rgba(232, 115, 58, 0.15);
    border-bottom: 2px solid rgba(232, 115, 58, 0.4);
  }

  /* Highlight label tag */
  .hl-label {
    display: inline-block;
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.04em;
    color: var(--ink-secondary);
    background: var(--paper-surface);
    border: 1px solid var(--paper-border);
    border-radius: 3px;
    padding: 1px 5px;
    margin-right: 4px;
    vertical-align: middle;
    line-height: 1.4;
  }

  /* Highlight hover controls */
  .hl-controls {
    display: inline-flex;
    gap: 2px;
    margin-left: 2px;
    vertical-align: middle;
    animation: popIn 0.1s ease-out;
  }

  .hl-ctrl-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border: none;
    border-radius: 3px;
    background: var(--paper-surface);
    color: var(--ink-muted);
    font-size: 10px;
    cursor: pointer;
    padding: 0;
    line-height: 1;
    transition: background 0.15s, color 0.15s;
  }

  .hl-ctrl-btn:hover {
    background: var(--paper-border);
    color: var(--ink);
  }

  .hl-ctrl-btn.remove:hover {
    background: rgba(232, 115, 58, 0.3);
    color: var(--accent);
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

  /* Label popover */
  .label-popover {
    position: absolute;
    transform: translateX(-50%);
    display: flex;
    gap: 4px;
    padding: 6px 8px;
    background: var(--chrome);
    border: 1px solid var(--chrome-border);
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    z-index: 11;
    animation: popIn 0.15s ease-out;
  }

  .label-input {
    width: 120px;
    padding: 4px 8px;
    border: 1px solid var(--chrome-border);
    border-radius: 5px;
    background: var(--chrome-surface);
    color: var(--chrome-text);
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    outline: none;
  }

  .label-input:focus {
    border-color: var(--accent);
  }

  .label-submit {
    padding: 4px 10px;
    border: none;
    border-radius: 5px;
    background: var(--accent);
    color: white;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
  }

  .label-submit:hover {
    background: #d4622e;
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
