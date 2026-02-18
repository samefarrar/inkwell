<script lang="ts">
  import { styles } from '$lib/stores/styles.svelte';
  import { session } from '$lib/stores/session.svelte';

  let editingName = $state(false);
  let editingDesc = $state(false);
  let nameInput = $state('');
  let descInput = $state('');

  let showPaste = $state(false);
  let pasteTitle = $state('');
  let pasteContent = $state('');

  let fileInput = $state<HTMLInputElement>();
  let confirmDelete = $state<number | null>(null);

  function goBack() {
    styles.clearCurrent();
    session.setAppView('styles');
  }

  function startEditName() {
    nameInput = styles.currentStyle?.name ?? '';
    editingName = true;
  }

  async function saveName() {
    if (!styles.currentStyle || !nameInput.trim()) return;
    await styles.updateStyle(styles.currentStyle.id, nameInput.trim());
    editingName = false;
  }

  function startEditDesc() {
    descInput = styles.currentStyle?.description ?? '';
    editingDesc = true;
  }

  async function saveDesc() {
    if (!styles.currentStyle) return;
    await styles.updateStyle(styles.currentStyle.id, undefined, descInput.trim());
    editingDesc = false;
  }

  async function handlePaste() {
    if (!styles.currentStyle || !pasteContent.trim()) return;
    await styles.addSample(styles.currentStyle.id, pasteTitle.trim(), pasteContent.trim());
    pasteTitle = '';
    pasteContent = '';
    showPaste = false;
  }

  function triggerUpload() {
    fileInput?.click();
  }

  async function handleFileChange(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file || !styles.currentStyle) return;
    await styles.uploadSample(styles.currentStyle.id, file);
    input.value = '';
  }

  async function handleDeleteSample(sampleId: number) {
    if (!styles.currentStyle) return;
    if (confirmDelete === sampleId) {
      await styles.deleteSample(styles.currentStyle.id, sampleId);
      confirmDelete = null;
    } else {
      confirmDelete = sampleId;
    }
  }

  async function handleDeleteStyle() {
    if (!styles.currentStyle) return;
    await styles.deleteStyle(styles.currentStyle.id);
    goBack();
  }

</script>

