<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { ws } from '$lib/ws.svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import type { LayoutData } from './$types';

	let { children, data }: { children: any; data: LayoutData } = $props();

	let sidebarCollapsed = $state(false);

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
	<div class="sidebar-wrapper" class:collapsed={sidebarCollapsed}>
		<Sidebar
			onResume={(id) => goto('/session/' + id)}
			onNewSession={() => goto('/dashboard')}
		/>

		<div class="sidebar-footer">
			<div class="user-info">
				<span class="user-name">{data.user.name}</span>
				<span class="user-plan">{data.user.plan}</span>
			</div>
			<form method="POST" action="/logout">
				<button type="submit" class="logout-btn">Log out</button>
			</form>
		</div>
	</div>

	<div class="main-area">
		<nav class="topbar">
			<div class="nav-left">
				<button
					class="collapse-btn"
					onclick={() => (sidebarCollapsed = !sidebarCollapsed)}
					aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
				>
					{sidebarCollapsed ? '›' : '‹'}
				</button>
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

	.sidebar-wrapper {
		width: 240px;
		min-width: 240px;
		height: 100vh;
		position: sticky;
		top: 0;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		border-right: 1px solid var(--chrome-border);
		transition: width 0.2s ease, min-width 0.2s ease;
		flex-shrink: 0;
	}

	.sidebar-wrapper.collapsed {
		width: 0;
		min-width: 0;
	}

	.sidebar-footer {
		padding: 12px 16px;
		border-top: 1px solid var(--chrome-border);
		background: #16161a;
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
		padding: 0 16px;
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

	.collapse-btn {
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: transparent;
		border: 1px solid var(--chrome-border);
		border-radius: 6px;
		color: var(--chrome-text-muted);
		font-size: 16px;
		cursor: pointer;
		transition:
			color 0.2s,
			background 0.2s;
		flex-shrink: 0;
	}

	.collapse-btn:hover {
		color: var(--chrome-text);
		background: rgba(255, 255, 255, 0.04);
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
