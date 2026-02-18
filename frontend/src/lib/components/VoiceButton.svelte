<script lang="ts">
  import { onMount } from 'svelte';
  import { checkVoiceSupport } from '$lib/audio-capture.svelte';
  import { transcription } from '$lib/transcription.svelte';

  let { onTranscript }: { onTranscript: (text: string) => void } = $props();

  let supported = $state(false);

  onMount(() => {
    supported = checkVoiceSupport().supported;
  });

  function toggle() {
    if (transcription.status === 'transcribing' || transcription.status === 'connecting') {
      transcription.stop();
    } else {
      transcription.start(onTranscript);
    }
  }

  $effect(() => {
    // Cleanup on unmount
    return () => {
      if (transcription.status === 'transcribing') {
        transcription.stop();
      }
    };
  });
</script>

{#if supported}
  <button
    class="voice-btn"
    class:recording={transcription.status === 'transcribing'}
    class:connecting={transcription.status === 'connecting'}
    class:error={transcription.status === 'error'}
    onclick={toggle}
    title={transcription.status === 'transcribing' ? 'Stop recording' : 'Start voice input'}
    disabled={transcription.status === 'connecting'}
  >
    {#if transcription.status === 'connecting'}
      <span class="icon">...</span>
    {:else if transcription.status === 'transcribing'}
      <span class="icon">&#9632;</span>
    {:else}
      <span class="icon">&#127908;</span>
    {/if}
  </button>
  {#if transcription.status === 'error'}
    <span class="error-msg">{transcription.errorMessage}</span>
  {/if}
  {#if transcription.partialText}
    <span class="partial">{transcription.partialText}</span>
  {/if}
{/if}

<style>
  .voice-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 1px solid var(--chrome-border);
    background: var(--chrome-surface);
    color: var(--chrome-text-muted);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    flex-shrink: 0;
  }

  .voice-btn:hover {
    border-color: var(--accent);
    color: var(--chrome-text);
  }

  .voice-btn.recording {
    background: var(--accent);
    border-color: var(--accent);
    color: white;
    animation: voicePulse 1.5s ease-in-out infinite;
  }

  .voice-btn.connecting {
    opacity: 0.6;
    cursor: wait;
  }

  .voice-btn.error {
    border-color: #dc2626;
    color: #dc2626;
  }

  .icon {
    font-size: 14px;
    line-height: 1;
  }

  .error-msg {
    font-family: 'Outfit', sans-serif;
    font-size: 11px;
    color: #dc2626;
    margin-left: 6px;
  }

  .partial {
    font-family: 'Outfit', sans-serif;
    font-size: 12px;
    color: var(--accent);
    opacity: 0.7;
    margin-left: 6px;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  @keyframes voicePulse {
    0% { box-shadow: 0 0 0 0 rgba(232, 115, 58, 0.4); }
    70% { box-shadow: 0 0 0 8px rgba(232, 115, 58, 0); }
    100% { box-shadow: 0 0 0 0 rgba(232, 115, 58, 0); }
  }
</style>
