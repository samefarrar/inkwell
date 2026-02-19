<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { styles } from '$lib/stores/styles.svelte';
	import StyleEditor from '$lib/components/StyleEditor.svelte';

	onMount(() => {
		const id = Number(page.params.id);
		if (!isNaN(id)) {
			styles.loadStyle(id);
		}
	});
</script>

<svelte:head>
	<title>{styles.currentStyle?.name ?? 'Style'} — Inkwell</title>
</svelte:head>

<StyleEditor />
