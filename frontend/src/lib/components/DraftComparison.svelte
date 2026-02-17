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
      <p class="hint">Click "Focus on this" on any draft to start editing, or highlight across drafts (coming soon).</p>
    </div>
  {/if}
</div>

<style>
  .draft-comparison {
    padding: 24px;
    max-width: 1200px;
    margin: 0 auto;
  }

  .header {
    margin-bottom: 24px;
  }

  h2 {
    font-size: 24px;
    font-weight: 700;
    color: var(--text-primary, #1a1a1a);
    margin: 0 0 8px;
  }

  .subtitle {
    font-size: 15px;
    color: var(--text-secondary, #666);
    margin: 0;
  }

  .panels {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }

  @media (max-width: 900px) {
    .panels {
      grid-template-columns: 1fr;
    }
  }

  .actions {
    margin-top: 24px;
    text-align: center;
  }

  .hint {
    font-size: 14px;
    color: var(--text-muted, #999);
    margin: 0;
  }
</style>
