<script lang="ts">
  import { drafts } from '$lib/stores/drafts.svelte';
  import { session } from '$lib/stores/session.svelte';
  import DraftPanel from './DraftPanel.svelte';
</script>

<div class="draft-comparison">
  <div class="header">
    <h2>Three angles on your {session.taskType}</h2>
    <p class="subtitle">Compare, highlight what you like, or pick one to focus on.</p>
  </div>

  <div class="panels">
    {#each drafts.drafts as draft, i}
      <DraftPanel {draft} index={i} />
    {/each}
  </div>

  {#if drafts.allComplete}
    <div class="actions">
      <p class="hint">Click "Focus on this" on any draft to start editing, or highlight across drafts.</p>
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
    flex-shrink: 0;
  }

  .hint {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    color: var(--chrome-text-muted);
    margin: 0;
  }
</style>
