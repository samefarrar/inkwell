<script lang="ts">
	import { focus } from '$lib/stores/focus.svelte';
	import { ws } from '$lib/ws.svelte';
	type Tab = 'suggestions' | 'comments' | 'chat';
	let activeTab = $state<Tab>('suggestions');
	let chatInput = $state('');

	function acceptSuggestion(id: string) {
		// TODO: apply replacement to TipTap document using start/end offsets
		focus.acceptSuggestion(id);
		ws.send({ type: 'focus.feedback', id, action: 'accept', feedback_type: 'suggestion' });
	}

	function rejectSuggestion(id: string) {
		focus.rejectSuggestion(id);
		ws.send({ type: 'focus.feedback', id, action: 'reject', feedback_type: 'suggestion' });
	}

	function dismissComment(id: string) {
		focus.dismissComment(id);
		ws.send({ type: 'focus.feedback', id, action: 'dismiss', feedback_type: 'comment' });
	}

	function sendChat() {
		const msg = chatInput.trim();
		if (!msg) return;
		focus.addChatMessage({ role: 'user', content: msg });
		ws.send({ type: 'focus.chat', message: msg });
		chatInput = '';
		focus.addChatMessage({ role: 'ai', content: '', done: false });
		focus.activeChatMessage = focus.chatMessages[focus.chatMessages.length - 1];
	}

	function handleChatKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendChat();
		}
	}

	function truncate(text: string, max: number): string {
		return text.length > max ? text.slice(0, max) + '...' : text;
	}
</script>

