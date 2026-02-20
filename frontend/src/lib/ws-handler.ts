/**
 * Shared WebSocket message handler — routes server messages to the session and drafts stores.
 * Call setupWsHandler() in onMount and destroy the returned unsubscribe in onDestroy.
 */

import type { Node as PMNode } from '@tiptap/pm/model';
import { ws, type ServerMessage } from '$lib/ws.svelte';
import { session, type ChatMessage } from '$lib/stores/session.svelte';
import { drafts } from '$lib/stores/drafts.svelte';
import { focus } from '$lib/stores/focus.svelte';
import { StreamBuffer } from '$lib/stream-buffer.svelte';
import { buildOffsetMap } from '$lib/extensions/offset-mapper';

export function setupWsHandler(): () => void {
	const activeBuffers: StreamBuffer[] = [];

	const unsubscribe = ws.onMessage((msg: ServerMessage) => {
		switch (msg.type) {
			case 'thought': {
				const thoughtMsg = session.addMessage({
					role: 'thought',
					content: '',
					thought: {
						assessment: '',
						missing: msg.missing,
						sufficient: msg.sufficient
					}
				});
				const tBuf = new StreamBuffer(thoughtMsg.thought!, 'assessment', () => {
					thoughtMsg.content = thoughtMsg.thought!.assessment;
				});
				tBuf.push(msg.assessment);
				activeBuffers.push(tBuf);
				break;
			}

			case 'interview.question': {
				const qMsg = session.addMessage({
					role: 'ai',
					content: ''
				});
				const qBuf = new StreamBuffer(qMsg, 'content');
				qBuf.push(msg.question);
				activeBuffers.push(qBuf);
				break;
			}

			case 'search.result':
				session.addMessage({
					role: 'search',
					content: msg.summary,
					search: { query: msg.query, summary: msg.summary }
				});
				break;

			case 'ready_to_draft':
				session.setReadyToDraft(msg.summary, msg.key_material);
				break;

			case 'outline.nodes':
				session.goToOutline(msg.nodes);
				break;

			case 'draft.start':
				if (session.screen !== 'drafts') {
					session.goToDrafts();
				}
				drafts.startDraft(msg.draft_index, msg.title, msg.angle);
				break;

			case 'draft.chunk':
				drafts.appendChunk(msg.draft_index, msg.content, msg.done);
				break;

			case 'draft.complete':
				drafts.completeDraft(msg.draft_index, msg.word_count);
				break;

			case 'status':
				session.addMessage({
					role: 'status',
					content: msg.message
				});
				break;

			case 'error':
				if (drafts.synthesizing) {
					drafts.synthesizing = false;
				}
				session.addMessage({
					role: 'status',
					content: `Error: ${msg.message}`
				});
				console.error('[WS] Error from server:', msg.message);
				break;

			case 'focus.suggestion':
				if (session.screen !== 'focus') break;
				focus.addSuggestion({
					id: msg.id,
					quote: msg.quote,
					start: msg.start,
					end: msg.end,
					replacement: msg.replacement,
					explanation: msg.explanation,
					ruleId: msg.rule_id
				});
				break;

			case 'focus.comment':
				if (session.screen !== 'focus') break;
				if (msg.comment) {
					focus.addComment(
						{
							id: msg.id,
							quote: msg.quote,
							start: msg.start,
							end: msg.end,
							comment: msg.comment
						},
						msg.done
					);
				} else if (msg.done) {
					focus.analyzing = false;
				}
				break;

			case 'focus.chat_response': {
				if (session.screen !== 'focus') break;
				if (focus.activeChatMessage && !focus.activeChatMessage.done) {
					focus.activeChatMessage.content += msg.content;
					focus.activeChatMessage.done = msg.done;
					if (msg.done) focus.activeChatMessage = null;
				} else {
					focus.addChatMessage({ role: 'ai', content: msg.content, done: msg.done });
				}
				break;
			}

			case 'focus.edit': {
				if (session.screen !== 'focus') break;
				const editor = focus.editorInstance;
				if (editor && msg.old_text) {
					// Block-local search: never cross paragraph boundaries — offset map
					// separator spaces are virtual positions that can corrupt structure.
					const { state, view } = editor;
					const doc = state.doc;
					let tr = state.tr;
					let replaced = false;

					doc.descendants((node: PMNode, pos: number) => {
						if (replaced || !node.isBlock) return !replaced;

						let blockText = '';
						const charPos: number[] = [];
						node.descendants((child: PMNode, childPos: number) => {
							if (child.isText && child.text) {
								for (let i = 0; i < child.text.length; i++) {
									charPos.push(pos + 1 + childPos + i);
									blockText += child.text[i];
								}
							}
						});

						const textIdx = blockText.indexOf(msg.old_text);
						if (textIdx === -1) return true;

						const from = charPos[textIdx];
						const to = charPos[textIdx + msg.old_text.length - 1] + 1;
						tr = tr.insertText(msg.new_text, from, to);
						replaced = true;
						return false;
					});

					if (replaced) view.dispatch(tr);
				}
				focus.removePendingApprove(msg.comment_id);
				focus.dismissComment(msg.comment_id);
				break;
			}
		}
	});

	return () => {
		unsubscribe();
		activeBuffers.forEach((b) => b.destroy());
	};
}

/**
 * Parse session detail response from the API and hydrate stores.
 */
export function hydrateSessionFromApi(data: {
	session_id: number;
	task_type: string;
	topic: string;
	status: string;
	interview_messages?: Array<{
		role: string;
		content: string;
		thought_json?: string | null;
		search_json?: string | null;
		ready_json?: string | null;
	}>;
	rounds?: Record<string, Array<{ title: string; angle: string; content: string; word_count: number }>>;
	highlights?: Array<{
		draft_index: number;
		start: number;
		end: number;
		sentiment: 'like' | 'flag';
		label?: string;
		note?: string;
	}>;
}): void {
	// Parse interview messages
	if (data.interview_messages?.length) {
		const msgs: ChatMessage[] = data.interview_messages.map((m) => {
			const msg: ChatMessage = {
				role: m.role as ChatMessage['role'],
				content: m.content
			};
			if (m.thought_json) {
				const t = JSON.parse(m.thought_json);
				msg.thought = { assessment: t.assessment, missing: t.missing ?? [], sufficient: t.sufficient ?? false };
			}
			if (m.search_json) {
				const s = JSON.parse(m.search_json);
				msg.search = { query: s.query, summary: s.summary };
			}
			return msg;
		});
		session.messages = msgs;
	}

	session.taskType = data.task_type ?? '';
	session.topic = data.topic ?? '';
	session.currentSessionId = data.session_id;

	const roundKeys = Object.keys(data.rounds ?? {}).map(Number);
	const maxRound = roundKeys.length > 0 ? Math.max(...roundKeys) : 0;

	if (roundKeys.length > 0) {
		drafts.loadFromSessionWithRounds(data.rounds!, data.highlights ?? [], maxRound);
		session.screen = 'drafts';
	} else {
		session.screen = 'interview';
	}
}
