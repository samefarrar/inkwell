<script lang="ts">
  import { ws } from '$lib/ws.svelte';
  import { session } from '$lib/stores/session.svelte';
  import { drafts } from '$lib/stores/drafts.svelte';
  import { tick } from 'svelte';
  import VoiceButton from '$lib/components/VoiceButton.svelte';

  let input = $state('');
  let messagesEnd: HTMLDivElement;

  $effect(() => {
    if (session.messages.length) {
      tick().then(() => {
        messagesEnd?.scrollIntoView({ behavior: 'smooth' });
      });
    }
  });

  function sendAnswer() {
    const answer = input.trim();
    if (!answer) return;

    session.addMessage({ role: 'user', content: answer });
    ws.send({ type: 'interview.answer', answer });
    input = '';
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendAnswer();
    }
  }

  function startDrafting() {
    session.goToDrafts();
    drafts.reset();
  }

  function questionCount(): number {
    return session.messages.filter((m) => m.role === 'ai').length;
  }
</script>

<div class="interview">
  <!-- Progress dots -->
  <div class="progress">
    {#each Array(5) as _, i}
      <span class="dot" class:filled={i < questionCount()}></span>
    {/each}
  </div>

  <div class="messages">
    {#each session.messages as msg, idx}
      {#if msg.role === 'thought' && msg.thought}
        {@const isFirst = !session.messages.slice(0, idx).some((m) => m.role === 'thought')}
        <div class="thought-block">
          <details open={isFirst}>
            <summary class="thought-label">Thinking</summary>
            <p class="assessment">{msg.thought.assessment}</p>
            {#if msg.thought.missing.length > 0}
              <div class="missing">
                <span class="missing-label">Still exploring: </span>
                <span class="missing-items">{msg.thought.missing.join(', ')}</span>
              </div>
            {/if}
            {#if msg.thought.sufficient}
              <span class="sufficient-badge">Ready to draft</span>
            {/if}
          </details>
        </div>
      {:else if msg.role === 'search' && msg.search}
        <div class="search-card">
          <div class="search-header">
            <span class="search-icon">&#x1F50D;</span>
            <span class="search-query">{msg.search.query}</span>
          </div>
          <p class="search-summary">{msg.search.summary}</p>
        </div>
      {:else if msg.role === 'status'}
        <div class="status-msg">{msg.content}</div>
      {:else if msg.role === 'ai'}
        <div class="ai-msg">
          <span class="msg-label">WRITING PARTNER</span>
          <p class="msg-text">{msg.content}</p>
        </div>
      {:else if msg.role === 'user'}
        <div class="user-msg">
          <span class="msg-label user-label">YOU</span>
          <div class="user-block">
            <p class="msg-text">{msg.content}</p>
          </div>
        </div>
      {/if}
    {/each}
    <div bind:this={messagesEnd}></div>
  </div>

  {#if session.readyToDraft}
    <div class="ready-bar">
      <span class="ready-text">I have enough material to write three drafts.</span>
      <button class="draft-btn" onclick={startDrafting}>Start Writing</button>
    </div>
  {:else}
    <div class="input-area">
      <textarea
        bind:value={input}
        onkeydown={handleKeydown}
        placeholder="Share your thoughts..."
        rows="5"
      ></textarea>
      <div class="input-actions">
        <VoiceButton onTranscript={(text) => (input += (input ? ' ' : '') + text)} />
        <button class="send-btn" onclick={sendAnswer} disabled={!input.trim()}>
          Send
        </button>
      </div>
    </div>
  {/if}
</div>

<style>
  .interview {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 48px);
    width: 100%;
    max-width: 800px;
    margin: 0 auto;
    padding: 24px 32px 0;
  }

  /* Progress dots */
  .progress {
    display: flex;
    justify-content: center;
    gap: 8px;
    padding-bottom: 24px;
    flex-shrink: 0;
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--chrome-border);
    transition: background 0.3s;
  }

  .dot.filled {
    background: var(--accent);
  }

  /* Messages */
  .messages {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 24px;
    padding-bottom: 24px;
    min-height: 0;
  }

  /* AI messages */
  .ai-msg {
    max-width: 100%;
  }

  .msg-label {
    display: block;
    font-family: 'Outfit', sans-serif;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--accent);
    margin-bottom: 6px;
  }

  .user-label {
    color: var(--chrome-text-muted);
  }

  .ai-msg .msg-text {
    font-family: 'Outfit', sans-serif;
    font-weight: 500;
    font-size: 18px;
    line-height: 1.5;
    color: var(--chrome-text);
    margin: 0;
  }

  /* User messages */
  .user-msg {
    max-width: 100%;
  }

  .user-block {
    background: var(--paper);
    border-radius: 12px;
    padding: 20px;
  }

  .user-block .msg-text {
    font-family: 'Newsreader', serif;
    font-size: 16px;
    line-height: 1.6;
    color: var(--ink);
    margin: 0;
  }

  /* Thought blocks — marginalia style */
  .thought-block {
    background: var(--thought-bg);
    border-left: 3px solid var(--thought-border);
    padding: 12px 16px;
    border-radius: 0 8px 8px 0;
  }

  .thought-block summary {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: #d4a574;
    cursor: pointer;
    list-style: none;
  }

  .thought-block summary::-webkit-details-marker {
    display: none;
  }

  .thought-block summary::before {
    content: '\25B8  ';
  }

  .thought-block details[open] summary::before {
    content: '\25BE  ';
  }

  .assessment {
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    color: var(--chrome-text);
    line-height: 1.5;
    margin: 8px 0;
  }

  .missing {
    margin: 8px 0;
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
  }

  .missing-label {
    font-weight: 600;
    color: var(--chrome-text-muted);
  }

  .missing-items {
    color: var(--chrome-text-muted);
  }

  .sufficient-badge {
    display: inline-block;
    padding: 3px 10px;
    background: rgba(74, 222, 128, 0.15);
    color: var(--success);
    border-radius: 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    font-weight: 600;
    margin-top: 4px;
  }

  /* Search result card */
  .search-card {
    background: rgba(232, 115, 58, 0.08);
    border: 1px solid rgba(232, 115, 58, 0.2);
    border-radius: 10px;
    padding: 12px 16px;
  }

  .search-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }

  .search-icon {
    font-size: 14px;
  }

  .search-query {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 600;
    color: var(--accent);
  }

  .search-summary {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    line-height: 1.5;
    color: var(--chrome-text-muted);
    margin: 0;
    max-height: 120px;
    overflow-y: auto;
    white-space: pre-wrap;
  }

  /* Status */
  .status-msg {
    text-align: center;
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    color: var(--chrome-text-muted);
    font-style: italic;
  }

  /* Input area */
  .input-area {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 16px 0 24px;
    flex-shrink: 0;
  }

  textarea {
    width: 100%;
    padding: 16px 20px;
    background: var(--paper);
    border: 1px solid var(--paper-border);
    border-radius: 12px;
    font-family: 'Newsreader', serif;
    font-size: 16px;
    line-height: 1.5;
    color: var(--ink);
    resize: vertical;
    min-height: 120px;
  }

  textarea::placeholder {
    color: var(--ink-muted);
  }

  textarea:focus {
    outline: none;
    border-color: var(--accent);
  }

  .input-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    align-self: flex-end;
  }

  .send-btn {
    padding: 8px 20px;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
  }

  .send-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  /* Ready bar */
  .ready-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    background: var(--accent);
    border-radius: 12px;
    margin: 16px 0 24px;
    flex-shrink: 0;
  }

  .ready-text {
    font-family: 'Outfit', sans-serif;
    font-size: 15px;
    color: white;
    font-weight: 500;
  }

  .draft-btn {
    padding: 10px 24px;
    background: white;
    color: var(--accent);
    border: none;
    border-radius: 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
    white-space: nowrap;
  }

  .draft-btn:hover {
    opacity: 0.9;
  }
</style>
