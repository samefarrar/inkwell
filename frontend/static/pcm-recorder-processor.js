/**
 * AudioWorklet processor that captures PCM audio and posts it to the main thread.
 * Runs off the main thread for glitch-free recording.
 */
class PCMRecorderProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (input && input[0] && input[0].length > 0) {
      // Copy the Float32 samples and send to main thread
      this.port.postMessage(new Float32Array(input[0]));
    }
    return true;
  }
}

registerProcessor('pcm-recorder-processor', PCMRecorderProcessor);
