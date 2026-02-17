/**
 * Drafts store — tracks 3 draft objects with streaming state.
 * Integrates StreamBuffer for smooth typewriter rendering.
 */

import { StreamBuffer } from '$lib/stream-buffer.svelte';

export interface Draft {
	title: string;
	angle: string;
	content: string;
	wordCount: number;
	streaming: boolean;
	complete: boolean;
}

function createEmptyDraft(): Draft {
	return {
		title: '',
		angle: '',
		content: '',
		wordCount: 0,
		streaming: false,
		complete: false
	};
}

class DraftsStore {
	drafts = $state<Draft[]>([createEmptyDraft(), createEmptyDraft(), createEmptyDraft()]);
	private buffers: (StreamBuffer | null)[] = [null, null, null];

	startDraft(index: number, title: string, angle: string): void {
		this.buffers[index]?.destroy();

		this.drafts[index] = {
			title,
			angle,
			content: '',
			wordCount: 0,
			streaming: true,
			complete: false
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
	}

	get allComplete(): boolean {
		return this.drafts.every((d) => d.complete);
	}

	get anyStarted(): boolean {
		return this.drafts.some((d) => d.streaming || d.complete);
	}

	reset(): void {
		this.buffers.forEach((b) => b?.destroy());
		this.buffers = [null, null, null];
		this.drafts = [createEmptyDraft(), createEmptyDraft(), createEmptyDraft()];
	}
}

export const drafts = new DraftsStore();
