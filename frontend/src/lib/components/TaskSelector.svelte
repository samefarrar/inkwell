<script lang="ts">
  import { goto } from '$app/navigation';
  import { ws } from '$lib/ws.svelte';
  import { session } from '$lib/stores/session.svelte';
  import { styles } from '$lib/stores/styles.svelte';
  import VoiceButton from '$lib/components/VoiceButton.svelte';

  let { onResume: _, lastStyleId = null }: {
    onResume: (sessionId: number) => void;
    lastStyleId?: number | null;
  } = $props();

  const taskTypes = [
    { value: 'essay', label: 'Essay' },
    { value: 'review', label: 'Review' },
    { value: 'newsletter', label: 'Newsletter' },
    { value: 'blog_post', label: 'Blog Post' },
    { value: 'landing_page', label: 'Landing Page' }
  ];

  let selectedType = $state('essay');
  let topic = $state('');

  // Pre-select last used style, falling back to first available
  let selectedStyleId = $state<number | null>(null);

  // Initialize once styles are available, respecting lastStyleId preference
  $effect(() => {
    if (selectedStyleId === null && styles.styles.length > 0) {
      selectedStyleId = lastStyleId ?? styles.styles[0].id;
    }
  });

  const selectedStyleName = $derived(
    styles.styles.find((s) => s.id === selectedStyleId)?.name ?? null
  );

  function startWriting() {
    if (!topic.trim()) return;
    session.startInterview(selectedType, topic.trim());
    ws.send({
      type: 'task.select',
      task_type: selectedType,
      topic: topic.trim(),
      style_id: selectedStyleId
    });
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey && topic.trim()) {
      e.preventDefault();
      startWriting();
    }
  }
</script>

<div class="task-selector">
  <div class="anim" style="animation-delay: 0ms">
    <h1 class="headline">
      What are we <span class="headline-accent">writing</span> today?
    </h1>
  </div>

  <div class="input-card anim" style="animation-delay: 120ms">
    <textarea
      bind:value={topic}
      placeholder="I'm writing a piece about..."
      rows="3"
      onkeydown={handleKeydown}
    ></textarea>

    <div class="task-pills">
      {#each taskTypes as t}
        <button
          class="task-pill"
          class:selected={selectedType === t.value}
          onclick={() => (selectedType = t.value)}
        >
          {t.label}
        </button>
      {/each}
    </div>

    <!-- Style picker -->
    <div class="style-row">
      {#if styles.styles.length === 0}
        <button class="style-cta" onclick={() => goto('/styles')}>
          Add your voice →
        </button>
      {:else}
        <span class="style-label">Writing as</span>
        <div class="style-select-wrap">
          <select
            class="style-select"
            bind:value={selectedStyleId}
          >
            {#each styles.styles as s (s.id)}
              <option value={s.id}>{s.name}</option>
            {/each}
          </select>
        </div>
      {/if}
    </div>

    <div class="toolbar">
      <VoiceButton onTranscript={(text) => (topic += (topic ? ' ' : '') + text)} />
      <button
        class="start-writing-btn"
        onclick={startWriting}
        disabled={!topic.trim()}
      >
        Start writing
      </button>
    </div>
  </div>
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
    font-size: 36px;
    font-weight: 400;
    color: var(--chrome-text);
    margin: 0 0 32px;
    text-align: center;
  }

  .headline-accent {
    background: var(--accent);
    color: white;
    padding: 2px 10px;
    border-radius: 6px;
    display: inline-block;
    line-height: 1.2;
  }

  /* Unified input card */
  .input-card {
    width: 100%;
    max-width: 560px;
    background: var(--paper);
    border: 1px solid var(--paper-border);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.12);
  }

  .input-card textarea {
    width: 100%;
    border: none;
    background: transparent;
    padding: 20px 24px 12px;
    font-family: 'Newsreader', serif;
    font-size: 17px;
    line-height: 1.6;
    color: var(--ink);
    resize: none;
    min-height: 80px;
  }

  .input-card textarea::placeholder {
    color: var(--ink-muted);
  }

  .input-card textarea:focus {
    outline: none;
  }

  /* Task pills inside card */
  .task-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 0 20px 12px;
  }

  .task-pill {
    padding: 4px 12px;
    border-radius: 16px;
    border: 1px solid var(--paper-border);
    background: transparent;
    color: var(--ink-muted);
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
  }

  .task-pill:hover {
    border-color: var(--ink-secondary);
    color: var(--ink-secondary);
  }

  .task-pill.selected {
    background: var(--accent);
    color: white;
    border-color: var(--accent);
  }

  /* Style picker row */
  .style-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 20px 10px;
  }

  .style-label {
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    color: var(--ink-muted);
    flex-shrink: 0;
  }

  .style-select-wrap {
    position: relative;
    flex: 1;
    max-width: 200px;
  }

  .style-select {
    appearance: none;
    width: 100%;
    background: transparent;
    border: 1px solid var(--paper-border);
    border-radius: 20px;
    padding: 3px 24px 3px 10px;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    font-weight: 500;
    color: var(--ink);
    cursor: pointer;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' stroke='%23999' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 8px center;
  }

  .style-select:focus {
    outline: none;
    border-color: var(--accent);
  }

  .style-cta {
    background: none;
    border: none;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    font-weight: 500;
    color: var(--accent);
    cursor: pointer;
    padding: 0;
    transition: opacity 0.15s;
  }

  .style-cta:hover {
    opacity: 0.8;
  }

  /* Toolbar */
  .toolbar {
    display: flex;
    align-items: center;
    padding: 10px 16px;
    border-top: 1px solid var(--paper-border);
    gap: 8px;
  }

  .start-writing-btn {
    margin-left: auto;
    padding: 6px 18px;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 20px;
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .start-writing-btn:hover:not(:disabled) {
    opacity: 0.9;
  }

  .start-writing-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
</style>
