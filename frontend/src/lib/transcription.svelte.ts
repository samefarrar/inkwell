/**
 * AssemblyAI Streaming v3 transcription client.
 * Manages the WebSocket connection and exposes reactive state via Svelte 5 runes.
 */

import { BASE_API_URL } from '$lib/config';
import { startCapture, type StopFn } from '$lib/audio-capture.svelte';

export type TranscriptionStatus = 'idle' | 'connecting' | 'transcribing' | 'error';

const ASSEMBLYAI_WS_BASE = 'wss://streaming.assemblyai.com/v3/ws';

class TranscriptionClient {
	status = $state<TranscriptionStatus>('idle');
	partialText = $state('');
	errorMessage = $state('');

	private ws: WebSocket | null = null;
	private stopCapture: StopFn | null = null;
	private onFinalCallback: ((text: string) => void) | null = null;

	/** Start recording and transcribing. */
	async start(onFinal: (text: string) => void): Promise<void> {
		if (this.status === 'transcribing' || this.status === 'connecting') return;

		this.onFinalCallback = onFinal;
		this.status = 'connecting';
		this.partialText = '';
		this.errorMessage = '';

		try {
			// 1. Get temporary token from backend
			const tokenRes = await fetch(`${BASE_API_URL}/api/voice/token`);
			if (!tokenRes.ok) {
				const body = await tokenRes.json().catch(() => ({ detail: 'Token request failed' }));
				throw new Error(body.detail || `Token error: ${tokenRes.status}`);
			}
			const { token } = await tokenRes.json();

			// 2. Connect to AssemblyAI WebSocket
			const wsUrl = `${ASSEMBLYAI_WS_BASE}?sample_rate=16000&token=${token}&format_turns=true`;
			this.ws = new WebSocket(wsUrl);

			this.ws.onopen = async () => {
				try {
					// 3. Start audio capture after WS is open
					this.stopCapture = await startCapture((pcm16: ArrayBuffer) => {
						if (this.ws?.readyState === WebSocket.OPEN) {
							this.ws.send(pcm16);
						}
					});
					this.status = 'transcribing';
				} catch (err) {
					this.handleError(err instanceof Error ? err.message : 'Microphone access denied');
				}
			};

			this.ws.onmessage = (event: MessageEvent) => {
				try {
					const msg = JSON.parse(event.data);
					this.handleAssemblyMessage(msg);
				} catch {
					// Ignore parse errors
				}
			};

			this.ws.onerror = () => {
				this.handleError('Connection to transcription service failed');
			};

			this.ws.onclose = () => {
				if (this.status === 'transcribing' || this.status === 'connecting') {
					this.cleanup();
					this.status = 'idle';
				}
			};
		} catch (err) {
			this.handleError(err instanceof Error ? err.message : 'Failed to start recording');
		}
	}

	/** Stop recording and transcription. */
	stop(): void {
		// Send termination message
		if (this.ws?.readyState === WebSocket.OPEN) {
			this.ws.send(JSON.stringify({ type: 'Terminate' }));
		}
		this.cleanup();
		this.status = 'idle';
	}

	/** Handle incoming AssemblyAI messages. */
	private handleAssemblyMessage(msg: Record<string, unknown>): void {
		const type = msg.type as string;

		if (type === 'Turn') {
			const transcript = msg.transcript as string | undefined;
			const isFinal = msg.turn_is_formatted as boolean | undefined;

			if (transcript) {
				if (isFinal) {
					this.partialText = '';
					this.onFinalCallback?.(transcript);
				} else {
					this.partialText = transcript;
				}
			}
		} else if (type === 'Termination') {
			this.cleanup();
			this.status = 'idle';
		}
	}

	private handleError(message: string): void {
		this.errorMessage = message;
		this.status = 'error';
		this.cleanup();
	}

	private cleanup(): void {
		this.stopCapture?.();
		this.stopCapture = null;

		if (this.ws) {
			this.ws.onopen = null;
			this.ws.onmessage = null;
			this.ws.onerror = null;
			this.ws.onclose = null;
			if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
				this.ws.close();
			}
			this.ws = null;
		}

		this.partialText = '';
	}
}

export const transcription = new TranscriptionClient();
