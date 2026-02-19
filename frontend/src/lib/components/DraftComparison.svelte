<script lang="ts">
  import { drafts } from '$lib/stores/drafts.svelte';
  import { session } from '$lib/stores/session.svelte';
  import { focus } from '$lib/stores/focus.svelte';
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
    const draft = drafts.drafts[draftIndex];
    if (!draft) return;
    focus.enterFocus(draftIndex, draft.content);
    session.goToFocus();
  }

  let roundLabel = $derived(
    drafts.synthesisRound > 0
      ? `Round ${drafts.synthesisRound + 1}`
      : ''
  );

  let roundNumbers = $derived(
    Object.keys(drafts.allRounds).map(Number).sort((a, b) => a - b)
  );

  let transcriptOpen = $state(false);
</script>

<div class="draft-comparison">
  <div class="header">
    <h2>
      {#if drafts.isViewingHistory}
        Round {(drafts.viewingRound ?? 0) + 1} (read-only)
      {:else if drafts.synthesisRound > 0}
        Refined drafts {roundLabel}
      {:else}
        Three angles on your {session.taskType}
      {/if}
    </h2>
    <p class="subtitle">
      {#if drafts.isViewingHistory}
        Viewing historical round. Switch to latest to edit.
      {:else if drafts.synthesizing}
        Synthesizing new drafts from your feedback...
      {:else if drafts.allComplete}
        Select text to highlight, edit directly, or focus on a draft.
      {:else}
        Drafts are generating...
      {/if}
    </p>
  </div>

  {#if roundNumbers.length > 1}
    <div class="round-tabs">
      {#each roundNumbers as rn}
        <button
          class="round-tab"
          class:active={drafts.isViewingHistory ? drafts.viewingRound === rn : rn === drafts.synthesisRound}
          onclick={() => {
            if (rn === drafts.synthesisRound) {
              drafts.viewLatestRound();
            } else {
              drafts.viewRound(rn);
            }
          }}
        >
          {rn === 0 ? 'Original' : `Round ${rn + 1}`}
          {#if rn === drafts.synthesisRound}
            <span class="latest-badge">latest</span>
          {/if}
        </button>
      {/each}
    </div>
  {/if}

  {#if session.messages.length > 0}
    <details class="transcript" bind:open={transcriptOpen}>
      <summary class="transcript-toggle">
        Interview transcript ({session.messages.filter(m => m.role === 'user' || m.role === 'ai').length} messages)
      </summary>
      <div class="transcript-body">
        {#each session.messages as msg}
          {#if msg.role === 'ai'}
            <div class="transcript-msg transcript-ai">
              <span class="transcript-label">AI</span>
              <p>{msg.content}</p>
            </div>
          {:else if msg.role === 'user'}
            <div class="transcript-msg transcript-user">
              <span class="transcript-label">You</span>
              <p>{msg.content}</p>
            </div>
          {:else if msg.role === 'thought' && msg.thought}
            <div class="transcript-msg transcript-thought">
              <span class="transcript-label">Thought</span>
              <p class="thought-text">{msg.thought.assessment}</p>
            </div>
          {/if}
        {/each}
      </div>
    </details>
  {/if}

  <div class="panels">
    {#each drafts.drafts as draft, i}
      <DraftPanel
        {draft}
        index={i}
        onhighlight={drafts.isViewingHistory ? undefined : (data) => handleHighlight(i, data)}
        onremove={drafts.isViewingHistory ? undefined : (hlIdx) => handleRemove(i, hlIdx)}
        onlabelchange={drafts.isViewingHistory ? undefined : (hlIdx, label) => handleLabelChange(i, hlIdx, label)}
        onedit={drafts.isViewingHistory ? undefined : (content) => handleEdit(i, content)}
        onfocus={drafts.isViewingHistory ? undefined : () => handleFocus(i)}
      />
    {/each}
  </div>

  {#if drafts.allComplete && !drafts.synthesizing && !drafts.isViewingHistory}
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

  /* Round tabs */
  .round-tabs {
    display: flex;
    justify-content: center;
    gap: 6px;
    margin-bottom: 16px;
    flex-shrink: 0;
  }

  .round-tab {
    padding: 6px 14px;
    border-radius: 16px;
    border: 1px solid var(--chrome-border);
    background: transparent;
    color: var(--chrome-text-muted);
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s, color 0.2s, border-color 0.2s;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .round-tab:hover {
    border-color: var(--chrome-text-muted);
    color: var(--chrome-text);
  }

  .round-tab.active {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
  }

  .latest-badge {
    font-size: 10px;
    opacity: 0.7;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  /* Interview transcript */
  .transcript {
    margin-bottom: 16px;
    flex-shrink: 0;
  }

  .transcript-toggle {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    color: var(--chrome-text-muted);
    cursor: pointer;
    padding: 8px 12px;
    border-radius: 8px;
    transition: color 0.2s;
  }

  .transcript-toggle:hover {
    color: var(--chrome-text);
  }

  .transcript-body {
    max-height: 240px;
    overflow-y: auto;
    padding: 12px;
    border: 1px solid var(--chrome-border);
    border-radius: 8px;
    margin-top: 8px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .transcript-msg {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    line-height: 1.5;
  }

  .transcript-msg p {
    margin: 2px 0 0;
    color: var(--chrome-text);
  }

  .transcript-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .transcript-ai .transcript-label {
    color: var(--accent);
  }

  .transcript-user .transcript-label {
    color: var(--success);
  }

  .transcript-thought .transcript-label {
    color: var(--chrome-text-muted);
  }

  .thought-text {
    color: var(--chrome-text-muted) !important;
    font-style: italic;
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
