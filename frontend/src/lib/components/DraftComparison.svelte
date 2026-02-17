<script lang="ts">
  import { drafts } from '$lib/stores/drafts.svelte';
  import { session } from '$lib/stores/session.svelte';
  import { ws } from '$lib/ws.svelte';
  import DraftPanel from './DraftPanel.svelte';

  function handleHighlight(
    draftIndex: number,
    data: { start: number; end: number; sentiment: 'like' | 'flag' }
  ) {
    drafts.addHighlight(draftIndex, data);
    ws.send({
      type: 'draft.highlight',
      draft_index: draftIndex,
      start: data.start,
      end: data.end,
      sentiment: data.sentiment,
    });
  }

  function handleSynthesize() {
    ws.send({ type: 'draft.synthesize' });
  }

  let totalHighlights = $derived(
    drafts.drafts.reduce((sum, d) => sum + d.highlights.length, 0)
  );
</script>

<div class="draft-comparison">
  <div class="header">
    <h2>Three angles on your {session.taskType}</h2>
    <p class="subtitle">
      {#if drafts.allComplete}
        Select text in any draft to highlight what you like or flag what needs work.
      {:else}
        Compare, highlight what you like, or pick one to focus on.
      {/if}
    </p>
  </div>

  <div class="panels">
    {#each drafts.drafts as draft, i}
      <DraftPanel
        {draft}
        index={i}
        onhighlight={(data) => handleHighlight(i, data)}
      />
    {/each}
  </div>

  {#if drafts.allComplete}
    <div class="actions">
      {#if totalHighlights > 0}
        <span class="hl-summary">
          {totalHighlights} highlight{totalHighlights === 1 ? '' : 's'} across drafts
        </span>
        <button class="synthesize-btn" onclick={handleSynthesize}>
          Synthesize into a new draft
        </button>
      {:else}
        <p class="hint">
          Select text in any draft to highlight favorites or flag sections to fix.
        </p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .draft-comparison {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 48px);
    padding: 24px 32px;
    background: var(--chrome);
  }

  .header {
    text-align: center;
    margin-bottom: 24px;
    flex-shrink: 0;
  }

  h2 {
    font-family: 'Outfit', sans-serif;
    font-size: 22px;
    font-weight: 600;
    color: var(--chrome-text);
    margin: 0 0 6px;
  }

  .subtitle {
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    color: var(--chrome-text-muted);
    margin: 0;
  }

  .panels {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: 1fr;
    gap: 20px;
    flex: 1;
    min-height: 0;
  }

  .panels > :global(.draft-panel) {
    min-height: 0;
  }

  @media (max-width: 900px) {
    .panels {
      grid-template-columns: 1fr;
      grid-template-rows: auto;
    }

    .draft-comparison {
      height: auto;
      min-height: calc(100vh - 48px);
    }
  }

  .actions {
    margin-top: 20px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    flex-shrink: 0;
  }

  .hint {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    color: var(--chrome-text-muted);
    margin: 0;
  }

  .hl-summary {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    color: var(--chrome-text-muted);
  }

  .synthesize-btn {
    padding: 10px 24px;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s, transform 0.1s;
  }

  .synthesize-btn:hover {
    background: #d4622e;
  }

  .synthesize-btn:active {
    transform: scale(0.97);
  }
</style>
