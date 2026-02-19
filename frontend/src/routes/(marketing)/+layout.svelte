<script lang="ts">
	import type { LayoutData } from './$types';

	let { children, data }: { children: any; data: LayoutData } = $props();
</script>

<svelte:head>
	<title>Inkwell — AI Writing Partner</title>
</svelte:head>

<nav class="marketing-nav">
	<a href="/" class="nav-logo">Inkwell</a>
	<div class="nav-links">
		<a href="/#features">Features</a>
		<a href="/#pricing">Pricing</a>
		{#if data.user}
			<a href="/dashboard" class="nav-cta">Dashboard</a>
		{:else}
			<a href="/login" class="nav-link-muted">Log in</a>
			<a href="/register" class="nav-cta">Get Started</a>
		{/if}
	</div>
</nav>

<main>
	{@render children()}
</main>

<footer class="marketing-footer">
	<div class="footer-inner">
		<span class="footer-logo">Inkwell</span>
		<div class="footer-links">
			<a href="/#features">Features</a>
			<a href="/#pricing">Pricing</a>
		</div>
		<p class="footer-copy">&copy; {new Date().getFullYear()} Inkwell. All rights reserved.</p>
	</div>
</footer>

<style>
	.marketing-nav {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 16px 40px;
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		z-index: 100;
		background: rgba(26, 26, 30, 0.85);
		backdrop-filter: blur(12px);
		border-bottom: 1px solid var(--chrome-border);
	}

	.nav-logo {
		font-family: 'Newsreader', serif;
		font-style: italic;
		font-weight: 600;
		font-size: 22px;
		color: var(--chrome-text);
		text-decoration: none;
		letter-spacing: -0.01em;
	}

	.nav-links {
		display: flex;
		align-items: center;
		gap: 24px;
	}

	.nav-links a {
		color: var(--chrome-text-muted);
		text-decoration: none;
		font-size: 14px;
		font-weight: 500;
		transition: color 0.2s;
	}

	.nav-links a:hover {
		color: var(--chrome-text);
	}

	.nav-link-muted {
		color: var(--chrome-text-muted) !important;
	}

	.nav-cta {
		background: var(--accent) !important;
		color: white !important;
		padding: 8px 20px;
		border-radius: 24px;
		font-weight: 600 !important;
		transition:
			opacity 0.2s,
			color 0s !important;
	}

	.nav-cta:hover {
		opacity: 0.9;
	}

	main {
		padding-top: 64px;
	}

	.marketing-footer {
		border-top: 1px solid var(--chrome-border);
		padding: 48px 40px 32px;
	}

	.footer-inner {
		max-width: 1000px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 16px;
	}

	.footer-logo {
		font-family: 'Newsreader', serif;
		font-style: italic;
		font-weight: 600;
		font-size: 18px;
		color: var(--chrome-text-muted);
	}

	.footer-links {
		display: flex;
		gap: 24px;
	}

	.footer-links a {
		color: var(--chrome-text-muted);
		text-decoration: none;
		font-size: 13px;
		transition: color 0.2s;
	}

	.footer-links a:hover {
		color: var(--chrome-text);
	}

	.footer-copy {
		font-size: 12px;
		color: var(--chrome-text-muted);
		margin: 0;
		opacity: 0.6;
	}
</style>