<div class="style-editor">
  {#if styles.currentStyleLoading}
    <div class="loading">Loading...</div>
  {:else if styles.currentStyle}
    <div class="top-bar">
      <button class="back-btn" onclick={goBack}>
        ← Styles
      </button>
      <button class="delete-style-btn" onclick={handleDeleteStyle}>
        Delete Style
      </button>
    </div>

    <div class="style-header">
      {#if editingName}
        <div class="inline-edit">
          <input
            type="text"
            bind:value={nameInput}
            maxlength="200"
            onkeydown={(e) => e.key === 'Enter' && saveName()}
          />
          <button class="inline-save" onclick={saveName}>Save</button>
          <button class="inline-cancel" onclick={() => (editingName = false)}>Cancel</button>
        </div>
      {:else}
        <h2 class="style-title" ondblclick={startEditName}>
          {styles.currentStyle.name}
          <button class="edit-icon" onclick={startEditName} title="Edit name">
            &#9998;
          </button>
        </h2>
      {/if}

      {#if editingDesc}
        <div class="inline-edit">
          <textarea
            bind:value={descInput}
            rows="2"
            maxlength="2000"
            onkeydown={(e) => e.key === 'Enter' && !e.shiftKey && saveDesc()}
          ></textarea>
          <button class="inline-save" onclick={saveDesc}>Save</button>
          <button class="inline-cancel" onclick={() => (editingDesc = false)}>Cancel</button>
        </div>
      {:else}
        <p class="style-description" ondblclick={startEditDesc}>
          {styles.currentStyle.description || 'No description — double-click to add one.'}
        </p>
      {/if}
    </div>

    <div class="samples-section">
      <div class="samples-header">
        <h3>Writing Samples</h3>
        <div class="sample-actions">
          <button class="action-btn" onclick={() => (showPaste = !showPaste)}>
            {showPaste ? 'Cancel' : 'Paste text'}
          </button>
          <button class="action-btn" onclick={triggerUpload}>Upload file</button>
          <input
            bind:this={fileInput}
            type="file"
            accept=".txt,.md"
            onchange={handleFileChange}
            style="display:none"
          />
        </div>
      </div>

      {#if showPaste}
        <div class="paste-form">
          <input
            type="text"
            bind:value={pasteTitle}
            placeholder="Sample title (optional)"
            maxlength="500"
          />
          <textarea
            bind:value={pasteContent}
            placeholder="Paste your writing sample here..."
            rows="6"
          ></textarea>
          <button class="save-btn" onclick={handlePaste} disabled={!pasteContent.trim()}>
            Add Sample
          </button>
        </div>
      {/if}

      {#if styles.currentStyle.samples.length === 0}
        <div class="empty-samples">
          <p>No samples yet. Add writing samples to help Inkwell learn your style.</p>
        </div>
      {:else}
        <div class="sample-list">
          {#each styles.currentStyle.samples as sample}
            <div class="sample-card">
              <div class="sample-info">
                <span class="sample-title">
                  {sample.title || 'Untitled'}
                </span>
                <span class="sample-meta">
                  {sample.word_count.toLocaleString()} words · {sample.source_type}
                </span>
              </div>
              <div class="sample-preview">
                {sample.content.slice(0, 200)}{sample.content.length > 200 ? '...' : ''}
              </div>
              <button
                class="remove-btn"
                class:confirming={confirmDelete === sample.id}
                onclick={() => handleDeleteSample(sample.id)}
              >
                {confirmDelete === sample.id ? 'Confirm?' : 'Remove'}
              </button>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .style-editor {
    max-width: 680px;
    margin: 0 auto;
    padding: 32px 24px;
  }

  .loading {
    text-align: center;
    padding: 48px;
    color: var(--chrome-text-muted);
  }

  .top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
  }

  .back-btn {
    background: none;
    border: none;
    color: var(--chrome-text-muted);
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    cursor: pointer;
    padding: 4px 0;
    transition: color 0.15s;
  }

  .back-btn:hover {
    color: var(--chrome-text);
  }

  .delete-style-btn {
    background: none;
    border: 1px solid #dc2626;
    color: #dc2626;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    padding: 4px 12px;
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.15s;
  }

  .delete-style-btn:hover {
    background: #dc2626;
    color: white;
  }

  .style-header {
    margin-bottom: 32px;
  }

  .style-title {
    font-family: 'Newsreader', serif;
    font-style: italic;
    font-size: 28px;
    font-weight: 400;
    color: var(--chrome-text);
    margin: 0 0 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .edit-icon {
    background: none;
    border: none;
    color: var(--chrome-text-muted);
    font-size: 14px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.15s;
    padding: 0;
  }

  .style-title:hover .edit-icon {
    opacity: 1;
  }

  .style-description {
    font-size: 14px;
    color: var(--chrome-text-muted);
    margin: 0;
    cursor: pointer;
  }

  .inline-edit {
    display: flex;
    gap: 8px;
    align-items: flex-start;
  }

  .inline-edit input,
  .inline-edit textarea {
    flex: 1;
    background: var(--chrome-surface);
    border: 1px solid var(--accent);
    border-radius: 8px;
    padding: 8px 12px;
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    color: var(--chrome-text);
    resize: none;
  }

  .inline-edit input:focus,
  .inline-edit textarea:focus {
    outline: none;
  }

  .inline-save,
  .inline-cancel {
    background: none;
    border: 1px solid var(--chrome-border);
    color: var(--chrome-text-muted);
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    padding: 4px 10px;
    border-radius: 16px;
    cursor: pointer;
    white-space: nowrap;
  }

  .inline-save {
    border-color: var(--accent);
    color: var(--accent);
  }

  .samples-section {
    border-top: 1px solid var(--chrome-border);
    padding-top: 24px;
  }

  .samples-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  h3 {
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: var(--chrome-text);
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .sample-actions {
    display: flex;
    gap: 8px;
  }

  .action-btn {
    padding: 4px 12px;
    background: var(--chrome-surface);
    border: 1px solid var(--chrome-border);
    border-radius: 16px;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    color: var(--chrome-text-muted);
    cursor: pointer;
    transition: border-color 0.15s;
  }

  .action-btn:hover {
    border-color: var(--accent);
    color: var(--chrome-text);
  }

  .paste-form {
    background: var(--chrome-surface);
    border: 1px solid var(--chrome-border);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
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

  .paste-form input,
  .paste-form textarea {
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

  .paste-form input::placeholder,
  .paste-form textarea::placeholder {
    color: var(--chrome-text-muted);
  }

  .paste-form input:focus,
  .paste-form textarea:focus {
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

  .empty-samples {
    text-align: center;
    padding: 32px;
    color: var(--chrome-text-muted);
    font-size: 13px;
  }

  .sample-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .sample-card {
    background: var(--chrome-surface);
    border: 1px solid var(--chrome-border);
    border-radius: 10px;
    padding: 12px 14px;
    position: relative;
  }

  .sample-info {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 6px;
  }

  .sample-title {
    font-weight: 600;
    font-size: 13px;
    color: var(--chrome-text);
  }

  .sample-meta {
    font-size: 11px;
    color: var(--chrome-text-muted);
  }

  .sample-preview {
    font-size: 12px;
    color: var(--chrome-text-muted);
    line-height: 1.5;
    max-height: 54px;
    overflow: hidden;
  }

  .remove-btn {
    position: absolute;
    top: 10px;
    right: 10px;
    background: none;
    border: none;
    color: var(--chrome-text-muted);
    font-family: 'Outfit', sans-serif;
    font-size: 11px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.15s, color 0.15s;
  }

  .sample-card:hover .remove-btn {
    opacity: 1;
  }

  .remove-btn.confirming {
    opacity: 1;
    color: #dc2626;
  }
</style>
