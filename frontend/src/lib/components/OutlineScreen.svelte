<script lang="ts">
	import { session, type OutlineNode } from '$lib/stores/session.svelte';
	import { ws } from '$lib/ws.svelte';

	// Local copy of nodes so drag-and-drop mutations don't affect the store directly
	let nodes = $state<OutlineNode[]>([...session.outlineNodes]);

	const NODE_TYPE_LABELS: Record<string, string> = {
		hook: 'Hook',
		context: 'Context',
		thesis: 'Thesis',
		story: 'Story',
		point: 'Point',
		evidence: 'Evidence',
		complication: 'Complication',
		insight: 'Insight',
		closing: 'Closing'
	};

	const NODE_TYPE_COLORS: Record<string, string> = {
		hook: 'var(--accent)',
		context: '#6b7280',
		thesis: '#3b82f6',
		story: '#8b5cf6',
		point: '#0ea5e9',
		evidence: '#10b981',
		complication: '#f59e0b',
		insight: '#ec4899',
		closing: '#6b7280'
	};

	const NODE_TYPES = Object.keys(NODE_TYPE_LABELS);

	// Drag state
	let dragIndex = $state<number | null>(null);
	let dragOverIndex = $state<number | null>(null);

	// Editing state — which node description is being edited
	let editingId = $state<string | null>(null);
	let editingType = $state<string | null>(null); // which node's type picker is open

	function handleDragStart(e: DragEvent, index: number) {
		dragIndex = index;
		if (e.dataTransfer) {
			e.dataTransfer.effectAllowed = 'move';
		}
	}

	function handleDragOver(e: DragEvent, index: number) {
		e.preventDefault();
		if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
		dragOverIndex = index;
	}

	function handleDrop(e: DragEvent, dropIndex: number) {
		e.preventDefault();
		if (dragIndex === null || dragIndex === dropIndex) {
			dragIndex = null;
			dragOverIndex = null;
			return;
		}
		const updated = [...nodes];
		const [moved] = updated.splice(dragIndex, 1);
		updated.splice(dropIndex, 0, moved);
		nodes = updated;
		dragIndex = null;
		dragOverIndex = null;
	}

	function handleDragEnd() {
		dragIndex = null;
		dragOverIndex = null;
	}

	function deleteNode(index: number) {
		nodes = nodes.filter((_, i) => i !== index);
	}

	function addNodeAfter(index: number) {
		const newNode: OutlineNode = {
			id: crypto.randomUUID(),
			node_type: 'point',
			description: ''
		};
		const updated = [...nodes];
		updated.splice(index + 1, 0, newNode);
		nodes = updated;
		// Start editing the new node immediately
		editingId = newNode.id;
	}

	function setNodeType(id: string, type: string) {
		nodes = nodes.map((n) => (n.id === id ? { ...n, node_type: type } : n));
		editingType = null;
	}

	function updateDescription(id: string, desc: string) {
		nodes = nodes.map((n) => (n.id === id ? { ...n, description: desc } : n));
	}

	function confirmOutline() {
		ws.send({ type: 'outline.confirm', nodes });
		session.goToDrafts();
	}

	function skipOutline() {
		ws.send({ type: 'outline.skip' });
		session.goToDrafts();
	}
</script>

