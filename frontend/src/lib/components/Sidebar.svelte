<script lang="ts">
  import { onMount } from 'svelte';
  import { session, type SessionSummary } from '$lib/stores/session.svelte';
  import { styles } from '$lib/stores/styles.svelte';
  import { ws } from '$lib/ws.svelte';

  let { onResume, onNewSession }: {
    onResume: (sessionId: number) => void;
    onNewSession: () => void;
  } = $props();

  let switchDebounce: ReturnType<typeof setTimeout> | null = null;

  onMount(() => {
    session.loadSessions();
    styles.loadStyles();
  });

  function handleSessionClick(s: SessionSummary) {
    if (s.id === session.currentSessionId) return;
    // Debounce rapid switching (200ms)
    if (switchDebounce) clearTimeout(switchDebounce);
    switchDebounce = setTimeout(() => {
      ws.send({ type: 'session.cancel' });
      onResume(s.id);
      switchDebounce = null;
    }, 200);
  }

  function handleNewSession() {
    ws.send({ type: 'session.cancel' });
    onNewSession();
  }

  function relativeDate(iso: string): string {
    const d = new Date(iso);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString();
  }

  const taskTypeLabels: Record<string, string> = {
    essay: 'Essay',
    review: 'Review',
    newsletter: 'Newsletter',
    landing_page: 'Landing Page',
    blog_post: 'Blog Post'
  };
</script>

<aside class="sidebar">
  <div class="sidebar-header">
    <span class="sidebar-logo">Inkwell</span>
  </div>

  <button class="new-session-btn" onclick={handleNewSession}>
    <span class="plus">+</span> New session
  </button>

  <nav class="sidebar-nav">
    <button
      class="nav-item"
      class:active={session.appView === 'session'}
      onclick={() => session.setAppView('session')}
    >
      Sessions
    </button>
    <button
      class="nav-item"
      class:active={session.appView === 'styles'}
      onclick={() => session.setAppView('styles')}
    >
      Styles
    </button>
  </nav>

  <div class="sidebar-content">
    {#if session.appView === 'session'}
      <div class="section-label">HISTORY</div>
      {#if session.sessionsLoading}
        <div class="skeleton-list">
          {#each Array(4) as _}
            <div class="skeleton-item">
              <div class="skeleton-line short"></div>
              <div class="skeleton-line"></div>
            </div>
          {/each}
        </div>
      {:else if session.sessionList.length === 0}
        <div class="empty-state">No sessions yet</div>
      {:else}
        <div class="session-list">
          {#each session.sessionList as s (s.id)}
            <button
              class="session-item"
              class:active={s.id === session.currentSessionId}
              onclick={() => handleSessionClick(s)}
            >
              <span class="session-type">
                {taskTypeLabels[s.task_type] ?? s.task_type}
              </span>
              <span class="session-topic">{s.topic}</span>
              <span class="session-meta">
                {relativeDate(s.created_at)}
                {#if s.draft_count > 0}
                  · {s.draft_count} draft{s.draft_count === 1 ? '' : 's'}
                {/if}
              </span>
            </button>
          {/each}
        </div>
      {/if}
    {:else if session.appView === 'styles' || session.appView === 'style_editor'}
      <div class="section-label">WRITING STYLES</div>
      {#if styles.loading}
        <div class="skeleton-list">
          {#each Array(3) as _}
            <div class="skeleton-item">
              <div class="skeleton-line short"></div>
            </div>
          {/each}
        </div>
      {:else if styles.styles.length === 0}
        <div class="empty-state">No styles yet</div>
      {:else}
        <div class="session-list">
          {#each styles.styles as style (style.id)}
            <button
              class="session-item"
              class:active={styles.currentStyle?.id === style.id}
              onclick={() => {
                styles.loadStyle(style.id);
                session.setAppView('style_editor');
              }}
            >
              <span class="session-topic">{style.name}</span>
              {#if style.description}
                <span class="session-meta">{style.description}</span>
              {/if}
            </button>
          {/each}
        </div>
      {/if}
    {/if}
  </div>
</aside>

<style>
  .sidebar {
    width: 240px;
    min-width: 240px;
    height: 100vh;
    background: #16161a;
    background-image: linear-gradient(
      180deg,
      rgba(232, 115, 58, 0.03) 0%,
      transparent 120px
    );
    border-right: 1px solid var(--chrome-border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .sidebar-header {
    padding: 14px 16px 10px;
    flex-shrink: 0;
  }

  .sidebar-logo {
    font-family: 'Newsreader', serif;
    font-style: italic;
    font-weight: 600;
    font-size: 22px;
    color: var(--chrome-text);
    letter-spacing: -0.01em;
  }

  .new-session-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    margin: 4px 8px 8px;
    color: var(--accent);
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 600;
    background: transparent;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    width: calc(100% - 16px);
    text-align: left;
    transition: background 0.2s;
  }

  .new-session-btn:hover {
    background: rgba(232, 115, 58, 0.08);
  }

  .plus {
    font-size: 16px;
    line-height: 1;
  }

  .sidebar-nav {
    display: flex;
    gap: 2px;
    padding: 0 8px;
    margin-bottom: 12px;
    flex-shrink: 0;
  }

  .nav-item {
    flex: 1;
    padding: 6px 0;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--chrome-text-muted);
    background: transparent;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: color 0.2s, background 0.2s;
  }

  .nav-item:hover {
    color: var(--chrome-text);
  }

  .nav-item.active {
    color: var(--accent);
    background: rgba(232, 115, 58, 0.08);
  }

  .sidebar-content {
    flex: 1;
    overflow-y: auto;
    padding: 0 8px;
  }

  .section-label {
    font-family: 'Outfit', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    color: var(--chrome-text-muted);
    padding: 8px 8px 6px;
  }

  .session-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .session-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 10px 16px 10px 12px;
    border: none;
    border-left: 3px solid transparent;
    background: transparent;
    cursor: pointer;
    text-align: left;
    font-family: 'Outfit', sans-serif;
    border-radius: 0 6px 6px 0;
    transition: border-color 0.2s, background 0.2s;
    width: 100%;
  }

  .session-item:hover {
    background: rgba(255, 255, 255, 0.03);
  }

  .session-item.active {
    border-left-color: var(--accent);
    background: rgba(232, 115, 58, 0.06);
  }

  .session-type {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--chrome-text-muted);
  }

  .session-topic {
    font-size: 13px;
    font-weight: 500;
    color: var(--chrome-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .session-meta {
    font-size: 11px;
    color: var(--chrome-text-muted);
  }

  .empty-state {
    padding: 16px 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    color: var(--chrome-text-muted);
    text-align: center;
  }

  /* Skeleton loading */
  .skeleton-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 4px 0;
  }

  .skeleton-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 10px 12px;
  }

  .skeleton-line {
    height: 10px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 4px;
    animation: shimmer 1.5s ease-in-out infinite;
  }

  .skeleton-line.short {
    width: 40%;
    height: 8px;
  }

  @keyframes shimmer {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 0.8; }
  }

  @media (max-width: 768px) {
    .sidebar {
      position: fixed;
      left: 0;
      top: 0;
      z-index: 100;
      width: 240px;
      transform: translateX(0);
      transition: transform 0.2s ease-out;
    }

    :global(.sidebar-collapsed) .sidebar {
      transform: translateX(-100%);
    }
  }
</style>
