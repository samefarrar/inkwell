<script lang="ts">
  import { ws } from '$lib/ws';
  import { session } from '$lib/stores/session.svelte';

  const taskTypes = [
    { value: 'essay', label: 'Essay' },
    { value: 'review', label: 'Review' },
    { value: 'newsletter', label: 'Newsletter' },
    { value: 'landing_page', label: 'Landing Page' },
    { value: 'blog_post', label: 'Blog Post' }
  ];

  let selectedType = $state('essay');
  let topic = $state('');

  function startInterview() {
    if (!topic.trim()) return;
    session.startInterview(selectedType, topic.trim());
    ws.send({ type: 'task.select', task_type: selectedType, topic: topic.trim() });
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && topic.trim()) {
      startInterview();
    }
  }
</script>

<div class="task-selector">
  <div class="hero">
    <h1>What are we writing?</h1>
    <p class="subtitle">I'll interview you to extract the good stuff, then draft three angles for you to choose from.</p>
  </div>

  <div class="form">
    <div class="field">
      <label for="task-type">Type</label>
      <select id="task-type" bind:value={selectedType}>
        {#each taskTypes as t}
          <option value={t.value}>{t.label}</option>
        {/each}
      </select>
    </div>

    <div class="field">
      <label for="topic">Topic</label>
      <input
        id="topic"
        type="text"
        bind:value={topic}
        onkeydown={handleKeydown}
        placeholder="e.g., Restaurant review of Burnt Orange Brighton"
      />
    </div>

    <button class="start-btn" onclick={startInterview} disabled={!topic.trim()}>
      Start Interview
    </button>
  </div>
</div>

<style>
  .task-selector {
    max-width: 560px;
    margin: 0 auto;
    padding: 80px 24px;
  }

  .hero {
    margin-bottom: 48px;
  }

  h1 {
    font-size: 32px;
    font-weight: 700;
    color: var(--text-primary, #1a1a1a);
    margin: 0 0 12px;
  }

  .subtitle {
    font-size: 16px;
    color: var(--text-secondary, #666);
    line-height: 1.5;
    margin: 0;
  }

  .form {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-secondary, #666);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  select,
  input {
    padding: 12px 16px;
    border: 1px solid var(--border, #e0e0e0);
    border-radius: 8px;
    font-size: 16px;
    color: var(--text-primary, #1a1a1a);
    background: var(--bg-surface, #fff);
    transition: border-color 0.15s;
  }

  select:focus,
  input:focus {
    outline: none;
    border-color: var(--accent, #f97316);
  }

  .start-btn {
    padding: 14px 24px;
    background: var(--accent, #f97316);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
    margin-top: 8px;
  }

  .start-btn:hover:not(:disabled) {
    opacity: 0.9;
  }

  .start-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
