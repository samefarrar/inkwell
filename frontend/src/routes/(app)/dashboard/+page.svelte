<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { session } from '$lib/stores/session.svelte';
	import { drafts } from '$lib/stores/drafts.svelte';
	import { setupWsHandler } from '$lib/ws-handler';
	import TaskSelector from '$lib/components/TaskSelector.svelte';
	import Interview from '$lib/components/Interview.svelte';
	import DraftComparison from '$lib/components/DraftComparison.svelte';
	import FocusEditor from '$lib/components/FocusEditor.svelte';
	import OutlineScreen from '$lib/components/OutlineScreen.svelte';
	import OnboardingPrompt from '$lib/components/OnboardingPrompt.svelte';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	let onboardingDismissed = $state(false);
	const showOnboarding = $derived(
		!data.onboarding_completed && !onboardingDismissed && data.sessions.length === 0
	);

	let cleanup: (() => void) | undefined;

	onMount(() => {
		session.reset();
		drafts.reset();
		cleanup = setupWsHandler();
	});

	onDestroy(() => {
		cleanup?.();
	});

	function relativeDate(iso: string): string {
		const d = new Date(iso);
		const now = new Date();
		const diff = now.getTime() - d.getTime();
		const mins = Math.floor(diff / 60000);
		if (mins < 1) return 'just now';
		if (mins < 60) return `${mins}m ago`;
		const hours = Math.floor(mins / 60);
		if (hours < 24) return `${hours}h ago`;
		const days = Math.floor(hours / 24);
		if (days < 7) return `${days}d ago`;
		return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
	}

	const taskTypeLabels: Record<string, string> = {
		essay: 'Essay',
		review: 'Review',
		newsletter: 'Newsletter',
		landing_page: 'Landing Page',
		blog_post: 'Blog Post'
	};
</script>

<svelte:head>
	<title>Inkwell</title>
</svelte:head>

{#key session.screen}
	<div class="screen">
		{#if session.screen === 'task'}
			{#if showOnboarding}
				<OnboardingPrompt onDismiss={() => (onboardingDismissed = true)} />
			{/if}

			<TaskSelector onResume={(id) => goto('/session/' + id)} lastStyleId={data.last_style_id} />

			{#if data.sessions.length > 0}
				<div class="recent-sessions">
					<div class="recent-label">Recent sessions</div>
					<div class="session-list">
						{#each data.sessions as s (s.id)}
							<button class="session-row" onclick={() => goto('/session/' + s.id)}>
								<span class="session-type">{taskTypeLabels[s.task_type] ?? s.task_type}</span>
								<span class="session-topic">{s.topic || 'Untitled'}</span>
								<span class="session-meta">
									{#if s.draft_count > 0}{s.draft_count} draft{s.draft_count === 1 ? '' : 's'} ·{/if}
									{relativeDate(s.created_at)}
								</span>
							</button>
						{/each}
					</div>
				</div>
			{/if}
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
		from {
			opacity: 0;
			transform: translateY(4px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.recent-sessions {
		width: 100%;
		max-width: 560px;
		margin: 0 auto;
		padding: 0 24px 40px;
	}

	.recent-label {
		font-family: 'Outfit', sans-serif;
		font-size: 11px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--chrome-text-muted);
		margin-bottom: 8px;
		padding: 0 4px;
	}

	.session-list {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.session-row {
		display: grid;
		grid-template-columns: 80px 1fr auto;
		align-items: center;
		gap: 12px;
		padding: 10px 12px;
		background: transparent;
		border: none;
		border-radius: 8px;
		cursor: pointer;
		text-align: left;
		font-family: 'Outfit', sans-serif;
		transition: background 0.15s;
		width: 100%;
	}

	.session-row:hover {
		background: rgba(255, 255, 255, 0.04);
	}

	.session-type {
		font-size: 10px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--accent);
		flex-shrink: 0;
	}

	.session-topic {
		font-size: 13px;
		color: var(--chrome-text);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.session-meta {
		font-size: 11px;
		color: var(--chrome-text-muted);
		white-space: nowrap;
		flex-shrink: 0;
	}
</style>
