<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link
		href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Outfit:wght@400;500;600;700&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

{@render children()}

<style>
	:global(:root) {
		/* Chrome (dark workspace) */
		--chrome: #1a1a1e;
		--chrome-surface: #26262b;
		--chrome-border: #38383d;
		--chrome-text: #e4e4e7;
		--chrome-text-muted: #71717a;

		/* Paper (warm reading surfaces) */
		--paper: #faf8f5;
		--paper-surface: #f3f0eb;
		--paper-border: #e2ddd5;

		/* Ink (text on paper) */
		--ink: #2c2418;
		--ink-secondary: #7a7062;
		--ink-muted: #a8a090;

		/* Accent */
		--accent: #e8733a;
		--accent-glow: rgba(232, 115, 58, 0.15);
		--accent-soft: #f4a574;

		/* Semantic */
		--success: #4ade80;
		--thought-bg: #2d2822;
		--thought-border: #4a3f2f;
	}

	:global(body) {
		margin: 0;
		font-family: 'Outfit', sans-serif;
		background: var(--chrome);
		color: var(--chrome-text);
		-webkit-font-smoothing: antialiased;
		-moz-osx-font-smoothing: grayscale;
	}

	:global(*, *::before, *::after) {
		box-sizing: border-box;
	}
</style>
