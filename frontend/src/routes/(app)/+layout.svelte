<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { ws } from '$lib/ws.svelte';
	import type { LayoutData } from './$types';

	let { children, data }: { children: any; data: LayoutData } = $props();

	onMount(() => {
		ws.connect();
	});

	onDestroy(() => {
		ws.disconnect();
	});
</script>

<svelte:head>
	<title>Inkwell</title>
</svelte:head>

<div class="app">
	<aside class="sidebar">
		<div class="sidebar-header">
			<span class="sidebar-logo">Inkwell</span>
		</div>

		<nav class="sidebar-nav">
			<a href="/dashboard" class="nav-item">Dashboard</a>
			<a href="/styles" class="nav-item">Styles</a>
			<a href="/settings" class="nav-item">Settings</a>
		</nav>

		<div class="sidebar-footer">
			<div class="user-info">
				<span class="user-name">{data.user.name}</span>
				<span class="user-plan">{data.user.plan}</span>
			</div>
			<form method="POST" action="/logout">
				<button type="submit" class="logout-btn">Log out</button>
			</form>
		</div>
	</aside>

	<div class="main-area">
		<nav class="topbar">
			<div class="nav-left">
				<span class="connection-dot" class:connected={ws.connected}></span>
			</div>
		</nav>

		<main>
			{@render children()}
		</main>
	</div>
</div>

<style>
	.app {
		min-height: 100vh;
		display: flex;
		flex-direction: row;
	}

	.sidebar {
		width: 240px;
		min-width: 240px;
		height: 100vh;
		background: #16161a;
		background-image: linear-gradient(180deg, rgba(232, 115, 58, 0.03) 0%, transparent 120px);
		border-right: 1px solid var(--chrome-border);
		display: flex;
		flex-direction: column;
		overflow: hidden;
		position: sticky;
		top: 0;
	}

	.sidebar-header {
		padding: 14px 16px 10px;
		flex-shrink: 0;
	}

	.sidebar-logo {
		font-family: 'Newsreader', serif;
		font-style: italic;
		font-weight: 600;
		font-size: 22px;
		color: var(--chrome-text);
		letter-spacing: -0.01em;
	}

	.sidebar-nav {
		display: flex;
		flex-direction: column;
		gap: 2px;
		padding: 8px;
		flex: 1;
	}

	.nav-item {
		padding: 8px 12px;
		font-family: 'Outfit', sans-serif;
		font-size: 13px;
		font-weight: 500;
		color: var(--chrome-text-muted);
		text-decoration: none;
		border-radius: 6px;
		transition:
			color 0.2s,
			background 0.2s;
	}

	.nav-item:hover {
		color: var(--chrome-text);
		background: rgba(255, 255, 255, 0.04);
	}

	.sidebar-footer {
		padding: 12px 16px;
		border-top: 1px solid var(--chrome-border);
		flex-shrink: 0;
	}

	.user-info {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 8px;
	}

	.user-name {
		font-size: 13px;
		font-weight: 500;
		color: var(--chrome-text);
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.user-plan {
		font-size: 10px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--accent);
		background: var(--accent-glow);
		padding: 2px 6px;
		border-radius: 4px;
	}

	.logout-btn {
		font-family: 'Outfit', sans-serif;
		font-size: 12px;
		color: var(--chrome-text-muted);
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
		transition: color 0.2s;
	}

	.logout-btn:hover {
		color: var(--chrome-text);
	}

	.main-area {
		flex: 1;
		display: flex;
		flex-direction: column;
		min-width: 0;
	}

	.topbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 24px;
		border-bottom: 1px solid var(--chrome-border);
		background: var(--chrome);
		height: 48px;
		flex-shrink: 0;
	}

	.nav-left {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.connection-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: #dc2626;
		animation: breathe 2s ease-in-out infinite;
	}

	.connection-dot.connected {
		background: var(--success);
	}

	@keyframes breathe {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.4;
		}
	}

	main {
		flex: 1;
		display: flex;
		flex-direction: column;
	}
</style>
