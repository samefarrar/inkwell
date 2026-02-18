/**
 * Shared WebSocket message handler — routes server messages to the session and drafts stores.
 * Call setupWsHandler() in onMount and destroy the returned unsubscribe in onDestroy.
 */

import { ws, type ServerMessage } from '$lib/ws.svelte';
import { session, type ChatMessage } from '$lib/stores/session.svelte';
import { drafts } from '$lib/stores/drafts.svelte';
import { StreamBuffer } from '$lib/stream-buffer.svelte';

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
