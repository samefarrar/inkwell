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

  function handleRemove(draftIndex: number, highlightIndex: number) {
    drafts.removeHighlight(draftIndex, highlightIndex);
    ws.send({
      type: 'highlight.remove',
      draft_index: draftIndex,
      highlight_index: highlightIndex,
    });
  }

  function handleLabelChange(draftIndex: number, highlightIndex: number, label: string) {
    drafts.updateHighlightLabel(draftIndex, highlightIndex, label);
    ws.send({
      type: 'highlight.update',
      draft_index: draftIndex,
      highlight_index: highlightIndex,
      label,
    });
  }

  function handleEdit(draftIndex: number, content: string) {
    drafts.updateDraftContent(draftIndex, content);
    ws.send({
      type: 'draft.edit',
      draft_index: draftIndex,
      content,
    });
  }

  function handleSynthesize() {
    drafts.startSynthesis();
    ws.send({ type: 'draft.synthesize' });
  }

  function handleFocus(draftIndex: number) {
    // Future: transition to focused editing mode
    session.goToFocus();
  }

  let roundLabel = $derived(
    drafts.synthesisRound > 0
      ? `Round ${drafts.synthesisRound + 1}`
      : ''
  );
</script>

<div class="draft-comparison">
  <div class="header">
    <h2>
      {#if drafts.synthesisRound > 0}
        Refined drafts {roundLabel}
      {:else}
        Three angles on your {session.taskType}
      {/if}
    </h2>
    <p class="subtitle">
      {#if drafts.synthesizing}
        Synthesizing new drafts from your feedback...
      {:else if drafts.allComplete}
        Select text to highlight, edit directly, or focus on a draft.
      {:else}
        Drafts are generating...
      {/if}
    </p>
  </div>

  <div class="panels">
    {#each drafts.drafts as draft, i}
      <DraftPanel
        {draft}
        index={i}
        onhighlight={(data) => handleHighlight(i, data)}
        onremove={(hlIdx) => handleRemove(i, hlIdx)}
        onlabelchange={(hlIdx, label) => handleLabelChange(i, hlIdx, label)}
        onedit={(content) => handleEdit(i, content)}
        onfocus={() => handleFocus(i)}
      />
    {/each}
  </div>

  {#if drafts.allComplete && !drafts.synthesizing}
    <div class="actions">
      {#if drafts.totalHighlights > 0}
        <span class="hl-summary">
          {drafts.totalHighlights} highlight{drafts.totalHighlights === 1 ? '' : 's'} across drafts
        </span>
        <button class="synthesize-btn" onclick={handleSynthesize}>
          {#if drafts.synthesisRound > 0}
            Re-synthesize
          {:else}
            Synthesize into new drafts
          {/if}
        </button>
      {:else}
        <p class="hint">
          Select text in any draft to highlight favorites or flag sections to fix.
        </p>
      {/if}
    </div>
  {/if}

  {#if drafts.synthesizing}
    <div class="actions">
      <div class="synth-loading">
        <span class="synth-dot"></span>
        Generating refined drafts...
      </div>
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

  /* Synthesis loading state */
  .synth-loading {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    color: var(--accent);
    font-weight: 500;
  }

  .synth-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--accent);
    animation: pulse 1.2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
  }
</style>
