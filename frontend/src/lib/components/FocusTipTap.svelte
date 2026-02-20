<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Highlight from '@tiptap/extension-highlight';
	import { focus } from '$lib/stores/focus.svelte';
	import { ws } from '$lib/ws.svelte';
	import {
		InlineFeedbackExtension,
		buildDecorations,
		setDecorations
	} from '$lib/extensions/inline-feedback';

	let element: HTMLDivElement;
	let editor = $state<Editor | null>(null);
	let updating = false;
	let updateTimer: ReturnType<typeof setTimeout> | null = null;

	/**
	 * Convert plain-text content (with \n\n paragraph breaks) to proper HTML.
	 * Returns the string unchanged if it already contains HTML tags.
	 * This ensures TipTap creates real paragraph nodes so that:
	 * 1. The document has paragraph structure (comment cards insert between paras)
	 * 2. Python's _strip_html offsets still match (both collapse \n\n to a space)
	 */
	function plainTextToHtml(text: string): string {
		if (/<[a-z][^>]*>/i.test(text)) return text;
		const paras = text.split(/\n{2,}/);
		return paras
			.map((p) => {
				const inner = p.trim().replace(/\n+/g, ' ');
				return inner ? `<p>${inner}</p>` : '';
			})
			.filter(Boolean)
			.join('');
	}

	onMount(() => {
		const e = new Editor({
			element,
			extensions: [StarterKit, Highlight, InlineFeedbackExtension],
			content: plainTextToHtml(focus.content),
			editorProps: {
				attributes: {
					class: 'focus-editor-content'
				},
				handleClick(_view, _pos, event) {
					const el = event.target as HTMLElement;
					const sid = el.closest?.('[data-suggestion-id]')?.getAttribute('data-suggestion-id');
					const cid = el.closest?.('[data-comment-id]')?.getAttribute('data-comment-id');
					if (sid) {
						focus.setActiveSuggestion(sid);
						return false;
					}
					if (cid) {
						focus.setActiveComment(cid);
						return false;
					}
					return false;
				}
			},
			onCreate: () => {
				focus.setEditorReady();
				focus.setEditorInstance(e);
			},
			onUpdate: ({ editor: upd }) => {
				if (updating) return;
				if (updateTimer) clearTimeout(updateTimer);
				updateTimer = setTimeout(() => {
					focus.content = upd.getHTML();
					updateTimer = null;
				}, 300);
			}
		});
		editor = e;
	});

	onDestroy(() => {
		if (updateTimer) clearTimeout(updateTimer);
		focus.setEditorInstance(null);
		editor?.destroy();
		editor = null;
	});

	// Rebuild decorations whenever suggestions, comments, or active IDs change.
	$effect(() => {
		if (!editor) return;
		const decoSet = buildDecorations(
			editor.state.doc,
			focus.suggestions,
			focus.comments,
			focus.activeSuggestionId,
			focus.activeCommentId,
			{
				onDismissComment(id) {
					focus.dismissComment(id);
					ws.send({ type: 'focus.feedback', id, action: 'dismiss', feedback_type: 'comment' });
				},
				onApproveComment(id) {
					focus.addPendingApprove(id);
					const editor = focus.editorInstance;
					const currentContent = editor ? editor.getHTML() : '';
					ws.send({ type: 'focus.approve_comment', id, current_content: currentContent });
				},
				onSuggestionClick(id) {
					focus.setActiveSuggestion(id);
				},
				onCommentClick(id) {
					focus.setActiveComment(id);
				}
			},
			focus.pendingApproveIds
		);
		setDecorations(editor.view, decoSet);
	});

	export function getEditor(): Editor | null {
		return editor;
	}

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

	/* ── Inline Suggestion Decorations ─────────────────────────────────────── */

	/* Strikethrough only — no background fill, keeps text readable */
	.editor-area :global(.suggestion-range) {
		text-decoration: line-through;
		text-decoration-color: #d9534f;
		text-decoration-thickness: 1.5px;
		cursor: pointer;
		border-radius: 2px;
	}

	.editor-area :global(.suggestion-range.suggestion-active) {
		text-decoration-color: #c0392b;
		background: rgba(192, 57, 43, 0.06);
	}

	/* Green replacement shown inline — small, italic, clearly secondary */
	.editor-area :global(.suggestion-replacement) {
		color: #2d7a3e;
		font-size: 0.88em;
		font-style: italic;
		cursor: pointer;
		border-radius: 2px;
		padding: 0 2px;
	}

	.editor-area :global(.suggestion-replacement.suggestion-active) {
		background: rgba(45, 122, 62, 0.1);
	}

	/* ── Inline Comment Decorations ─────────────────────────────────────────── */

	/* Subtle dotted underline on quoted text — far less intrusive than a fill */
	.editor-area :global(.comment-range) {
		border-bottom: 1.5px dotted rgba(180, 120, 40, 0.55);
		cursor: pointer;
	}

	.editor-area :global(.comment-range.comment-active) {
		border-bottom-color: #b47728;
		border-bottom-style: solid;
		background: rgba(180, 120, 40, 0.07);
	}

	/* Grayed-out while LLM edit is in flight */
	.editor-area :global(.comment-range.comment-pending) {
		opacity: 0.45;
		border-bottom-style: dashed;
	}

	/* Comment callout card — light paper surface, readable in the editor area */
	.editor-area :global(.comment-card-inline) {
		display: block;
		margin: 6px 0 18px;
		padding: 11px 14px;
		background: var(--paper-surface, #f3f0eb);
		border: 1px solid var(--paper-border, #e2ddd5);
		border-left: 3px solid var(--accent, #e8733a);
		border-radius: 6px;
		font-family: 'Outfit', sans-serif;
		cursor: pointer;
		user-select: none;
		transition: box-shadow 0.15s, border-left-color 0.15s;
	}

	.editor-area :global(.comment-card-inline.comment-active) {
		border-left-color: var(--accent, #e8733a);
		box-shadow: 0 0 0 2px rgba(232, 115, 58, 0.18);
	}

	.editor-area :global(.comment-card-inline:hover) {
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
	}

	.editor-area :global(.comment-card-header) {
		display: flex;
		align-items: flex-start;
		gap: 8px;
		margin-bottom: 8px;
	}

	.editor-area :global(.comment-card-icon) {
		font-size: 14px;
		flex-shrink: 0;
		margin-top: 1px;
		line-height: 1.5;
	}

	.editor-area :global(.comment-card-text) {
		font-size: 13px;
		color: var(--ink, #2c2a25);
		line-height: 1.5;
		flex: 1;
	}

	.editor-area :global(.comment-card-actions) {
		display: flex;
		justify-content: flex-end;
		gap: 6px;
		margin-top: 2px;
	}

	.editor-area :global(.comment-card-approve) {
		font-family: 'Outfit', sans-serif;
		font-size: 11px;
		color: var(--accent, #e8733a);
		background: transparent;
		border: 1px solid var(--accent, #e8733a);
		border-radius: 4px;
		padding: 2px 8px;
		cursor: pointer;
		transition: background 0.15s;
	}

	.editor-area :global(.comment-card-approve:hover:not(:disabled)) {
		background: rgba(232, 115, 58, 0.1);
	}

	.editor-area :global(.comment-card-approve:disabled) {
		opacity: 0.55;
		cursor: wait;
	}

	.editor-area :global(.comment-card-inline.comment-pending) {
		opacity: 0.65;
	}

	.editor-area :global(.comment-card-dismiss) {
		font-family: 'Outfit', sans-serif;
		font-size: 11px;
		/* Use ink-muted, not chrome-text-muted — we're on a light paper background */
		color: var(--ink-muted, #a8a090);
		background: transparent;
		border: 1px solid var(--paper-border, #e2ddd5);
		border-radius: 4px;
		padding: 2px 8px;
		cursor: pointer;
		transition: color 0.15s, border-color 0.15s;
	}

	.editor-area :global(.comment-card-dismiss:hover) {
		color: var(--ink-secondary, #7a7062);
		border-color: var(--ink-muted, #a8a090);
	}
</style>
