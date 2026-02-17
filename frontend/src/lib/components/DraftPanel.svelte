<script lang="ts">
  import type { Draft } from '$lib/stores/drafts.svelte';

  interface Props {
    draft: Draft;
    index: number;
  }

  let { draft, index }: Props = $props();
</script>

<div class="draft-panel" class:streaming={draft.streaming} class:complete={draft.complete}>
  <div class="panel-header">
    <div class="angle-badge">{draft.angle || `Draft ${index + 1}`}</div>
    <span class="word-count">
      {#if draft.streaming}
        {draft.wordCount} words...
      {:else if draft.complete}
        {draft.wordCount} words
      {/if}
    </span>
  </div>

  <div class="panel-body">
    {#if !draft.streaming && !draft.complete}
      <div class="skeleton">
        <div class="skeleton-line long"></div>
        <div class="skeleton-line medium"></div>
        <div class="skeleton-line long"></div>
        <div class="skeleton-line short"></div>
      </div>
    {:else}
      <div class="draft-content">
        {#each draft.content.split('\n') as line}
          {#if line.trim()}
            <p>{line}</p>
          {/if}
        {/each}
      </div>
      {#if draft.streaming}
        <span class="cursor-blink">|</span>
      {/if}
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
    background: var(--bg-surface, #fff);
    border: 1px solid var(--border, #e0e0e0);
    border-radius: 12px;
    overflow: hidden;
    min-height: 300px;
    transition: border-color 0.2s;
  }

  .draft-panel.streaming {
    border-color: var(--accent, #f97316);
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border, #e0e0e0);
    background: var(--bg-muted, #f9fafb);
  }

  .angle-badge {
    padding: 4px 10px;
    background: var(--accent-light, #fff7ed);
    color: var(--accent, #f97316);
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
  }

  .word-count {
    font-size: 12px;
    color: var(--text-muted, #999);
  }

  .panel-body {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    max-height: 400px;
  }

  .draft-content p {
    margin: 0 0 12px;
    font-size: 14px;
    line-height: 1.6;
    color: var(--text-primary, #1a1a1a);
  }

  .draft-content p:first-child {
    font-weight: 600;
    font-size: 16px;
  }

  .cursor-blink {
    animation: blink 0.8s infinite;
    color: var(--accent, #f97316);
    font-weight: 300;
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }

  /* Skeleton loading */
  .skeleton {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .skeleton-line {
    height: 14px;
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
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
    padding: 12px 16px;
    border-top: 1px solid var(--border, #e0e0e0);
    display: flex;
    justify-content: flex-end;
  }

  .focus-btn {
    padding: 8px 16px;
    background: var(--accent, #f97316);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
  }

  .focus-btn:hover {
    opacity: 0.9;
  }
</style>
