<script lang="ts">
  import { onMount, onDestroy, tick } from 'svelte';
  import { WebSocketClient, type ServerMessage } from '$lib/ws.svelte';
  import type { ChatMessage, ThoughtBlock, SearchInfo } from '$lib/stores/session.svelte';
  import { StreamBuffer } from '$lib/stream-buffer.svelte';

  interface PanelState {
    provider: string;
    label: string;
    ws: WebSocketClient;
    messages: ChatMessage[];
    connected: boolean;
    readyToDraft: boolean;
  }

  const providers = ['anthropic', 'ddg', 'exa'] as const;
  const labels: Record<string, string> = {
    anthropic: 'Anthropic (built-in)',
    ddg: 'DuckDuckGo',
    exa: 'Exa.ai'
  };

  let panels = $state<PanelState[]>([]);
  let input = $state('');
  let taskType = $state('');
  let topic = $state('');
  let started = $state(false);
  let unsubscribers: (() => void)[] = [];
  let activeBuffers: StreamBuffer[] = [];
  let messageEnds: (HTMLDivElement | undefined)[] = $state([undefined, undefined, undefined]);

  onMount(() => {
    panels = providers.map((p) => ({
      provider: p,
      label: labels[p],
      ws: new WebSocketClient(p),
      messages: [],
      connected: false,
      readyToDraft: false
    }));

    panels.forEach((panel, idx) => {
      panel.ws.connect();

      const unsub = panel.ws.onMessage((msg: ServerMessage) => {
        handleMessage(idx, msg);
      });
      unsubscribers.push(unsub);
    });
  });

  onDestroy(() => {
    unsubscribers.forEach((u) => u());
    panels.forEach((p) => p.ws.disconnect());
  });

  function handleMessage(idx: number, msg: ServerMessage): void {
    const panel = panels[idx];

    switch (msg.type) {
      case 'thought': {
        const thought: ThoughtBlock = {
          assessment: '',
          missing: msg.missing,
          sufficient: msg.sufficient
        };
        const chatMsg: ChatMessage = { role: 'thought', content: '', thought };
        panel.messages = [...panel.messages, chatMsg];
        const reactiveMsg = panel.messages[panel.messages.length - 1];
        const tBuf = new StreamBuffer(reactiveMsg.thought!, 'assessment', () => {
          reactiveMsg.content = reactiveMsg.thought!.assessment;
        });
        tBuf.push(msg.assessment);
        activeBuffers.push(tBuf);
        break;
      }

      case 'interview.question': {
        const chatMsg: ChatMessage = { role: 'ai', content: '' };
        panel.messages = [...panel.messages, chatMsg];
        const reactiveMsg = panel.messages[panel.messages.length - 1];
        const qBuf = new StreamBuffer(reactiveMsg, 'content');
        qBuf.push(msg.question);
        activeBuffers.push(qBuf);
        break;
      }

      case 'search.result': {
        const searchInfo: SearchInfo = { query: msg.query, summary: msg.summary };
        panel.messages = [...panel.messages, { role: 'search', content: msg.summary, search: searchInfo }];
        break;
      }

      case 'ready_to_draft':
        panel.readyToDraft = true;
        panel.messages = [
          ...panel.messages,
          { role: 'status', content: 'Ready to draft! Material gathered.' }
        ];
        break;

      case 'status':
        panel.messages = [...panel.messages, { role: 'status', content: msg.message }];
        break;

      case 'error':
        panel.messages = [
          ...panel.messages,
          { role: 'status', content: `Error: ${msg.message}` }
        ];
        break;
    }

    scrollPanel(idx);
  }

  async function scrollPanel(idx: number): Promise<void> {
    await tick();
    messageEnds[idx]?.scrollIntoView({ behavior: 'smooth' });
  }

  function startExperiment(): void {
    if (!taskType.trim() || !topic.trim()) return;
    started = true;

    panels.forEach((panel) => {
      panel.ws.send({
        type: 'task.select',
        task_type: taskType,
        topic: topic
      });
    });
  }

  function sendAnswer(): void {
    const answer = input.trim();
    if (!answer) return;

    panels.forEach((panel) => {
      panel.messages = [...panel.messages, { role: 'user', content: answer }];
      panel.ws.send({ type: 'interview.answer', answer });
    });

    input = '';
  }

  function handleKeydown(e: KeyboardEvent): void {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!started) {
        startExperiment();
      } else {
        sendAnswer();
      }
    }
  }
