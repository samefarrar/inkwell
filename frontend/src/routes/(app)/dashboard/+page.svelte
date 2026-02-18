<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}

	function statusLabel(status: string): string {
		const labels: Record<string, string> = {
			interview: 'Interview',
			drafting: 'Drafting',
			highlighting: 'Highlighting',
			synthesizing: 'Synthesizing',
			complete: 'Complete'
		};
		return labels[status] ?? status;
	}
</script>

<svelte:head>
	<title>Dashboard — Inkwell</title>
</svelte:head>

<div class="dashboard">
	<div class="header">
		<h1>Your Sessions</h1>
	</div>

	<div class="grid">
		<a href="/session/new" class="card new-card">
			<span class="plus">+</span>
			<span class="new-label">New Session</span>
		</a>

		{#each data.sessions as session}
			<a href="/session/{session.id}" class="card session-card">
				<div class="card-top">
					<span class="badge">{session.task_type}</span>
					<span class="status">{statusLabel(session.status)}</span>
				</div>
				<p class="topic">{session.topic || 'Untitled session'}</p>
				<div class="card-meta">
					<span>{session.draft_count} draft{session.draft_count !== 1 ? 's' : ''}</span>
					<span>{formatDate(session.created_at)}</span>
				</div>
			</a>
		{/each}
	</div>

	{#if data.sessions.length === 0}
		<div class="empty">
			<p class="empty-title">Start your first writing session</p>
			<p class="empty-sub">Describe what you want to write — Inkwell will interview you and generate draft angles.</p>
			<a href="/session/new" class="btn-primary">New Session</a>
		</div>
	{/if}
</div>

<style>
	.dashboard {
		padding: 32px;
		max-width: 960px;
		margin: 0 auto;
	}

	.header {
		margin-bottom: 24px;
	}

	h1 {
		font-family: 'Newsreader', serif;
		font-weight: 600;
		font-size: 24px;
		margin: 0;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
		gap: 16px;
	}

	.card {
		display: flex;
		flex-direction: column;
		padding: 20px;
		border-radius: 10px;
		border: 1px solid var(--chrome-border);
		background: var(--chrome-surface);
		text-decoration: none;
		color: inherit;
		transition: border-color 0.2s;
	}

	.card:hover {
		border-color: var(--chrome-text-muted);
	}

	.new-card {
		align-items: center;
		justify-content: center;
		gap: 8px;
		min-height: 140px;
		border-style: dashed;
	}

	.plus {
		font-size: 28px;
		color: var(--accent);
		font-weight: 300;
	}

	.new-label {
		font-size: 14px;
		font-weight: 500;
		color: var(--chrome-text-muted);
	}

	.card-top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 10px;
	}

	.badge {
		font-size: 11px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--accent);
		background: var(--accent-glow);
		padding: 3px 8px;
		border-radius: 4px;
	}

	.status {
		font-size: 11px;
		color: var(--chrome-text-muted);
	}

	.topic {
		font-size: 15px;
		font-weight: 500;
		color: var(--chrome-text);
		margin: 0 0 auto;
		line-height: 1.4;
		flex: 1;
	}

	.card-meta {
		display: flex;
		justify-content: space-between;
		font-size: 12px;
		color: var(--chrome-text-muted);
		margin-top: 14px;
		padding-top: 10px;
		border-top: 1px solid var(--chrome-border);
	}

	.empty {
		text-align: center;
		padding: 60px 20px;
	}

	.empty-title {
		font-family: 'Newsreader', serif;
		font-size: 20px;
		font-weight: 600;
		color: var(--chrome-text);
		margin: 0 0 8px;
	}

	.empty-sub {
		font-size: 14px;
		color: var(--chrome-text-muted);
		margin: 0 0 24px;
		max-width: 400px;
		margin-left: auto;
		margin-right: auto;
	}

	.btn-primary {
		display: inline-block;
		background: var(--accent);
		color: white;
		padding: 12px 28px;
		border-radius: 24px;
		font-size: 14px;
		font-weight: 600;
		text-decoration: none;
		transition: opacity 0.2s;
	}

	.btn-primary:hover {
		opacity: 0.9;
	}
</style>
