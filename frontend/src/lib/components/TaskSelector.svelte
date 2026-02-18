<script lang="ts">
  import { onMount } from 'svelte';
  import { ws } from '$lib/ws.svelte';
  import { session } from '$lib/stores/session.svelte';

  interface SessionSummary {
    id: number;
    task_type: string;
    topic: string;
    status: string;
    draft_count: number;
    max_round: number;
    created_at: string;
  }

  let { onResume }: {
    onResume: (sessionId: number) => void;
  } = $props();

  const taskTypes = [
    { value: 'essay', label: 'Essay' },
    { value: 'review', label: 'Review' },
    { value: 'newsletter', label: 'Newsletter' },
    { value: 'landing_page', label: 'Landing Page' },
    { value: 'blog_post', label: 'Blog Post' }
  ];

  let selectedType = $state('essay');
  let topic = $state('');
  let sessions = $state<SessionSummary[]>([]);

  onMount(() => {
    fetch('http://localhost:8000/api/sessions')
      .then((r) => r.json())
      .then((data: SessionSummary[]) => {
        sessions = data;
      })
      .catch(() => {});
  });

  function startInterview() {
    if (!topic.trim()) return;
    session.startInterview(selectedType, topic.trim());
    ws.send({ type: 'task.select', task_type: selectedType, topic: topic.trim() });
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

<div class="task-selector">
  <div class="anim" style="animation-delay: 0ms">
    <h1 class="headline">What are we writing?</h1>
  </div>

  <p class="subtitle anim" style="animation-delay: 80ms">
    I'll interview you to extract the good stuff, then draft three angles.
  </p>

  <div class="pills anim" style="animation-delay: 160ms">
    {#each taskTypes as t}
      <button
        class="pill"
        class:selected={selectedType === t.value}
        onclick={() => (selectedType = t.value)}
      >
        {t.label}
      </button>
    {/each}
  </div>

  <div class="anim" style="animation-delay: 240ms">
    <textarea
      bind:value={topic}
      placeholder="What's the topic? e.g., Restaurant review of Burnt Orange Brighton"
      rows="3"
    ></textarea>
  </div>

  <button
    class="start-btn anim"
    style="animation-delay: 320ms"
    onclick={startInterview}
    disabled={!topic.trim()}
  >
    Start Interview
  </button>

  {#if sessions.length > 0}
    <div class="sessions-section anim" style="animation-delay: 400ms">
      <h3 class="sessions-heading">Past sessions</h3>
      <div class="sessions-list">
        {#each sessions as s}
          <button class="session-card" onclick={() => onResume(s.id)}>
            <span class="session-topic">{s.topic}</span>
            <span class="session-meta">
              <span class="type-pill">{taskTypeLabels[s.task_type] ?? s.task_type}</span>
              {#if s.draft_count > 0}
                {s.draft_count} draft{s.draft_count === 1 ? '' : 's'}
              {:else}
                interview
              {/if}
              {#if s.max_round > 0}
                &middot; round {s.max_round}
              {/if}
              &middot; {relativeDate(s.created_at)}
            </span>
          </button>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .task-selector {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: calc(100vh - 48px);
    padding: 40px 24px;
    background: radial-gradient(ellipse at center, rgba(232, 115, 58, 0.04) 0%, transparent 70%);
  }

  .anim {
    animation: slideUp 0.4s ease-out both;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(16px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .headline {
    font-family: 'Newsreader', serif;
    font-style: italic;
    font-size: 40px;
    font-weight: 400;
    color: var(--chrome-text);
    margin: 0;
    text-align: center;
  }

  .subtitle {
    font-family: 'Outfit', sans-serif;
    font-size: 16px;
    color: var(--chrome-text-muted);
    margin: 8px 0 36px;
    text-align: center;
  }

  /* Pill buttons */
  .pills {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
    margin-bottom: 28px;
  }

  .pill {
    padding: 8px 20px;
    border-radius: 24px;
    border: 1px solid var(--chrome-border);
    background: transparent;
    color: var(--chrome-text-muted);
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s, color 0.2s, box-shadow 0.2s, border-color 0.2s;
  }

  .pill:hover {
    border-color: var(--chrome-text-muted);
    color: var(--chrome-text);
  }

  .pill.selected {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
    box-shadow: 0 0 12px var(--accent-glow);
  }

  /* Topic textarea */
  textarea {
    width: 100%;
    max-width: 480px;
    min-height: 80px;
    padding: 16px 20px;
    background: var(--paper);
    border: 1px solid var(--paper-border);
    border-radius: 12px;
    font-family: 'Newsreader', serif;
    font-size: 16px;
    line-height: 1.5;
    color: var(--ink);
    resize: vertical;
    margin-bottom: 20px;
  }

  textarea::placeholder {
    color: var(--ink-muted);
  }

  textarea:focus {
    outline: none;
    border-color: var(--accent);
  }

  /* Start button */
  .start-btn {
    width: 100%;
    max-width: 480px;
    padding: 16px;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 12px;
    font-family: 'Outfit', sans-serif;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s, box-shadow 0.2s;
  }

  .start-btn:hover:not(:disabled) {
    opacity: 0.9;
  }

  .start-btn:not(:disabled) {
    animation: slideUp 0.4s ease-out both, glowPulse 2s ease-in-out infinite 0.4s;
  }

  .start-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  @keyframes glowPulse {
    0%, 100% { box-shadow: 0 0 0 rgba(232, 115, 58, 0); }
    50% { box-shadow: 0 0 20px var(--accent-glow); }
  }

  /* Sessions list */
  .sessions-section {
    margin-top: 32px;
    width: 100%;
    max-width: 480px;
  }

  .sessions-heading {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: var(--chrome-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 12px;
  }

  .sessions-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 240px;
    overflow-y: auto;
  }

  .session-card {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 12px 16px;
    background: transparent;
    border: 1px solid var(--chrome-border);
    border-radius: 10px;
    color: var(--chrome-text);
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    cursor: pointer;
    text-align: left;
    transition: color 0.2s, border-color 0.2s, background 0.2s;
  }

  .session-card:hover {
    border-color: var(--accent);
    background: rgba(232, 115, 58, 0.04);
  }

  .session-topic {
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .session-meta {
    font-size: 12px;
    color: var(--chrome-text-muted);
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }

  .type-pill {
    padding: 2px 8px;
    border-radius: 10px;
    background: var(--chrome-surface);
    font-size: 11px;
    font-weight: 500;
  }
</style>
