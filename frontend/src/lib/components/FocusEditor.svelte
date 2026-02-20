<script lang="ts">
	import { onMount } from 'svelte';
	import { session } from '$lib/stores/session.svelte';
	import { focus } from '$lib/stores/focus.svelte';
	import { ws } from '$lib/ws.svelte';
	import FocusTipTap from './FocusTipTap.svelte';
	import FocusSidebar from './FocusSidebar.svelte';

	let tiptap: FocusTipTap;

	function handleBack() {
		ws.send({ type: 'focus.exit' });
		focus.leaveFocus();
		session.goToDrafts();
	}

	// Send focus.enter to backend exactly once on mount
	onMount(() => {
		if (focus.selectedDraftIndex >= 0) {
			ws.send({ type: 'focus.enter', draft_index: focus.selectedDraftIndex });
		}
	});
</script>

<div class="focus-layout">
	<div class="top-bar">
		<button class="back-btn" onclick={handleBack}>
			&larr; Back to drafts
		</button>
		<span class="session-title">{session.topic || 'Untitled'}</span>
		<span class="word-count">{focus.wordCount} words</span>
	</div>

	<div class="panels">
		<div class="editor-panel">
			<FocusTipTap bind:this={tiptap} />
		</div>
		<div class="sidebar-panel">
			<FocusSidebar />
		</div>
	</div>
</div>

<style>
	.focus-layout {
		display: flex;
		flex-direction: column;
		height: calc(100vh - 48px);
	}

	.top-bar {
		display: flex;
		align-items: center;
		padding: 10px 20px;
		border-bottom: 1px solid var(--chrome-border);
		background: var(--chrome);
		flex-shrink: 0;
		gap: 16px;
	}

	.back-btn {
		padding: 6px 12px;
		border: 1px solid var(--chrome-border);
		border-radius: 6px;
		background: transparent;
		color: var(--chrome-text-muted);
		font-family: 'Outfit', sans-serif;
		font-size: 13px;
		cursor: pointer;
		transition: color 0.2s, border-color 0.2s;
		white-space: nowrap;
	}

	.back-btn:hover {
		color: var(--chrome-text);
		border-color: var(--chrome-text-muted);
	}

	.session-title {
		flex: 1;
		font-family: 'Outfit', sans-serif;
		font-size: 14px;
		font-weight: 500;
		color: var(--chrome-text);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		text-align: center;
	}

	.word-count {
		font-family: 'Outfit', sans-serif;
		font-size: 13px;
		color: var(--chrome-text-muted);
		white-space: nowrap;
	}

	.panels {
		display: flex;
		flex: 1;
		min-height: 0;
	}

	.editor-panel {
		flex: 7;
		background: var(--paper);
		overflow: hidden;
	}

	.sidebar-panel {
		flex: 3;
		min-width: 280px;
		max-width: 400px;
	}
</style>
