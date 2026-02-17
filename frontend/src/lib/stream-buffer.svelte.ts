/**
 * StreamBuffer — smooth typewriter rendering for streamed LLM content.
 * Buffers incoming WebSocket chunks and drains at a constant rate
 * via requestAnimationFrame for a smooth reading experience.
 *
 * ~180 chars/sec at 60fps (3 chars per frame).
 */

export class StreamBuffer {
	private buffer = '';
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	private target: Record<string, any>;
	private key: string;
	private rafId: number | null = null;
	private charsPerFrame = 3;
	private onUpdate?: () => void;

	constructor(
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		target: Record<string, any>,
		key: string = 'content',
		onUpdate?: () => void
	) {
		this.target = target;
		this.key = key;
		this.onUpdate = onUpdate;
	}

	/** Enqueue text from a WebSocket chunk. Starts the drain loop if idle. */
	push(text: string): void {
		this.buffer += text;
		if (this.rafId === null) {
			this.drain();
		}
	}

	/** Immediately render all remaining buffered text. */
	flush(): void {
		if (this.rafId !== null) {
			cancelAnimationFrame(this.rafId);
			this.rafId = null;
		}
		this.target[this.key] += this.buffer;
		this.buffer = '';
		this.onUpdate?.();
	}

	/** Cancel the rAF loop and discard any buffered text. */
	destroy(): void {
		if (this.rafId !== null) {
			cancelAnimationFrame(this.rafId);
			this.rafId = null;
		}
		this.buffer = '';
	}

	private drain(): void {
		if (this.buffer.length === 0) {
			this.rafId = null;
			return;
		}

		const chunk = this.buffer.slice(0, this.charsPerFrame);
		this.buffer = this.buffer.slice(this.charsPerFrame);
		this.target[this.key] += chunk;
		this.onUpdate?.();

		this.rafId = requestAnimationFrame(() => this.drain());
	}
}
