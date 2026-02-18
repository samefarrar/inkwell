<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			month: 'long',
			year: 'numeric'
		});
	}
</script>

<svelte:head>
	<title>Settings — Inkwell</title>
</svelte:head>

<div class="settings">
	<h1>Settings</h1>

	<!-- Profile -->
	<section class="card">
		<h2>Profile</h2>
		<div class="field">
			<label>Name</label>
			<input type="text" value={data.user.name} disabled />
		</div>
		<div class="field">
			<label>Email</label>
			<input type="email" value={data.user.email} disabled />
		</div>
	</section>

	<!-- Plan -->
	<section class="card">
		<h2>Plan</h2>
		<div class="plan-row">
			<div class="plan-info">
				<span class="plan-badge">{data.user.plan}</span>
				<span class="plan-desc">
					{#if data.user.plan === 'free'}
						5 sessions per month, 3 draft angles
					{:else if data.user.plan === 'pro'}
						Unlimited sessions, voice input, advanced style learning
					{:else}
						Everything in Pro + team features
					{/if}
				</span>
			</div>
			{#if data.user.plan === 'free'}
				<a href="/#pricing" class="upgrade-link">Upgrade</a>
			{/if}
		</div>
	</section>

	<!-- Password -->
	<section class="card">
		<h2>Change Password</h2>
		<p class="card-hint">Password change is coming soon.</p>
	</section>
</div>

<style>
	.settings {
		padding: 32px;
		max-width: 600px;
		margin: 0 auto;
	}

	h1 {
		font-family: 'Newsreader', serif;
		font-weight: 600;
		font-size: 24px;
		margin: 0 0 24px;
	}

	.card {
		background: var(--chrome-surface);
		border: 1px solid var(--chrome-border);
		border-radius: 10px;
		padding: 24px;
		margin-bottom: 16px;
	}

	.card h2 {
		font-size: 16px;
		font-weight: 600;
		margin: 0 0 16px;
		color: var(--chrome-text);
	}

	.field {
		margin-bottom: 12px;
	}

	.field:last-child {
		margin-bottom: 0;
	}

	.field label {
		display: block;
		font-size: 12px;
		font-weight: 500;
		color: var(--chrome-text-muted);
		margin-bottom: 4px;
	}

	.field input {
		width: 100%;
		padding: 8px 12px;
		border-radius: 6px;
		border: 1px solid var(--chrome-border);
		background: var(--chrome);
		color: var(--chrome-text);
		font-size: 14px;
		font-family: inherit;
	}

	.field input:disabled {
		opacity: 0.7;
	}

	.plan-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
	}

	.plan-info {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.plan-badge {
		font-size: 11px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--accent);
		background: var(--accent-glow);
		padding: 4px 10px;
		border-radius: 4px;
	}

	.plan-desc {
		font-size: 13px;
		color: var(--chrome-text-muted);
	}

	.upgrade-link {
		font-size: 13px;
		font-weight: 600;
		color: var(--accent);
		text-decoration: none;
	}

	.upgrade-link:hover {
		text-decoration: underline;
	}

	.card-hint {
		font-size: 13px;
		color: var(--chrome-text-muted);
		margin: 0;
	}
</style>
