/**
 * Drafts store — tracks 3 draft objects with streaming state.
 * Uses Svelte 5 runes for reactivity.
 */

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

  startDraft(index: number, title: string, angle: string): void {
    this.drafts[index] = {
      title,
      angle,
      content: '',
      wordCount: 0,
      streaming: true,
      complete: false
    };
  }

  appendChunk(index: number, content: string, done: boolean): void {
    const draft = this.drafts[index];
    if (!draft) return;

    if (done) {
      draft.streaming = false;
    } else {
      draft.content += content;
      draft.wordCount = draft.content.split(/\s+/).filter(Boolean).length;
    }
  }

  completeDraft(index: number, wordCount: number): void {
    const draft = this.drafts[index];
    if (!draft) return;
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
    this.drafts = [createEmptyDraft(), createEmptyDraft(), createEmptyDraft()];
  }
}

export const drafts = new DraftsStore();
