/**
 * AudioWorklet-based microphone capture at 16kHz.
 * Converts Float32 → PCM16 and sends chunks via callback.
 */

export type StopFn = () => void;

/** Convert Float32 audio samples to PCM16 (Int16Array). */
function float32ToPcm16(float32: Float32Array): ArrayBuffer {
	const pcm16 = new Int16Array(float32.length);
	for (let i = 0; i < float32.length; i++) {
		const s = Math.max(-1, Math.min(1, float32[i]));
		pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
	}
	return pcm16.buffer;
}

/**
 * Start capturing audio from the microphone.
 * @param onChunk Called with PCM16 ArrayBuffer for each audio chunk
 * @returns A function to stop recording and release resources
 */
export async function startCapture(onChunk: (pcm16: ArrayBuffer) => void): Promise<StopFn> {
	const stream = await navigator.mediaDevices.getUserMedia({
		audio: {
			sampleRate: 16000,
			channelCount: 1,
			echoCancellation: true,
			noiseSuppression: true
		}
	});

	const audioCtx = new AudioContext({ sampleRate: 16000 });
	await audioCtx.audioWorklet.addModule('/pcm-recorder-processor.js');

	const source = audioCtx.createMediaStreamSource(stream);
	const workletNode = new AudioWorkletNode(audioCtx, 'pcm-recorder-processor');

	workletNode.port.onmessage = (event: MessageEvent<Float32Array>) => {
		const pcm16 = float32ToPcm16(event.data);
		onChunk(pcm16);
	};

	source.connect(workletNode);
	workletNode.connect(audioCtx.destination);

	return () => {
		workletNode.disconnect();
		source.disconnect();
		stream.getTracks().forEach((track) => track.stop());
		audioCtx.close();
	};
}

/** Check if voice recording is supported in this browser. */
export function checkVoiceSupport(): { supported: boolean; reason?: string } {
	if (!navigator.mediaDevices?.getUserMedia) {
		return { supported: false, reason: 'No microphone support' };
	}
	if (typeof AudioWorkletNode === 'undefined') {
		return { supported: false, reason: 'Browser too old' };
	}
	return { supported: true };
}
