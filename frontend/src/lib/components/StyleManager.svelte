<script lang="ts">
  import { goto } from '$app/navigation';
  import { styles } from '$lib/stores/styles.svelte';

  let showCreate = $state(false);
  let newName = $state('');
  let newDesc = $state('');

  async function handleCreate() {
    if (!newName.trim()) return;
    const style = await styles.createStyle(newName.trim(), newDesc.trim());
    if (style) {
      newName = '';
      newDesc = '';
      showCreate = false;
      goto(`/styles/${style.id}`);
    }
  }

  function openStyle(id: number) {
    goto(`/styles/${id}`);
  }

  function formatDate(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
</script>

<div class="style-manager">
  <div class="header">
    <h2>Writing Styles</h2>
    <button class="create-btn" onclick={() => (showCreate = !showCreate)}>
      {showCreate ? 'Cancel' : '+ New Style'}
    </button>
  </div>

  {#if showCreate}
    <div class="create-form">
      <input
        type="text"
        bind:value={newName}
        placeholder="Style name (e.g. 'Newsletter voice')"
        maxlength="200"
      />
      <textarea
        bind:value={newDesc}
        placeholder="Brief description of this writing style..."
        rows="2"
        maxlength="2000"
      ></textarea>
      <button class="save-btn" onclick={handleCreate} disabled={!newName.trim()}>
        Create Style
      </button>
    </div>
  {/if}

  {#if styles.loading}
    <div class="loading">
      {#each [1, 2, 3] as _}
        <div class="skeleton-card"></div>
      {/each}
    </div>
  {:else if styles.styles.length === 0}
    <div class="empty">
      <p class="empty-title">No styles yet</p>
      <p class="empty-desc">
        Create a writing style and add samples to teach Inkwell your voice.
      </p>
    </div>
  {:else}
    <div class="style-list">
      {#each styles.styles as style}
        <button class="style-card" onclick={() => openStyle(style.id)}>
          <div class="style-name">{style.name}</div>
          {#if style.description}
            <div class="style-desc">{style.description}</div>
          {/if}
          <div class="style-meta">
            Updated {formatDate(style.updated_at)}
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .style-manager {
    max-width: 640px;
    margin: 0 auto;
    padding: 48px 24px;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
  }

  h2 {
    font-family: 'Newsreader', serif;
    font-style: italic;
    font-size: 28px;
    font-weight: 400;
    color: var(--chrome-text);
    margin: 0;
  }

  .create-btn {
    padding: 6px 16px;
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

  .create-btn:hover {
    opacity: 0.9;
  }

  .create-form {
    background: var(--chrome-surface);
    border: 1px solid var(--chrome-border);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 24px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    animation: slideDown 0.2s ease-out;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .create-form input,
  .create-form textarea {
    width: 100%;
    background: var(--chrome);
    border: 1px solid var(--chrome-border);
    border-radius: 8px;
    padding: 10px 12px;
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    color: var(--chrome-text);
    resize: none;
  }

  .create-form input::placeholder,
  .create-form textarea::placeholder {
    color: var(--chrome-text-muted);
  }

  .create-form input:focus,
  .create-form textarea:focus {
    outline: none;
    border-color: var(--accent);
  }

  .save-btn {
    align-self: flex-end;
    padding: 6px 16px;
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

  .save-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .loading {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .skeleton-card {
    height: 72px;
    background: var(--chrome-surface);
    border-radius: 12px;
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.6; }
    50% { opacity: 0.3; }
  }

  .empty {
    text-align: center;
    padding: 48px 0;
  }

  .empty-title {
    font-family: 'Newsreader', serif;
    font-style: italic;
    font-size: 18px;
    color: var(--chrome-text-muted);
    margin: 0 0 8px;
  }

  .empty-desc {
    font-size: 13px;
    color: var(--chrome-text-muted);
    margin: 0;
  }

  .style-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .style-card {
    display: block;
    width: 100%;
    text-align: left;
    background: var(--chrome-surface);
    border: 1px solid var(--chrome-border);
    border-radius: 12px;
    padding: 14px 16px;
    cursor: pointer;
    transition: border-color 0.15s;
  }

  .style-card:hover {
    border-color: var(--accent);
  }

  .style-name {
    font-weight: 600;
    font-size: 14px;
    color: var(--chrome-text);
    margin-bottom: 4px;
  }

  .style-desc {
    font-size: 13px;
    color: var(--chrome-text-muted);
    margin-bottom: 6px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .style-meta {
    font-size: 11px;
    color: var(--chrome-text-muted);
    opacity: 0.7;
  }
</style>
