<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Highlight from '@tiptap/extension-highlight';
	import { focus } from '$lib/stores/focus.svelte';

	let element: HTMLDivElement;
	let editor: Editor | null = null;
	let updating = false;
	let updateTimer: ReturnType<typeof setTimeout> | null = null;

	onMount(() => {
		editor = new Editor({
			element,
			extensions: [StarterKit, Highlight],
			content: focus.content,
			editorProps: {
				attributes: {
					class: 'focus-editor-content'
				}
			},
			onCreate: () => {
				focus.setEditorReady();
			},
			onUpdate: ({ editor: e }) => {
				if (updating) return;
				if (updateTimer) clearTimeout(updateTimer);
				updateTimer = setTimeout(() => {
					focus.content = e.getHTML();
					updateTimer = null;
				}, 300);
			}
		});
	});

	onDestroy(() => {
		if (updateTimer) clearTimeout(updateTimer);
		editor?.destroy();
		editor = null;
	});

	function toggleBold() { editor?.chain().focus().toggleBold().run(); }
	function toggleItalic() { editor?.chain().focus().toggleItalic().run(); }
	function toggleH1() { editor?.chain().focus().toggleHeading({ level: 1 }).run(); }
	function toggleH2() { editor?.chain().focus().toggleHeading({ level: 2 }).run(); }
	function toggleH3() { editor?.chain().focus().toggleHeading({ level: 3 }).run(); }
	function toggleBulletList() { editor?.chain().focus().toggleBulletList().run(); }
	function toggleOrderedList() { editor?.chain().focus().toggleOrderedList().run(); }
</script>

<div class="tiptap-wrapper">
	<div class="toolbar">
		<button class="tool-btn" class:active={editor?.isActive('bold')} onclick={toggleBold} title="Bold">
			<strong>B</strong>
		</button>
		<button class="tool-btn" class:active={editor?.isActive('italic')} onclick={toggleItalic} title="Italic">
			<em>I</em>
		</button>
		<span class="tool-sep"></span>
		<button class="tool-btn" class:active={editor?.isActive('heading', { level: 1 })} onclick={toggleH1} title="Heading 1">
			H1
		</button>
		<button class="tool-btn" class:active={editor?.isActive('heading', { level: 2 })} onclick={toggleH2} title="Heading 2">
			H2
		</button>
		<button class="tool-btn" class:active={editor?.isActive('heading', { level: 3 })} onclick={toggleH3} title="Heading 3">
			H3
		</button>
		<span class="tool-sep"></span>
		<button class="tool-btn" class:active={editor?.isActive('bulletList')} onclick={toggleBulletList} title="Bullet list">
			&bull;
		</button>
		<button class="tool-btn" class:active={editor?.isActive('orderedList')} onclick={toggleOrderedList} title="Ordered list">
			1.
		</button>
	</div>
	<div class="editor-area" bind:this={element}></div>
</div>

<style>
	.tiptap-wrapper {
		display: flex;
		flex-direction: column;
		height: 100%;
	}

	.toolbar {
		display: flex;
		align-items: center;
		gap: 2px;
		padding: 8px 12px;
		border-bottom: 1px solid var(--paper-border);
		background: var(--paper-surface);
		flex-shrink: 0;
	}

	.tool-btn {
		padding: 4px 8px;
		border: none;
		border-radius: 4px;
		background: transparent;
		color: var(--ink-secondary);
		font-family: 'Outfit', sans-serif;
		font-size: 13px;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.15s, color 0.15s;
		min-width: 28px;
		text-align: center;
	}

	.tool-btn:hover {
		background: var(--paper-border);
		color: var(--ink);
	}

	.tool-btn.active {
		background: var(--accent-glow);
		color: var(--accent);
	}

	.tool-sep {
		width: 1px;
		height: 18px;
		background: var(--paper-border);
		margin: 0 4px;
	}

	.editor-area {
		flex: 1;
		overflow-y: auto;
		padding: 32px;
	}

	.editor-area :global(.focus-editor-content) {
		max-width: 680px;
		margin: 0 auto;
		font-family: 'Newsreader', serif;
		font-size: 18px;
		line-height: 1.7;
		color: var(--ink);
		outline: none;
		min-height: 100%;
	}

	.editor-area :global(.focus-editor-content p) {
		margin: 0 0 1em;
	}

	.editor-area :global(.focus-editor-content h1) {
		font-size: 32px;
		font-weight: 600;
		margin: 0 0 0.5em;
		line-height: 1.3;
	}

	.editor-area :global(.focus-editor-content h2) {
		font-size: 24px;
		font-weight: 600;
		margin: 1.2em 0 0.4em;
		line-height: 1.3;
	}

	.editor-area :global(.focus-editor-content h3) {
		font-size: 20px;
		font-weight: 600;
		margin: 1em 0 0.3em;
		line-height: 1.3;
	}

	.editor-area :global(.focus-editor-content ul),
	.editor-area :global(.focus-editor-content ol) {
		margin: 0 0 1em;
		padding-left: 1.5em;
	}

	.editor-area :global(.focus-editor-content li) {
		margin: 0.3em 0;
	}

	.editor-area :global(.focus-editor-content strong) {
		font-weight: 600;
	}

	.editor-area :global(.focus-editor-content em) {
		font-style: italic;
	}
</style>