<div class="sidebar">
	<div class="tabs">
		<button
			class="tab"
			class:active={activeTab === 'suggestions'}
			onclick={() => (activeTab = 'suggestions')}
		>
			Suggestions
			{#if focus.suggestionCount > 0}
				<span class="badge">{focus.suggestionCount}</span>
			{/if}
		</button>
		<button
			class="tab"
			class:active={activeTab === 'comments'}
			onclick={() => (activeTab = 'comments')}
		>
			Comments
			{#if focus.commentCount > 0}
				<span class="badge">{focus.commentCount}</span>
			{/if}
		</button>
		<button
			class="tab"
			class:active={activeTab === 'chat'}
			onclick={() => (activeTab = 'chat')}
		>
			Chat
		</button>
	</div>

	<div class="tab-content">
		{#if activeTab === 'suggestions'}
			<div class="suggestion-list">
				{#if focus.suggestions.length === 0}
					{#if focus.analyzing}
						<div class="empty-state">
							<span class="loading-dot"></span>
							Analyzing your draft...
						</div>
					{:else}
						<div class="empty-state">No suggestions yet.</div>
					{/if}
				{:else}
					{#each focus.suggestions as s (s.id)}
						<div class="suggestion-card">
							<div class="suggestion-quote">"{truncate(s.quote, 60)}"</div>
							{#if s.replacement}
								<div class="suggestion-change">
									<span class="change-from">{s.quote}</span>
									<span class="change-arrow">&rarr;</span>
									<span class="change-to">{s.replacement}</span>
								</div>
							{:else}
								<div class="suggestion-change">
									<span class="change-from">{s.quote}</span>
									<span class="change-arrow">&rarr;</span>
									<span class="change-remove">(remove)</span>
								</div>
							{/if}
							<div class="suggestion-explanation">{s.explanation}</div>
							<div class="suggestion-actions">
								<button class="action-btn accept" onclick={() => acceptSuggestion(s.id)}>
									Accept
								</button>
								<button class="action-btn reject" onclick={() => rejectSuggestion(s.id)}>
									Reject
								</button>
								<span class="rule-tag">{s.ruleId}</span>
							</div>
						</div>
					{/each}
				{/if}
			</div>

		{:else if activeTab === 'comments'}
			<div class="comment-list">
				{#if focus.comments.length === 0}
					{#if focus.analyzing}
						<div class="empty-state">
							<span class="loading-dot"></span>
							Generating editorial feedback...
						</div>
					{:else}
						<div class="empty-state">No comments yet.</div>
					{/if}
				{:else}
					{#each focus.comments as c (c.id)}
						<div class="comment-card">
							<div class="comment-quote">"{truncate(c.quote, 60)}"</div>
							<div class="comment-text">{c.comment}</div>
							<div class="comment-actions">
								<button class="action-btn dismiss" onclick={() => dismissComment(c.id)}>
									Dismiss
								</button>
							</div>
						</div>
					{/each}
				{/if}
			</div>

		{:else if activeTab === 'chat'}
			<div class="chat-panel">
				<div class="chat-messages">
					{#if focus.chatMessages.length === 0}
						<div class="empty-state">
							Ask the AI about your draft. It can suggest edits, answer questions, and search the web.
						</div>
					{:else}
						{#each focus.chatMessages as msg, i}
							{#if msg.role === 'user'}
								<div class="chat-msg chat-user">{msg.content}</div>
							{:else if msg.role === 'ai'}
								<div class="chat-msg chat-ai">
									{msg.content}
									{#if !msg.done}
										<span class="typing-indicator"></span>
									{/if}
								</div>
							{:else if msg.role === 'search'}
								<div class="chat-msg chat-search">
									<div class="search-label">Search: {msg.searchQuery}</div>
									<div class="search-summary">{msg.content}</div>
								</div>
							{/if}
						{/each}
					{/if}
				</div>
				<div class="chat-input-area">
					<textarea
						class="chat-input"
						placeholder="Ask about your draft..."
						bind:value={chatInput}
						onkeydown={handleChatKeydown}
						rows="2"
					></textarea>
					<button class="send-btn" onclick={sendChat} disabled={!chatInput.trim() || !!focus.activeChatMessage}>
						Send
					</button>
				</div>
			</div>
		{/if}
	</div>

	{#if focus.analyzing}
		<div class="analysis-bar">
			<span class="loading-dot"></span>
			Analyzing draft...
		</div>
	{/if}
</div>

<style>
	.sidebar {
		display: flex;
		flex-direction: column;
		height: 100%;
		background: var(--chrome);
		border-left: 1px solid var(--chrome-border);
	}

	.tabs {
		display: flex;
		border-bottom: 1px solid var(--chrome-border);
		flex-shrink: 0;
	}

	.tab {
		flex: 1;
		padding: 10px 8px;
		border: none;
		background: transparent;
		color: var(--chrome-text-muted);
		font-family: 'Outfit', sans-serif;
		font-size: 12px;
		font-weight: 500;
		cursor: pointer;
		transition: color 0.2s, border-color 0.2s;
		border-bottom: 2px solid transparent;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
	}

	.tab:hover {
		color: var(--chrome-text);
	}

	.tab.active {
		color: var(--chrome-text);
		border-bottom-color: var(--accent);
	}

	.badge {
		background: var(--accent);
		color: white;
		font-size: 10px;
		font-weight: 600;
		padding: 1px 6px;
		border-radius: 10px;
		min-width: 18px;
		text-align: center;
	}

	.tab-content {
		flex: 1;
		overflow-y: auto;
		min-height: 0;
	}

	.empty-state {
		padding: 24px 16px;
		text-align: center;
		color: var(--chrome-text-muted);
		font-family: 'Outfit', sans-serif;
		font-size: 13px;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
	}

	/* Suggestions */
	.suggestion-list {
		padding: 8px;
	}

	.suggestion-card {
		padding: 12px;
		border: 1px solid var(--chrome-border);
		border-radius: 8px;
		margin-bottom: 8px;
		transition: border-color 0.2s;
	}

	.suggestion-card:hover {
		border-color: var(--chrome-text-muted);
	}

	.suggestion-quote {
		font-family: 'Newsreader', serif;
		font-size: 13px;
		color: var(--chrome-text-muted);
		font-style: italic;
		margin-bottom: 6px;
	}

	.suggestion-change {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 6px;
		font-family: 'Outfit', sans-serif;
		font-size: 13px;
	}

	.change-from {
		color: var(--error, #ef4444);
		text-decoration: line-through;
	}

	.change-arrow {
		color: var(--chrome-text-muted);
	}

	.change-to {
		color: var(--success);
	}

	.change-remove {
		color: var(--chrome-text-muted);
		font-style: italic;
	}

	.suggestion-explanation {
		font-family: 'Outfit', sans-serif;
		font-size: 12px;
		color: var(--chrome-text-muted);
		margin-bottom: 8px;
		line-height: 1.4;
	}

	.suggestion-actions {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.action-btn {
		padding: 4px 12px;
		border-radius: 4px;
		border: 1px solid var(--chrome-border);
		background: transparent;
		font-family: 'Outfit', sans-serif;
		font-size: 12px;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.15s, color 0.15s, border-color 0.15s;
	}

	.action-btn.accept {
		color: var(--success);
		border-color: var(--success);
	}

	.action-btn.accept:hover {
		background: rgba(74, 222, 128, 0.1);
	}

	.action-btn.reject {
		color: var(--error, #ef4444);
		border-color: var(--error, #ef4444);
	}

	.action-btn.reject:hover {
		background: rgba(239, 68, 68, 0.08);
	}

	.action-btn.dismiss {
		color: var(--chrome-text-muted);
	}

	.action-btn.dismiss:hover {
		color: var(--chrome-text);
		border-color: var(--chrome-text-muted);
	}

	.rule-tag {
		margin-left: auto;
		font-family: 'Outfit', sans-serif;
		font-size: 10px;
		color: var(--chrome-text-muted);
		padding: 2px 6px;
		background: var(--chrome-surface);
		border-radius: 4px;
	}

	/* Comments */
	.comment-list {
		padding: 8px;
	}

	.comment-card {
		padding: 12px;
		border: 1px solid var(--chrome-border);
		border-radius: 8px;
		margin-bottom: 8px;
	}

	.comment-quote {
		font-family: 'Newsreader', serif;
		font-size: 13px;
		color: var(--chrome-text-muted);
		font-style: italic;
		margin-bottom: 6px;
		padding-left: 10px;
		border-left: 2px solid var(--accent);
	}

	.comment-text {
		font-family: 'Outfit', sans-serif;
		font-size: 13px;
		color: var(--chrome-text);
		line-height: 1.5;
		margin-bottom: 8px;
	}

	.comment-actions {
		display: flex;
		align-items: center;
	}

	/* Chat */
	.chat-panel {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.chat-messages {
		flex: 1;
		overflow-y: auto;
		padding: 12px;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.chat-msg {
		font-family: 'Outfit', sans-serif;
		font-size: 13px;
		line-height: 1.5;
		padding: 8px 12px;
		border-radius: 8px;
		max-width: 90%;
	}

	.chat-user {
		background: var(--accent);
		color: white;
		align-self: flex-end;
		border-bottom-right-radius: 2px;
	}

	.chat-ai {
		background: var(--chrome-surface);
		color: var(--chrome-text);
		align-self: flex-start;
		border-bottom-left-radius: 2px;
	}

	.chat-search {
		background: var(--thought-bg);
		border: 1px solid var(--thought-border);
		color: var(--chrome-text);
		align-self: flex-start;
		width: 100%;
		max-width: 100%;
	}

	.search-label {
		font-size: 11px;
		font-weight: 600;
		color: var(--chrome-text-muted);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		margin-bottom: 4px;
	}

	.search-summary {
		font-size: 12px;
		color: var(--chrome-text-muted);
		line-height: 1.4;
	}

	.typing-indicator {
		display: inline-block;
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--accent);
		animation: pulse 1s ease-in-out infinite;
		margin-left: 4px;
		vertical-align: middle;
	}

	.chat-input-area {
		display: flex;
		gap: 8px;
		padding: 8px 12px;
		border-top: 1px solid var(--chrome-border);
		flex-shrink: 0;
	}

	.chat-input {
		flex: 1;
		padding: 8px 10px;
		border: 1px solid var(--chrome-border);
		border-radius: 6px;
		background: var(--chrome-surface);
		color: var(--chrome-text);
		font-family: 'Outfit', sans-serif;
		font-size: 13px;
		resize: none;
		outline: none;
		transition: border-color 0.2s;
	}

	.chat-input:focus {
		border-color: var(--accent);
	}

	.chat-input::placeholder {
		color: var(--chrome-text-muted);
	}

	.send-btn {
		padding: 8px 16px;
		background: var(--accent);
		color: white;
		border: none;
		border-radius: 6px;
		font-family: 'Outfit', sans-serif;
		font-size: 13px;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.2s;
		align-self: flex-end;
	}

	.send-btn:hover:not(:disabled) {
		background: var(--accent-hover, #d4622e);
	}

	.send-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Analysis bar */
	.analysis-bar {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 8px 16px;
		border-top: 1px solid var(--chrome-border);
		font-family: 'Outfit', sans-serif;
		font-size: 12px;
		color: var(--accent);
		flex-shrink: 0;
	}

	.loading-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--accent);
		animation: pulse 1.2s ease-in-out infinite;
		flex-shrink: 0;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.5; transform: scale(0.8); }
	}
</style>
