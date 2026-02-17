<script lang="ts">
  import { ws } from '$lib/ws.svelte';
  import { session, type ChatMessage } from '$lib/stores/session.svelte';
  import { drafts } from '$lib/stores/drafts.svelte';
  import { tick } from 'svelte';

  let input = $state('');
  let messagesEnd: HTMLDivElement;

  $effect(() => {
    // Scroll to bottom when messages change
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

  function renderMessage(msg: ChatMessage): { class: string; label: string } {
    switch (msg.role) {
      case 'user':
        return { class: 'user', label: 'You' };
      case 'ai':
        return { class: 'ai', label: 'Writing Partner' };
      case 'thought':
        return { class: 'thought', label: 'Thinking...' };
      case 'status':
        return { class: 'status', label: '' };
      default:
        return { class: 'ai', label: 'Writing Partner' };
    }
  }
</script>

<div class="interview">
  <div class="header">
    <h2>Interview: {session.topic}</h2>
    <span class="badge">{session.taskType}</span>
  </div>

  <div class="messages">
    {#each session.messages as msg}
      {@const meta = renderMessage(msg)}
      <div class="message {meta.class}">
        {#if msg.role === 'thought' && msg.thought}
          <details class="thought-block" open>
            <summary>Thinking...</summary>
            <p class="assessment">{msg.thought.assessment}</p>
            {#if msg.thought.missing.length > 0}
              <div class="missing">
                <span class="missing-label">Still need:</span>
                <ul>
                  {#each msg.thought.missing as item}
                    <li>{item}</li>
                  {/each}
                </ul>
              </div>
            {/if}
            {#if msg.thought.sufficient}
              <span class="sufficient-badge">Ready to draft</span>
            {/if}
          </details>
        {:else if msg.role === 'status'}
          <div class="status-text">{msg.content}</div>
        {:else}
          {#if meta.label}
            <span class="msg-label">{meta.label}</span>
          {/if}
          <p class="msg-content">{msg.content}</p>
        {/if}
      </div>
    {/each}
    <div bind:this={messagesEnd}></div>
  </div>

  {#if session.readyToDraft}
    <div class="ready-bar">
      <p>I have enough material to write three drafts.</p>
      <button class="draft-btn" onclick={startDrafting}>Start Writing</button>
    </div>
  {:else}
    <div class="input-bar">
      <textarea
        bind:value={input}
        onkeydown={handleKeydown}
        placeholder="Type your answer..."
        rows="5"
      ></textarea>
      <button class="send-btn" onclick={sendAnswer} disabled={!input.trim()}>
        Send
      </button>
    </div>
  {/if}
</div>

<style>
  .interview {
    display: flex;
    flex-direction: column;
    height: 100%;
    max-width: 720px;
    margin: 0 auto;
    padding: 24px;
  }

  .header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border, #e0e0e0);
  }

  h2 {
    font-size: 20px;
    font-weight: 600;
    color: var(--text-primary, #1a1a1a);
    margin: 0;
  }

  .badge {
    padding: 4px 10px;
    background: var(--bg-muted, #f3f4f6);
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary, #666);
    text-transform: capitalize;
  }

  .messages {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding-bottom: 16px;
  }

  .message {
    max-width: 85%;
  }

  .message.user {
    align-self: flex-end;
    background: var(--accent, #f97316);
    color: white;
    padding: 12px 16px;
    border-radius: 16px 16px 4px 16px;
  }

  .message.ai {
    align-self: flex-start;
    background: var(--bg-surface, #f9fafb);
    border: 1px solid var(--border, #e0e0e0);
    padding: 12px 16px;
    border-radius: 16px 16px 16px 4px;
  }

  .message.status {
    align-self: center;
  }

  .status-text {
    font-size: 13px;
    color: var(--text-muted, #999);
    font-style: italic;
  }

  .msg-label {
    display: block;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-muted, #999);
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .message.user .msg-label {
    color: rgba(255, 255, 255, 0.7);
  }

  .msg-content {
    margin: 0;
    line-height: 1.5;
  }

  /* Thought block */
  .thought-block {
    align-self: flex-start;
    background: #fff8f0;
    border: 1px solid #fed7aa;
    border-radius: 12px;
    padding: 12px 16px;
    width: 100%;
    max-width: 85%;
  }

  .thought-block summary {
    font-size: 13px;
    font-weight: 600;
    color: #ea580c;
    cursor: pointer;
  }

  .assessment {
    font-size: 14px;
    color: var(--text-primary, #1a1a1a);
    line-height: 1.5;
    margin: 8px 0;
  }

  .missing {
    margin: 8px 0;
  }

  .missing-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary, #666);
  }

  .missing ul {
    margin: 4px 0 0;
    padding-left: 20px;
  }

  .missing li {
    font-size: 13px;
    color: var(--text-secondary, #666);
    margin: 2px 0;
  }

  .sufficient-badge {
    display: inline-block;
    padding: 2px 8px;
    background: #dcfce7;
    color: #16a34a;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    margin-top: 4px;
  }

  /* Input bar */
  .input-bar {
    display: flex;
    gap: 12px;
    padding-top: 16px;
    border-top: 1px solid var(--border, #e0e0e0);
  }

  textarea {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid var(--border, #e0e0e0);
    border-radius: 12px;
    font-size: 15px;
    font-family: inherit;
    resize: none;
    color: var(--text-primary, #1a1a1a);
  }

  textarea:focus {
    outline: none;
    border-color: var(--accent, #f97316);
  }

  .send-btn {
    padding: 12px 20px;
    background: var(--accent, #f97316);
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
    align-self: flex-end;
  }

  .send-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Ready bar */
  .ready-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 12px;
    margin-top: 16px;
  }

  .ready-bar p {
    margin: 0;
    font-size: 15px;
    color: #16a34a;
    font-weight: 500;
  }

  .draft-btn {
    padding: 10px 20px;
    background: #16a34a;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
  }

  .draft-btn:hover {
    opacity: 0.9;
  }
</style>
