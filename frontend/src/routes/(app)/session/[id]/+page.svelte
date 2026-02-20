<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { ws } from '$lib/ws.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { drafts } from '$lib/stores/drafts.svelte';
	import { setupWsHandler, hydrateSessionFromApi } from '$lib/ws-handler';
	import Interview from '$lib/components/Interview.svelte';
	import DraftComparison from '$lib/components/DraftComparison.svelte';
	import FocusEditor from '$lib/components/FocusEditor.svelte';
	import OutlineScreen from '$lib/components/OutlineScreen.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	let cleanup: (() => void) | undefined;

	onMount(() => {
		cleanup = setupWsHandler();
		hydrateSessionFromApi(data.sessionData);
		ws.send({ type: 'session.resume', session_id: data.sessionData.session_id });
	});

	onDestroy(() => {
		cleanup?.();
	});
</script>

<svelte:head>
	<title>{data.sessionData.topic || 'Session'} — Inkwell</title>
</svelte:head>

{#key session.screen}
	<div class="screen">
		{#if session.screen === 'interview'}
			<Interview />
		{:else if session.screen === 'outline'}
			<OutlineScreen />
		{:else if session.screen === 'drafts'}
			<DraftComparison />
		{:else if session.screen === 'focus'}
			<FocusEditor />
		{:else}
			<div class="placeholder">
				<p>Loading session...</p>
			</div>
		{/if}
	</div>
{/key}

<style>
	.screen {
		flex: 1;
		display: flex;
		flex-direction: column;
		animation: fadeIn 0.2s ease-out;
	}

	@keyframes fadeIn {
		from { opacity: 0; transform: translateY(4px); }
		to { opacity: 1; transform: translateY(0); }
	}

	.placeholder {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 50vh;
		color: var(--chrome-text-muted);
	}
</style>
