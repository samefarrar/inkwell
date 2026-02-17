<script lang="ts">
  import { tick } from 'svelte';
  import type { Draft } from '$lib/stores/drafts.svelte';

  interface Props {
    draft: Draft;
    index: number;
  }

  let { draft, index }: Props = $props();
  let contentEl = $state<HTMLDivElement>();

  $effect(() => {
    if (draft.streaming && draft.content && contentEl) {
      tick().then(() => {
        if (contentEl) {
          contentEl.scrollTop = contentEl.scrollHeight;
        }
      });
    }
  });

  function paragraphs(text: string): string[] {
    return text.split('\n').filter((line) => line.trim());
  }
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
      {/if}
    </span>
  </div>

  <div class="panel-body" bind:this={contentEl}>
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
      <div class="draft-content">
        {#each paragraphs(draft.content) as line, i}
          <p class:title-line={i === 0}>{line}</p>
        {/each}
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
    flex: 1;
    padding: 20px 24px;
    overflow-y: auto;
    min-height: 0;
  }

  .streaming-text {
    white-space: pre-wrap;
    font-family: 'Newsreader', serif;
    font-size: 17px;
    line-height: 1.75;
    color: var(--ink);
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

  /* Completed paragraphs */
  .draft-content p {
    font-family: 'Newsreader', serif;
    font-size: 17px;
    line-height: 1.75;
    color: var(--ink);
    margin: 0 0 1em;
  }

  .draft-content p.title-line {
    font-weight: 600;
    font-size: 20px;
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
