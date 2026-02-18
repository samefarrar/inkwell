<script lang="ts">
	import { onMount } from 'svelte';
	import { styles } from '$lib/stores/styles.svelte';
	import StyleManager from '$lib/components/StyleManager.svelte';

	onMount(() => {
		styles.loadStyles();
	});
</script>

<svelte:head>
	<title>Styles — Inkwell</title>
</svelte:head>

<StyleManager />
