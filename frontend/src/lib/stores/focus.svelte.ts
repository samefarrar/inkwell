/**
 * Focus mode store — tracks editor state, suggestions, comments, and chat
 * for the single-draft editing screen with AI sidebar.
 * Uses Svelte 5 runes for reactivity.
 */

export interface FocusSuggestion {
	id: string;
	quote: string;
	start: number;
	end: number;
	replacement: string;
	explanation: string;
	ruleId: string;
}

export interface FocusComment {
	id: string;
	quote: string;
	start: number;
	end: number;
	comment: string;
}

export interface FocusChatMessage {
	role: 'user' | 'ai' | 'search';
	content: string;
	done?: boolean;
	searchQuery?: string;
}

type QueuedMessage =
	| { kind: 'suggestion'; data: FocusSuggestion }
	| { kind: 'comment'; data: FocusComment; done: boolean };

class FocusStore {
	selectedDraftIndex = $state<number>(-1);
	content = $state('');
	suggestions = $state<FocusSuggestion[]>([]);
	comments = $state<FocusComment[]>([]);
	chatMessages = $state<FocusChatMessage[]>([]);
	activeChatMessage = $state<FocusChatMessage | null>(null);
	analyzing = $state(false);
	chatStreaming = $state(false);
	editorReady = $state(false);
	private pendingQueue: QueuedMessage[] = [];

	get suggestionCount(): number {
		return this.suggestions.length;
	}

	get commentCount(): number {
		return this.comments.length;
	}

	get wordCount(): number {
		const text = this.content.replace(/<[^>]+>/g, ' ');
		return text.split(/\s+/).filter(Boolean).length;
	}

	enterFocus(draftIndex: number, draftContent: string): void {
		this.selectedDraftIndex = draftIndex;
		this.content = draftContent;
		this.suggestions = [];
		this.comments = [];
		this.chatMessages = [];
		this.analyzing = true;
		this.chatStreaming = false;
		this.editorReady = false;
		this.pendingQueue = [];
	}

	leaveFocus(): void {
		this.selectedDraftIndex = -1;
		this.content = '';
		this.suggestions = [];
		this.comments = [];
		this.chatMessages = [];
		this.analyzing = false;
		this.chatStreaming = false;
		this.editorReady = false;
		this.pendingQueue = [];
		this.activeChatMessage = null;
	}

	setEditorReady(): void {
		this.editorReady = true;
		this.flushPendingQueue();
	}

	addSuggestion(suggestion: FocusSuggestion): void {
		if (!this.editorReady) {
			this.pendingQueue.push({ kind: 'suggestion', data: suggestion });
			return;
		}
		this.suggestions = [...this.suggestions, suggestion];
	}

	addComment(comment: FocusComment, done: boolean): void {
		if (!this.editorReady) {
			this.pendingQueue.push({ kind: 'comment', data: comment, done });
			if (done) this.analyzing = false;
			return;
		}
		// Skip empty sentinel comments (used to signal done with no results)
		if (comment.id && comment.quote) {
			this.comments = [...this.comments, comment];
		}
		if (done) this.analyzing = false;
	}

	acceptSuggestion(id: string): void {
		this.suggestions = this.suggestions.filter((s) => s.id !== id);
	}

	rejectSuggestion(id: string): void {
		this.suggestions = this.suggestions.filter((s) => s.id !== id);
	}

	dismissComment(id: string): void {
		this.comments = this.comments.filter((c) => c.id !== id);
	}

	addChatMessage(msg: FocusChatMessage): void {
		this.chatMessages = [...this.chatMessages, msg];
		if (msg.role === 'ai' && !msg.done) {
			this.chatStreaming = true;
		}
	}

	private flushPendingQueue(): void {
		const newSuggestions = [...this.suggestions];
		const newComments = [...this.comments];
		let setAnalyzingFalse = false;

		for (const item of this.pendingQueue) {
			if (item.kind === 'suggestion') {
				newSuggestions.push(item.data);
			} else {
				if (item.data.id && item.data.quote) {
					newComments.push(item.data);
				}
				if (item.done) setAnalyzingFalse = true;
			}
		}

		this.suggestions = newSuggestions;
		this.comments = newComments;
		if (setAnalyzingFalse) this.analyzing = false;
		this.pendingQueue = [];
	}
}

export const focus = new FocusStore();
