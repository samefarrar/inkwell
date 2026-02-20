<script lang="ts">
  import { BASE_API_URL } from '$lib/config';
  import { styles } from '$lib/stores/styles.svelte';

  let { onDismiss }: { onDismiss: () => void } = $props();

  let content = $state('');
  let saving = $state(false);

  async function handleSave() {
    if (!content.trim()) return;
    saving = true;
    try {
      // Create a "My Writing" style
      const style = await styles.createStyle('My Writing', '');
      if (!style) throw new Error('Failed to create style');

      // Add the pasted text as a sample
      await styles.addSample(style.id, 'My Writing', content.trim());

      // Mark onboarding complete
      await fetch(`${BASE_API_URL}/api/preferences/onboarding`, { method: 'POST' });
      onDismiss();
    } catch {
      // Silently handle — user can skip
    } finally {
      saving = false;
    }
  }

  async function handleSkip() {
    await fetch(`${BASE_API_URL}/api/preferences/onboarding`, { method: 'POST' });
    onDismiss();
  }
</script>

<div class="onboarding-card">
  <div class="onboarding-header">
    <span class="onboarding-badge">Get started</span>
    <h2 class="onboarding-title">Paste something you've written</h2>
    <p class="onboarding-subtitle">
      Inkwell will use it to match your voice from the first session.
      2–3 pieces works best.
    </p>
  </div>

  <textarea
    bind:value={content}
    placeholder="Paste a blog post, essay, or any piece you're proud of..."
    rows="6"
    class="onboarding-textarea"
  ></textarea>

  <div class="onboarding-actions">
    <button
      class="save-btn"
      onclick={handleSave}
      disabled={!content.trim() || saving}
    >
      {saving ? 'Saving…' : 'Save to my profile'}
    </button>
    <button class="skip-btn" onclick={handleSkip}>Skip for now</button>
  </div>
</div>

<style>
  .onboarding-card {
    width: 100%;
    max-width: 560px;
    margin: 0 auto 32px;
    padding: 24px;
    background: var(--chrome-surface);
    border: 1px solid rgba(232, 115, 58, 0.25);
    border-radius: 16px;
    animation: fadeIn 0.3s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .onboarding-badge {
    display: inline-block;
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--accent);
    background: rgba(232, 115, 58, 0.1);
    padding: 2px 8px;
    border-radius: 20px;
    margin-bottom: 10px;
  }

  .onboarding-title {
    font-family: 'Newsreader', serif;
    font-style: italic;
    font-size: 22px;
    font-weight: 400;
    color: var(--chrome-text);
    margin: 0 0 6px;
  }

  .onboarding-subtitle {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    color: var(--chrome-text-muted);
    margin: 0 0 16px;
    line-height: 1.5;
  }

  .onboarding-textarea {
    width: 100%;
    background: var(--chrome);
    border: 1px solid var(--chrome-border);
    border-radius: 10px;
    padding: 12px 14px;
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    color: var(--chrome-text);
    resize: vertical;
    line-height: 1.6;
    box-sizing: border-box;
    margin-bottom: 16px;
  }

  .onboarding-textarea::placeholder {
    color: var(--chrome-text-muted);
  }

  .onboarding-textarea:focus {
    outline: none;
    border-color: var(--accent);
  }

  .onboarding-actions {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .save-btn {
    padding: 8px 20px;
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

  .skip-btn {
    background: none;
    border: none;
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    color: var(--chrome-text-muted);
    cursor: pointer;
    padding: 0;
    transition: color 0.15s;
  }

  .skip-btn:hover {
    color: var(--chrome-text);
  }
</style>
