<script lang="ts">
	import { enhance } from '$app/forms';
	import type { ActionData } from './$types';

	let { form }: { form: ActionData } = $props();
</script>

<svelte:head>
	<title>Sign up — Inkwell</title>
</svelte:head>

<div class="auth-page">
	<div class="auth-card">
		<h1>Create your account</h1>
		<p class="subtitle">Start writing with AI in minutes</p>

		{#if form?.error}
			<div class="error-banner">{form.error}</div>
		{/if}

		<form method="POST" use:enhance>
			<label>
				<span>Name</span>
				<input
					type="text"
					name="name"
					value={form?.name ?? ''}
					required
					autocomplete="name"
				/>
			</label>

			<label>
				<span>Email</span>
				<input
					type="email"
					name="email"
					value={form?.email ?? ''}
					required
					autocomplete="email"
				/>
			</label>

			<label>
				<span>Password</span>
				<input
					type="password"
					name="password"
					required
					minlength="8"
					autocomplete="new-password"
				/>
				<span class="hint">At least 8 characters</span>
			</label>

			<button type="submit">Create account</button>
		</form>

		<p class="switch-link">
			Already have an account? <a href="/login">Log in</a>
		</p>
	</div>
</div>

<style>
	.auth-page {
		min-height: calc(100vh - 64px);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 40px 20px;
	}

	.auth-card {
		width: 100%;
		max-width: 400px;
	}

	h1 {
		font-family: 'Newsreader', serif;
		font-weight: 600;
		font-size: 28px;
		margin: 0 0 4px;
		color: var(--chrome-text);
	}

	.subtitle {
		color: var(--chrome-text-muted);
		font-size: 14px;
		margin: 0 0 28px;
	}

	.error-banner {
		background: rgba(239, 68, 68, 0.12);
		border: 1px solid rgba(239, 68, 68, 0.3);
		color: #fca5a5;
		padding: 10px 14px;
		border-radius: 8px;
		font-size: 13px;
		margin-bottom: 20px;
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	label span {
		font-size: 13px;
		font-weight: 500;
		color: var(--chrome-text-muted);
	}

	.hint {
		font-size: 12px !important;
		color: var(--chrome-text-muted) !important;
		opacity: 0.7;
	}

	input {
		padding: 10px 14px;
		border-radius: 8px;
		border: 1px solid var(--chrome-border);
		background: var(--chrome-surface);
		color: var(--chrome-text);
		font-size: 15px;
		font-family: inherit;
		outline: none;
		transition: border-color 0.2s;
	}

	input:focus {
		border-color: var(--accent);
	}

	button {
		margin-top: 4px;
		padding: 12px;
		border-radius: 8px;
		border: none;
		background: var(--accent);
		color: white;
		font-size: 15px;
		font-weight: 600;
		font-family: inherit;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	button:hover {
		opacity: 0.9;
	}

	.switch-link {
		text-align: center;
		font-size: 13px;
		color: var(--chrome-text-muted);
		margin-top: 24px;
	}

	.switch-link a {
		color: var(--accent);
		text-decoration: none;
		font-weight: 500;
	}

	.switch-link a:hover {
		text-decoration: underline;
	}
</style>