</script>

<div class="experiment">
  <h2 class="title">Search Provider Experiment</h2>
  <p class="subtitle">Compare Anthropic, DuckDuckGo, and Exa search side-by-side</p>

  {#if !started}
    <div class="setup">
      <div class="field">
        <label for="task-type">Task Type</label>
        <select id="task-type" bind:value={taskType}>
          <option value="">Select...</option>
          <option value="essay">Essay</option>
          <option value="newsletter">Newsletter</option>
          <option value="review">Review</option>
          <option value="landing_page">Landing Page</option>
        </select>
      </div>
      <div class="field">
        <label for="topic">Topic</label>
        <input
          id="topic"
          type="text"
          bind:value={topic}
          onkeydown={handleKeydown}
          placeholder="e.g., restaurant review of Osteria Francescana"
        />
      </div>
      <button class="start-btn" onclick={startExperiment} disabled={!taskType || !topic.trim()}>
        Start Experiment
      </button>
    </div>
  {:else}
    <div class="panels">
      {#each panels as panel, idx}
        <div class="panel">
          <div class="panel-header">
            <span class="provider-label">{panel.label}</span>
            <span class="conn-dot" class:connected={panel.ws.connected}></span>
          </div>
          <div class="panel-messages">
            {#each panel.messages as msg, msgIdx}
              {#if msg.role === 'thought' && msg.thought}
                {@const isFirst = !panel.messages.slice(0, msgIdx).some((m) => m.role === 'thought')}
                <div class="thought-block">
                  <details open={isFirst}>
                    <summary>Thinking</summary>
                    <p class="assessment">{msg.thought.assessment}</p>
                    {#if msg.thought.missing.length > 0}
                      <div class="missing">
                        <span class="missing-label">Still exploring: </span>
                        <span>{msg.thought.missing.join(', ')}</span>
                      </div>
                    {/if}
                    {#if msg.thought.sufficient}
                      <span class="sufficient-badge">Ready</span>
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
                  <p>{msg.content}</p>
                </div>
              {:else if msg.role === 'user'}
                <div class="user-msg">
                  <p>{msg.content}</p>
                </div>
              {/if}
            {/each}
            <div bind:this={messageEnds[idx]}></div>
          </div>
        </div>
      {/each}
    </div>

    <div class="input-area">
      <textarea
        bind:value={input}
        onkeydown={handleKeydown}
        placeholder="Your answer goes to all three panels..."
        rows="3"
      ></textarea>
      <button class="send-btn" onclick={sendAnswer} disabled={!input.trim()}>
        Send to All
      </button>
    </div>
  {/if}
</div>

<style>
  .experiment {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 48px);
    padding: 16px 24px 0;
  }

  .title {
    font-family: 'Outfit', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: var(--chrome-text);
    margin: 0;
  }

  .subtitle {
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    color: var(--chrome-text-muted);
    margin: 4px 0 16px;
  }

  /* Setup form */
  .setup {
    max-width: 500px;
    margin: 24px auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .field label {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--chrome-text-muted);
  }

  .field select,
  .field input {
    padding: 10px 14px;
    background: var(--chrome-surface);
    border: 1px solid var(--chrome-border);
    border-radius: 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 15px;
    color: var(--chrome-text);
  }

  .field select:focus,
  .field input:focus {
    outline: none;
    border-color: var(--accent);
  }

  .start-btn {
    padding: 12px 24px;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 8px;
  }

  .start-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  /* Three-panel layout */
  .panels {
    flex: 1;
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 12px;
    min-height: 0;
    overflow: hidden;
  }

  .panel {
    display: flex;
    flex-direction: column;
    background: var(--chrome-surface);
    border: 1px solid var(--chrome-border);
    border-radius: 12px;
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-bottom: 1px solid var(--chrome-border);
    flex-shrink: 0;
  }

  .provider-label {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--accent);
  }

  .conn-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #dc2626;
  }

  .conn-dot.connected {
    background: var(--success);
  }

  .panel-messages {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  /* Message styles (compact for panels) */
  .thought-block {
    background: var(--thought-bg);
    border-left: 2px solid var(--thought-border);
    padding: 8px 10px;
    border-radius: 0 6px 6px 0;
    font-size: 12px;
  }

  .thought-block summary {
    font-family: 'Outfit', sans-serif;
    font-size: 11px;
    font-weight: 600;
    color: #d4a574;
    cursor: pointer;
    list-style: none;
  }

  .thought-block summary::-webkit-details-marker {
    display: none;
  }

  .assessment {
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    color: var(--chrome-text);
    line-height: 1.4;
    margin: 6px 0;
  }

  .missing {
    font-family: 'Outfit', sans-serif;
    font-size: 11px;
    color: var(--chrome-text-muted);
    margin: 4px 0;
  }

  .missing-label {
    font-weight: 600;
  }

  .sufficient-badge {
    display: inline-block;
    padding: 2px 8px;
    background: rgba(74, 222, 128, 0.15);
    color: var(--success);
    border-radius: 6px;
    font-family: 'Outfit', sans-serif;
    font-size: 10px;
    font-weight: 600;
    margin-top: 4px;
  }

  /* Search result card */
  .search-card {
    background: rgba(232, 115, 58, 0.08);
    border: 1px solid rgba(232, 115, 58, 0.2);
    border-radius: 8px;
    padding: 8px 10px;
  }

  .search-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
  }

  .search-icon {
    font-size: 12px;
  }

  .search-query {
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    font-weight: 600;
    color: var(--accent);
  }

  .search-summary {
    font-family: 'Outfit', sans-serif;
    font-size: 11px;
    line-height: 1.4;
    color: var(--chrome-text-muted);
    margin: 0;
    max-height: 80px;
    overflow-y: auto;
    white-space: pre-wrap;
  }

  .status-msg {
    text-align: center;
    font-family: 'Outfit', sans-serif;
    font-size: 11px;
    color: var(--chrome-text-muted);
    font-style: italic;
  }

  .ai-msg {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 500;
    line-height: 1.4;
    color: var(--chrome-text);
  }

  .ai-msg p {
    margin: 0;
  }

  .user-msg {
    background: var(--paper);
    border-radius: 8px;
    padding: 8px 10px;
  }

  .user-msg p {
    font-family: 'Newsreader', serif;
    font-size: 13px;
    line-height: 1.4;
    color: var(--ink);
    margin: 0;
  }

  /* Shared input at bottom */
  .input-area {
    display: flex;
    gap: 8px;
    padding: 12px 0 16px;
    flex-shrink: 0;
    align-items: flex-end;
  }

  textarea {
    flex: 1;
    padding: 10px 14px;
    background: var(--paper);
    border: 1px solid var(--paper-border);
    border-radius: 8px;
    font-family: 'Newsreader', serif;
    font-size: 15px;
    line-height: 1.4;
    color: var(--ink);
    resize: none;
  }

  textarea::placeholder {
    color: var(--ink-muted);
  }

  textarea:focus {
    outline: none;
    border-color: var(--accent);
  }

  .send-btn {
    padding: 10px 20px;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }

  .send-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
</style>
