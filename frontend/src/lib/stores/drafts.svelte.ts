/**
 * Drafts store — tracks 3 draft objects with streaming state.
 * Integrates StreamBuffer for smooth typewriter rendering.
 * Supports iterative synthesis rounds with highlight editing.
 */

import { StreamBuffer } from '$lib/stream-buffer.svelte';

export interface Highlight {
	start: number;
	end: number;
	sentiment: 'like' | 'flag';
	label?: string;
	note?: string;
}

export interface Draft {
	title: string;
	angle: string;
	content: string;
	wordCount: number;
	streaming: boolean;
	complete: boolean;
	highlights: Highlight[];
}

function createEmptyDraft(): Draft {
	return {
		title: '',
		angle: '',
		content: '',
		wordCount: 0,
		streaming: false,
		complete: false,
		highlights: []
	};
}

class DraftsStore {
	drafts = $state<Draft[]>([createEmptyDraft(), createEmptyDraft(), createEmptyDraft()]);
	synthesisRound = $state(0);
	synthesizing = $state(false);
	private buffers: (StreamBuffer | null)[] = [null, null, null];

	addHighlight(draftIndex: number, highlight: Highlight): void {
		const draft = this.drafts[draftIndex];
		if (!draft) return;
		draft.highlights = [...draft.highlights, highlight];
	}

	removeHighlight(draftIndex: number, highlightIndex: number): void {
		const draft = this.drafts[draftIndex];
		if (!draft) return;
		draft.highlights = draft.highlights.filter((_, i) => i !== highlightIndex);
	}

	updateHighlightLabel(draftIndex: number, highlightIndex: number, label: string): void {
		const draft = this.drafts[draftIndex];
		if (!draft || highlightIndex >= draft.highlights.length) return;
		draft.highlights = draft.highlights.map((h, i) =>
			i === highlightIndex ? { ...h, label } : h
		);
	}

	updateDraftContent(draftIndex: number, content: string): void {
		const draft = this.drafts[draftIndex];
		if (!draft) return;
		draft.content = content;
		draft.wordCount = content.split(/\s+/).filter(Boolean).length;
	}

	startDraft(index: number, title: string, angle: string): void {
		this.buffers[index]?.destroy();

		this.drafts[index] = {
			title,
			angle,
			content: '',
			wordCount: 0,
			streaming: true,
			complete: false,
			highlights: []
		};

		const draft = this.drafts[index];
		this.buffers[index] = new StreamBuffer(draft, 'content', () => {
			draft.wordCount = draft.content.split(/\s+/).filter(Boolean).length;
		});
	}

	appendChunk(index: number, content: string, done: boolean): void {
		if (done) {
			this.buffers[index]?.flush();
			this.buffers[index]?.destroy();
			this.buffers[index] = null;
			const draft = this.drafts[index];
			if (draft) draft.streaming = false;
		} else {
			this.buffers[index]?.push(content);
		}
	}

	completeDraft(index: number, wordCount: number): void {
		const draft = this.drafts[index];
		if (!draft) return;

		this.buffers[index]?.flush();
		this.buffers[index]?.destroy();
		this.buffers[index] = null;

		draft.wordCount = wordCount;
		draft.complete = true;
		draft.streaming = false;

		// Check if all drafts complete after synthesis
		if (this.synthesizing && this.allComplete) {
			this.synthesizing = false;
		}
	}

	startSynthesis(): void {
		this.synthesizing = true;
		this.synthesisRound++;
	}

	get allComplete(): boolean {
		return this.drafts.every((d) => d.complete);
	}

	get anyStarted(): boolean {
		return this.drafts.some((d) => d.streaming || d.complete);
	}

	get totalHighlights(): number {
		return this.drafts.reduce((sum, d) => sum + d.highlights.length, 0);
	}

	reset(): void {
		this.buffers.forEach((b) => b?.destroy());
		this.buffers = [null, null, null];
		this.drafts = [createEmptyDraft(), createEmptyDraft(), createEmptyDraft()];
		this.synthesisRound = 0;
		this.synthesizing = false;
	}
}

export const drafts = new DraftsStore();
