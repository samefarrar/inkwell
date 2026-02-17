<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { ws, type ServerMessage } from '$lib/ws';
  import { session } from '$lib/stores/session.svelte';
  import { drafts } from '$lib/stores/drafts.svelte';
  import TaskSelector from '$lib/components/TaskSelector.svelte';
  import Interview from '$lib/components/Interview.svelte';
  import DraftComparison from '$lib/components/DraftComparison.svelte';

  let unsubscribe: (() => void) | undefined;

  onMount(() => {
    ws.connect();

    unsubscribe = ws.onMessage((msg: ServerMessage) => {
      switch (msg.type) {
        case 'thought':
          session.addMessage({
            role: 'thought',
            content: msg.assessment,
            thought: {
              assessment: msg.assessment,
              missing: msg.missing,
              sufficient: msg.sufficient
            }
          });
          break;

        case 'interview.question':
          session.addMessage({
            role: 'ai',
            content: msg.question
          });
          break;

        case 'ready_to_draft':
          session.setReadyToDraft(msg.summary, msg.key_material);
          break;

        case 'draft.start':
          if (session.screen !== 'drafts') {
            session.goToDrafts();
          }
          drafts.startDraft(msg.draft_index, msg.title, msg.angle);
          break;

        case 'draft.chunk':
          drafts.appendChunk(msg.draft_index, msg.content, msg.done);
          break;

        case 'draft.complete':
          drafts.completeDraft(msg.draft_index, msg.word_count);
          break;

        case 'status':
          session.addMessage({
            role: 'status',
            content: msg.message
          });
          break;

        case 'error':
          session.addMessage({
            role: 'status',
            content: `Error: ${msg.message}`
          });
          break;
      }
    });
  });

  onDestroy(() => {
    unsubscribe?.();
    ws.disconnect();
  });
</script>

<svelte:head>
  <title>Proof Editor</title>
</svelte:head>

<div class="app">
  <nav class="topbar">
    <span class="logo">Proof</span>
    <span class="connection" class:connected={ws.connected}>
      {ws.connected ? 'Connected' : 'Disconnected'}
    </span>
  </nav>

  <main>
    {#if session.screen === 'task'}
      <TaskSelector />
    {:else if session.screen === 'interview'}
      <Interview />
    {:else if session.screen === 'drafts'}
      <DraftComparison />
    {:else if session.screen === 'focus'}
      <div class="placeholder">
        <p>Focus editing mode coming in Phase 5.</p>
      </div>
    {/if}
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    font-family:
      -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
      'Helvetica Neue', Arial, sans-serif;
    background: var(--bg, #fafafa);
    color: var(--text-primary, #1a1a1a);
    -webkit-font-smoothing: antialiased;
  }

  :global(:root) {
    --bg: #fafafa;
    --bg-surface: #ffffff;
    --bg-muted: #f3f4f6;
    --text-primary: #1a1a1a;
    --text-secondary: #666666;
    --text-muted: #999999;
    --border: #e0e0e0;
    --accent: #f97316;
    --accent-light: #fff7ed;
  }

  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 24px;
    border-bottom: 1px solid var(--border);
    background: var(--bg-surface);
  }

  .logo {
    font-size: 18px;
    font-weight: 700;
    color: var(--text-primary);
  }

  .connection {
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 12px;
    background: #fef2f2;
    color: #dc2626;
  }

  .connection.connected {
    background: #f0fdf4;
    color: #16a34a;
  }

  main {
    flex: 1;
  }

  .placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 50vh;
    color: var(--text-muted);
  }
</style>
