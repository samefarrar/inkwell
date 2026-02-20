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
	// Inline feedback active state (drives decoration emphasis + sidebar highlight)
	activeSuggestionId = $state<string | null>(null);
	activeCommentId = $state<string | null>(null);
	// Reference to the TipTap Editor instance (set by FocusTipTap on mount)
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	editorInstance = $state<any>(null);
	// Comment IDs waiting for an LLM-driven approve edit to come back
	pendingApproveIds = $state<string[]>([]);
	// Set when user exits focus — content of the finished piece for save-to-profile prompt
	postFocusContent = $state<string | null>(null);
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
		this.activeSuggestionId = null;
		this.activeCommentId = null;
		this.pendingApproveIds = [];
		this.pendingQueue = [];
	}

	leaveFocus(saveContent?: string): void {
		// Capture content for save-to-profile prompt before clearing state
		this.postFocusContent = saveContent ?? (this.content || null);
		this.selectedDraftIndex = -1;
		this.content = '';
		this.suggestions = [];
		this.comments = [];
		this.chatMessages = [];
		this.analyzing = false;
		this.chatStreaming = false;
		this.editorReady = false;
		this.activeSuggestionId = null;
		this.activeCommentId = null;
		this.pendingApproveIds = [];
		this.pendingQueue = [];
		this.activeChatMessage = null;
	}

	clearPostFocusContent(): void {
		this.postFocusContent = null;
	}

	setEditorInstance(editor: unknown): void {
		this.editorInstance = editor;
	}

	setActiveSuggestion(id: string | null): void {
		this.activeSuggestionId = id;
		this.activeCommentId = null;
	}

	setActiveComment(id: string | null): void {
		this.activeCommentId = id;
		this.activeSuggestionId = null;
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
		if (this.activeSuggestionId === id) this.activeSuggestionId = null;
	}

	rejectSuggestion(id: string): void {
		this.suggestions = this.suggestions.filter((s) => s.id !== id);
		if (this.activeSuggestionId === id) this.activeSuggestionId = null;
	}

	dismissComment(id: string): void {
		this.comments = this.comments.filter((c) => c.id !== id);
		if (this.activeCommentId === id) this.activeCommentId = null;
		this.pendingApproveIds = this.pendingApproveIds.filter((i) => i !== id);
	}

	addPendingApprove(id: string): void {
		if (!this.pendingApproveIds.includes(id)) {
			this.pendingApproveIds = [...this.pendingApproveIds, id];
		}
	}

	removePendingApprove(id: string): void {
		this.pendingApproveIds = this.pendingApproveIds.filter((i) => i !== id);
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
