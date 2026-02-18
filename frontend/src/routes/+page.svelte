<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { ws, type ServerMessage } from '$lib/ws.svelte';
  import { session } from '$lib/stores/session.svelte';
  import { drafts } from '$lib/stores/drafts.svelte';
  import { StreamBuffer } from '$lib/stream-buffer.svelte';
  import { BASE_API_URL } from '$lib/config';
  import TaskSelector from '$lib/components/TaskSelector.svelte';
  import Interview from '$lib/components/Interview.svelte';
  import DraftComparison from '$lib/components/DraftComparison.svelte';

  let unsubscribe: (() => void) | undefined;
  let activeBuffers: StreamBuffer[] = [];

  async function resumeSession(sessionId: number) {
    try {
      const res = await fetch(`${BASE_API_URL}/api/sessions/${sessionId}`);
      const data = await res.json();
      if (!data.found) return;

      // Parse interview messages into ChatMessages
      if (data.interview_messages?.length) {
        const msgs = data.interview_messages.map((m: {
          role: string;
          content: string;
          thought_json?: string | null;
          search_json?: string | null;
          ready_json?: string | null;
        }) => {
          const msg: import('$lib/stores/session.svelte').ChatMessage = {
            role: m.role as 'user' | 'ai' | 'thought' | 'status' | 'search',
            content: m.content
          };
          if (m.thought_json) {
            const t = JSON.parse(m.thought_json);
            msg.thought = { assessment: t.assessment, missing: t.missing ?? [], sufficient: t.sufficient ?? false };
          }
          if (m.search_json) {
            const s = JSON.parse(m.search_json);
            msg.search = { query: s.query, summary: s.summary };
          }
          return msg;
        });
        session.messages = msgs;
      }

      // Set session metadata
      session.taskType = data.task_type ?? '';
      session.topic = data.topic ?? '';

      // Determine max round from rounds keys
      const roundKeys = Object.keys(data.rounds ?? {}).map(Number);
      const maxRound = roundKeys.length > 0 ? Math.max(...roundKeys) : 0;

      if (roundKeys.length > 0) {
        // Load with round navigation
        drafts.loadFromSessionWithRounds(
          data.rounds,
          data.highlights ?? [],
          maxRound
        );
        session.screen = 'drafts';
      } else {
        // No drafts yet — resume at interview
        session.screen = 'interview';
      }

      // Tell backend to hydrate its orchestrator
      ws.send({ type: 'session.resume', session_id: data.session_id });
    } catch {
      // Silently fail
    }
  }

  onMount(() => {
    ws.connect();

    unsubscribe = ws.onMessage((msg: ServerMessage) => {
      switch (msg.type) {
        case 'thought': {
          const thoughtMsg = session.addMessage({
            role: 'thought',
            content: '',
            thought: {
              assessment: '',
              missing: msg.missing,
              sufficient: msg.sufficient
            }
          });
          // Stream the assessment into thought.assessment, mirror to content
          const tBuf = new StreamBuffer(thoughtMsg.thought!, 'assessment', () => {
            thoughtMsg.content = thoughtMsg.thought!.assessment;
          });
          tBuf.push(msg.assessment);
          activeBuffers.push(tBuf);
          break;
        }

        case 'interview.question': {
          const qMsg = session.addMessage({
            role: 'ai',
            content: ''
          });
          const qBuf = new StreamBuffer(qMsg, 'content');
          qBuf.push(msg.question);
          activeBuffers.push(qBuf);
          break;
        }

        case 'search.result':
          session.addMessage({
            role: 'search',
            content: msg.summary,
            search: { query: msg.query, summary: msg.summary }
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
          // If synthesis was in progress, reset the loading state
          if (drafts.synthesizing) {
            drafts.synthesizing = false;
          }
          session.addMessage({
            role: 'status',
            content: `Error: ${msg.message}`
          });
          console.error('[WS] Error from server:', msg.message);
          break;
      }
    });
  });

  onDestroy(() => {
    unsubscribe?.();
    ws.disconnect();
  });

  const steps = ['task', 'interview', 'drafts'] as const;
  const stepLabels: Record<string, string> = {
    task: 'Task',
    interview: 'Interview',
    drafts: 'Drafts'
  };
  const screenOrder: Record<string, number> = { task: 0, interview: 1, drafts: 2, focus: 3 };
</script>

<svelte:head>
  <title>Proof Editor</title>
</svelte:head>

<div class="app">
  <nav class="topbar">
    <div class="nav-left">
      <span class="logo">Proof</span>
      <span class="connection-dot" class:connected={ws.connected}></span>
    </div>
    <div class="breadcrumb">
      {#each steps as step, i}
        {#if i > 0}
          <span class="crumb-sep">›</span>
        {/if}
        <span
          class="crumb"
          class:past={(screenOrder[session.screen] ?? 0) > i}
          class:current={session.screen === step}
          class:future={(screenOrder[session.screen] ?? 0) < i}
        >
          {stepLabels[step]}
        </span>
      {/each}
    </div>
  </nav>

  <main>
    {#key session.screen}
      <div class="screen">
        {#if session.screen === 'task'}
          <TaskSelector onResume={resumeSession} />
        {:else if session.screen === 'interview'}
          <Interview />
        {:else if session.screen === 'drafts'}
          <DraftComparison />
        {:else if session.screen === 'focus'}
          <div class="placeholder">
            <p>Focus editing mode coming soon.</p>
          </div>
        {/if}
      </div>
    {/key}
  </main>
</div>

<style>
  :global(:root) {
    /* Chrome (dark workspace) */
    --chrome: #1a1a1e;
    --chrome-surface: #26262b;
    --chrome-border: #38383d;
    --chrome-text: #e4e4e7;
    --chrome-text-muted: #71717a;

    /* Paper (warm reading surfaces) */
    --paper: #faf8f5;
    --paper-surface: #f3f0eb;
    --paper-border: #e2ddd5;

    /* Ink (text on paper) */
    --ink: #2c2418;
    --ink-secondary: #7a7062;
    --ink-muted: #a8a090;

    /* Accent */
    --accent: #e8733a;
    --accent-glow: rgba(232, 115, 58, 0.15);
    --accent-soft: #f4a574;

    /* Semantic */
    --success: #4ade80;
    --thought-bg: #2d2822;
    --thought-border: #4a3f2f;
  }

  :global(body) {
    margin: 0;
    font-family: 'Outfit', sans-serif;
    background: var(--chrome);
    color: var(--chrome-text);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  :global(*, *::before, *::after) {
    box-sizing: border-box;
  }

  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Nav bar */
  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    border-bottom: 1px solid var(--chrome-border);
    background: var(--chrome);
    height: 48px;
    flex-shrink: 0;
  }

  .nav-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .logo {
    font-family: 'Outfit', sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: var(--chrome-text);
    letter-spacing: 0.02em;
  }

  .connection-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #dc2626;
    animation: breathe 2s ease-in-out infinite;
  }

  .connection-dot.connected {
    background: var(--success);
  }

  @keyframes breathe {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  /* Breadcrumb */
  .breadcrumb {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    font-weight: 500;
  }

  .crumb-sep {
    color: var(--chrome-text-muted);
    font-size: 11px;
  }

  .crumb {
    color: var(--chrome-border);
    transition: color 0.2s;
  }

  .crumb.past {
    color: var(--chrome-text-muted);
  }

  .crumb.current {
    color: var(--accent);
    font-weight: 600;
  }

  .crumb.future {
    color: var(--chrome-border);
  }

  /* Main */
  main {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .screen {
    flex: 1;
    display: flex;
    flex-direction: column;
    animation: fadeIn 0.2s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(4px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 50vh;
    color: var(--chrome-text-muted);
    font-family: 'Outfit', sans-serif;
  }
</style>
