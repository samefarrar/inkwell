<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { session } from '$lib/stores/session.svelte';
	import { drafts } from '$lib/stores/drafts.svelte';
	import { setupWsHandler } from '$lib/ws-handler';
	import TaskSelector from '$lib/components/TaskSelector.svelte';
	import Interview from '$lib/components/Interview.svelte';
	import DraftComparison from '$lib/components/DraftComparison.svelte';
	import FocusEditor from '$lib/components/FocusEditor.svelte';
	import OutlineScreen from '$lib/components/OutlineScreen.svelte';

	let cleanup: (() => void) | undefined;

	onMount(() => {
		session.reset();
		drafts.reset();
		cleanup = setupWsHandler();
	});

	onDestroy(() => {
		cleanup?.();
	});
</script>

<svelte:head>
	<title>New Session — Inkwell</title>
</svelte:head>

{#key session.screen}
	<div class="screen">
		{#if session.screen === 'task'}
			<TaskSelector onResume={() => {}} />
		{:else if session.screen === 'interview'}
			<Interview />
		{:else if session.screen === 'outline'}
			<OutlineScreen />
		{:else if session.screen === 'drafts'}
			<DraftComparison />
		{:else if session.screen === 'focus'}
			<FocusEditor />
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
</style>
