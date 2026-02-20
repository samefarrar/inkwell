/**
 * WebSocket client — connects to the backend and handles typed messages.
 * Auto-reconnects with exponential backoff.
 */

import { BASE_WS_URL } from '$lib/config';

export type ServerMessage =
  | { type: 'thought'; assessment: string; missing: string[]; sufficient: boolean }
  | { type: 'interview.question'; question: string; context: string }
  | { type: 'search.result'; query: string; summary: string }
  | { type: 'ready_to_draft'; summary: string; key_material: string[] }
  | { type: 'draft.start'; draft_index: number; title: string; angle: string }
  | { type: 'draft.chunk'; draft_index: number; content: string; done: boolean }
  | { type: 'draft.complete'; draft_index: number; word_count: number }
  | { type: 'draft.synthesized'; content: string; sent_to_proof: boolean }
  | { type: 'status'; message: string }
  | { type: 'error'; message: string }
  | {
      type: 'focus.suggestion';
      id: string;
      quote: string;
      start: number;
      end: number;
      replacement: string;
      explanation: string;
      rule_id: string;
    }
  | {
      type: 'focus.comment';
      id: string;
      quote: string;
      start: number;
      end: number;
      comment: string;
      done: boolean;
    }
  | { type: 'focus.chat_response'; content: string; done: boolean }
  | { type: 'focus.edit'; comment_id: string; old_text: string; new_text: string }
  | {
      type: 'outline.nodes';
      nodes: Array<{ id: string; node_type: string; description: string }>;
    };

export type ClientMessage =
  | { type: 'task.select'; task_type: string; topic: string }
  | { type: 'interview.answer'; answer: string }
  | {
      type: 'draft.highlight';
      draft_index: number;
      start: number;
      end: number;
      sentiment: 'like' | 'flag';
      label?: string;
      note?: string;
    }
  | { type: 'highlight.update'; draft_index: number; highlight_index: number; label: string }
  | { type: 'highlight.remove'; draft_index: number; highlight_index: number }
  | { type: 'draft.edit'; draft_index: number; content: string }
  | { type: 'draft.synthesize' }
  | { type: 'session.resume'; session_id: number }
  | { type: 'session.cancel' }
  | { type: 'focus.enter'; draft_index: number }
  | { type: 'focus.exit' }
  | { type: 'focus.chat'; message: string }
  | { type: 'focus.feedback'; id: string; action: 'accept' | 'reject' | 'dismiss'; feedback_type: 'suggestion' | 'comment' }
  | { type: 'focus.approve_comment'; id: string; current_content: string }
  | {
      type: 'outline.confirm';
      nodes: Array<{ id: string; node_type: string; description: string }>;
    }
  | { type: 'outline.skip' };

type MessageHandler = (msg: ServerMessage) => void;

const MAX_RECONNECT_DELAY = 30000;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Set<MessageHandler> = new Set();
  private reconnectDelay = 1000;
  private shouldReconnect = true;
  private _connected = $state(false);
  private pendingSends: ClientMessage[] = [];

  get connected(): boolean {
    return this._connected;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    this.ws = new WebSocket(BASE_WS_URL);

    this.ws.onopen = () => {
      this._connected = true;
      this.reconnectDelay = 1000;
      console.log('[WS] Connected');
      // Flush any messages queued before connection opened
      for (const msg of this.pendingSends) {
        this.ws!.send(JSON.stringify(msg));
      }
      this.pendingSends = [];
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const msg: ServerMessage = JSON.parse(event.data);
        this.handlers.forEach((handler) => handler(msg));
      } catch (e) {
        console.error('[WS] Failed to parse message:', e);
      }
    };

    this.ws.onclose = (event: CloseEvent) => {
      this._connected = false;
      console.log('[WS] Disconnected', event.code);
      if (event.code === 4001) {
        // Auth expired — redirect, don't reconnect
        window.location.href = '/login?returnTo=' + encodeURIComponent(window.location.pathname);
        return;
      }
      if (this.shouldReconnect) {
        setTimeout(() => this.connect(), this.reconnectDelay);
        this.reconnectDelay = Math.min(this.reconnectDelay * 2, MAX_RECONNECT_DELAY);
      }
    };

    this.ws.onerror = (error: Event) => {
      console.error('[WS] Error:', error);
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.ws?.close();
  }

  send(msg: ClientMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    } else {
      // Queue messages to be sent when connection opens
      this.pendingSends.push(msg);
    }
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }
}

/** Default client (no provider — uses Anthropic by default) */
export const ws = new WebSocketClient();