<div class="outline-screen">
	<header class="outline-header">
		<div class="outline-header-text">
			<h2>Here's how I'd structure this piece.</h2>
			<p>Drag to reorder, click to edit. Add or remove nodes as needed.</p>
		</div>
		<button class="btn-skip" onclick={skipOutline}>Skip, just draft →</button>
	</header>

	<div class="node-list">
		{#each nodes as node, i (node.id)}
			<div
				class="node-card"
				class:drag-over={dragOverIndex === i && dragIndex !== i}
				class:dragging={dragIndex === i}
				draggable="true"
				ondragstart={(e) => handleDragStart(e, i)}
				ondragover={(e) => handleDragOver(e, i)}
				ondrop={(e) => handleDrop(e, i)}
				ondragend={handleDragEnd}
				role="listitem"
			>
				<span class="drag-handle" title="Drag to reorder">⠿</span>

				<div class="node-body">
					<!-- Type pill -->
					<div class="type-picker-wrap">
						<button
							class="type-pill"
							style="--pill-color: {NODE_TYPE_COLORS[node.node_type] ?? '#6b7280'}"
							onclick={() => (editingType = editingType === node.id ? null : node.id)}
						>
							{NODE_TYPE_LABELS[node.node_type] ?? node.node_type}
						</button>
						{#if editingType === node.id}
							<div class="type-dropdown">
								{#each NODE_TYPES as t}
									<button
										class="type-option"
										class:active={t === node.node_type}
										onclick={() => setNodeType(node.id, t)}
									>
										{NODE_TYPE_LABELS[t]}
									</button>
								{/each}
							</div>
						{/if}
					</div>

					<!-- Description -->
					{#if editingId === node.id}
						<textarea
							class="node-description-edit"
							value={node.description}
							placeholder="Describe what goes in this section..."
							oninput={(e) => updateDescription(node.id, (e.target as HTMLTextAreaElement).value)}
							onblur={() => (editingId = null)}
							autofocus
							rows="2"
						></textarea>
					{:else}
						<button
							class="node-description"
							onclick={() => (editingId = node.id)}
							title="Click to edit"
						>
							{node.description || 'Click to describe this section...'}
						</button>
					{/if}
				</div>

				<div class="node-actions">
					<button class="btn-add-below" onclick={() => addNodeAfter(i)} title="Add node below">
						+
					</button>
					<button class="btn-delete" onclick={() => deleteNode(i)} title="Remove node">×</button>
				</div>
			</div>
		{/each}

		{#if nodes.length === 0}
			<div class="empty-state">
				<button class="btn-add-first" onclick={() => addNodeAfter(-1)}>+ Add first node</button>
			</div>
		{/if}
	</div>

	<footer class="outline-footer">
		<button class="btn-add-node" onclick={() => addNodeAfter(nodes.length - 1)}>
			+ Add node
		</button>
		<button class="btn-confirm" onclick={confirmOutline} disabled={nodes.length === 0}>
			Generate drafts →
		</button>
	</footer>
</div>

<style>
	.outline-screen {
		display: flex;
		flex-direction: column;
		min-height: 100vh;
		max-width: 760px;
		margin: 0 auto;
		padding: 2rem 1.5rem;
		color: var(--ink, #2c2418);
	}

	.outline-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 2rem;
		margin-bottom: 2rem;
	}

	.outline-header-text h2 {
		font-family: 'Newsreader', serif;
		font-size: 1.5rem;
		font-weight: 600;
		margin: 0 0 0.25rem;
	}

	.outline-header-text p {
		font-size: 0.875rem;
		color: #6b7280;
		margin: 0;
	}

	.btn-skip {
		flex-shrink: 0;
		background: none;
		border: none;
		color: #6b7280;
		font-size: 0.875rem;
		cursor: pointer;
		padding: 0.25rem 0;
		text-decoration: underline;
		text-decoration-color: transparent;
		transition: color 0.15s, text-decoration-color 0.15s;
	}

	.btn-skip:hover {
		color: var(--ink, #2c2418);
		text-decoration-color: currentColor;
	}

	.node-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		flex: 1;
	}

	.node-card {
		display: flex;
		align-items: flex-start;
		gap: 0.75rem;
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 0.75rem;
		transition: border-color 0.15s, box-shadow 0.15s, opacity 0.15s;
	}

	.node-card.drag-over {
		border-color: var(--accent, #e8733a);
		box-shadow: 0 0 0 2px rgba(232, 115, 58, 0.2);
	}

	.node-card.dragging {
		opacity: 0.4;
	}

	.drag-handle {
		cursor: grab;
		color: #d1d5db;
		font-size: 1rem;
		line-height: 1.5;
		user-select: none;
		padding-top: 0.125rem;
		flex-shrink: 0;
	}

	.drag-handle:active {
		cursor: grabbing;
	}

	.node-body {
		display: flex;
		align-items: flex-start;
		gap: 0.5rem;
		flex: 1;
		min-width: 0;
	}

	.type-picker-wrap {
		position: relative;
		flex-shrink: 0;
	}

	.type-pill {
		background: color-mix(in srgb, var(--pill-color) 15%, transparent);
		color: var(--pill-color);
		border: 1px solid color-mix(in srgb, var(--pill-color) 30%, transparent);
		border-radius: 100px;
		padding: 0.2rem 0.6rem;
		font-size: 0.75rem;
		font-weight: 600;
		cursor: pointer;
		white-space: nowrap;
		transition: background 0.15s;
	}

	.type-pill:hover {
		background: color-mix(in srgb, var(--pill-color) 25%, transparent);
	}

	.type-dropdown {
		position: absolute;
		top: calc(100% + 4px);
		left: 0;
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		padding: 0.25rem;
		z-index: 10;
		min-width: 130px;
	}

	.type-option {
		display: block;
		width: 100%;
		text-align: left;
		background: none;
		border: none;
		padding: 0.375rem 0.625rem;
		font-size: 0.8125rem;
		border-radius: 5px;
		cursor: pointer;
		transition: background 0.1s;
	}

	.type-option:hover,
	.type-option.active {
		background: #f3f4f6;
	}

	.node-description {
		flex: 1;
		min-width: 0;
		text-align: left;
		background: none;
		border: none;
		padding: 0.125rem 0.25rem;
		font-size: 0.875rem;
		color: var(--ink, #2c2418);
		cursor: text;
		border-radius: 4px;
		line-height: 1.5;
		transition: background 0.1s;
		word-break: break-word;
	}

	.node-description:hover {
		background: #f9fafb;
	}

	.node-description-edit {
		flex: 1;
		min-width: 0;
		border: 1px solid #e5e7eb;
		border-radius: 4px;
		padding: 0.25rem 0.375rem;
		font-size: 0.875rem;
		font-family: inherit;
		color: var(--ink, #2c2418);
		resize: vertical;
		line-height: 1.5;
		background: #fafafa;
	}

	.node-description-edit:focus {
		outline: none;
		border-color: var(--accent, #e8733a);
		box-shadow: 0 0 0 2px rgba(232, 115, 58, 0.15);
	}

	.node-actions {
		display: flex;
		gap: 0.25rem;
		flex-shrink: 0;
	}

	.btn-add-below,
	.btn-delete {
		background: none;
		border: 1px solid transparent;
		border-radius: 4px;
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		font-size: 1rem;
		color: #9ca3af;
		transition: color 0.1s, border-color 0.1s, background 0.1s;
	}

	.btn-add-below:hover {
		color: var(--accent, #e8733a);
		border-color: var(--accent, #e8733a);
		background: rgba(232, 115, 58, 0.05);
	}

	.btn-delete:hover {
		color: #ef4444;
		border-color: #fca5a5;
		background: #fef2f2;
	}

	.empty-state {
		display: flex;
		justify-content: center;
		padding: 2rem;
	}

	.btn-add-first {
		background: none;
		border: 2px dashed #d1d5db;
		border-radius: 8px;
		padding: 0.75rem 1.5rem;
		color: #6b7280;
		cursor: pointer;
		font-size: 0.875rem;
		transition: border-color 0.15s, color 0.15s;
	}

	.btn-add-first:hover {
		border-color: var(--accent, #e8733a);
		color: var(--accent, #e8733a);
	}

	.outline-footer {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 1.5rem;
		padding-top: 1rem;
		border-top: 1px solid #f3f4f6;
	}

	.btn-add-node {
		background: none;
		border: 1px solid #e5e7eb;
		border-radius: 6px;
		padding: 0.5rem 1rem;
		font-size: 0.875rem;
		color: #6b7280;
		cursor: pointer;
		transition: border-color 0.15s, color 0.15s;
	}

	.btn-add-node:hover {
		border-color: var(--accent, #e8733a);
		color: var(--accent, #e8733a);
	}

	.btn-confirm {
		background: var(--accent, #e8733a);
		color: white;
		border: none;
		border-radius: 8px;
		padding: 0.625rem 1.5rem;
		font-size: 0.9375rem;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.15s;
	}

	.btn-confirm:hover:not(:disabled) {
		opacity: 0.9;
	}

	.btn-confirm:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}
</style>
