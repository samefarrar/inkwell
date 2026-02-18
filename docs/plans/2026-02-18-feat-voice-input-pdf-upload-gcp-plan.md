---
title: "feat: AssemblyAI voice input + PDF upload with GCP storage"
type: feat
date: 2026-02-18
parent_plan: 2026-02-18-feat-inkwell-rebrand-sidebar-voice-styles-plan.md
---

# AssemblyAI Voice Input + PDF Upload with GCP Storage

## Overview

Implement the two remaining phases from the Inkwell feature plan:

1. **Phase 4: AssemblyAI Voice Input** — Mic button for dictation in TaskSelector and Interview, using AssemblyAI Streaming v3 via temporary tokens
2. **Phase 6: PDF Upload + Drag-and-Drop** — Extend style sample upload to support PDF text extraction (PyMuPDF), store originals in GCS (`gs://inkwell-uploads`), add drag-and-drop UI

## Current State

- Phases 1-3, 5, 7 are complete (sidebar, rebrand, home screen, styles CRUD, polish)
- `.env` has `ASSEMBLYAI_API_KEY` and `EXA_API_KEY`
- File upload works for `.txt`/`.md` with chunked reading + size limits
- GCP project `inkwell` with bucket `gs://inkwell-uploads` in `europe-west2`
- Service account key at `./inkwell-sa-key.json`

## Phase A: Voice Input (Backend + Frontend)

### A1. Backend — Voice Token Endpoint

**File:** `backend/src/proof_editor/api/voice.py` (new)

- `GET /api/voice/token` — generates temporary AssemblyAI token (60s TTL)
- Rate limited: 10s cooldown between requests (module-level `_last_token_time`)
- Uses `httpx` direct call to `https://streaming.assemblyai.com/v3/token`
- Reads `ASSEMBLYAI_API_KEY` from environment
- Mount in `main.py` alongside sessions + styles routers

**Acceptance:**
- [ ] Returns `{"token": "..."}` on success
- [ ] Returns 429 if called within 10s of last request
- [ ] Returns 500 if AssemblyAI API key missing or invalid

### A2. Frontend — AudioWorklet Processor

**File:** `frontend/static/pcm-recorder-processor.js` (new, plain JS)

- `PCMRecorderProcessor` extends `AudioWorkletProcessor`
- Captures Float32 audio samples from microphone
- Posts samples to main thread via `port.postMessage`

### A3. Frontend — Audio Capture Module

**File:** `frontend/src/lib/audio-capture.svelte.ts` (new)

- `startCapture(onChunk: (pcm16: ArrayBuffer) => void): Promise<StopFn>`
- Creates `AudioContext({ sampleRate: 16000 })` for hardware resampling
- Loads AudioWorklet processor from `/pcm-recorder-processor.js`
- Converts Float32 → PCM16 (Int16Array) before sending
- Returns cleanup function that stops MediaStream tracks + closes AudioContext

### A4. Frontend — AssemblyAI Transcription Client

**File:** `frontend/src/lib/transcription.svelte.ts` (new)

- `Transcription` class with Svelte 5 runes (`$state`)
- State: `idle | connecting | transcribing | error`
- `start()`: fetches token from `/api/voice/token`, connects to `wss://streaming.assemblyai.com/v3/ws?sample_rate=16000&token={token}&format_turns=true`
- `stop()`: sends termination message, closes WebSocket, stops audio capture
- Receives `Begin`, `Turn` (partial + final), `Termination` events
- Exposes `partialText` and `finalText` as reactive state
- `onFinalTranscript` callback for consumers
- Token is single-use — new token needed per connection

### A5. Frontend — VoiceButton Component

**File:** `frontend/src/lib/components/VoiceButton.svelte` (new)

- 4-state UI: `idle` | `requesting` (permission dialog) | `recording` (orange pulse) | `error`
- Click to start recording, click again to stop
- Orange accent pulsing ring animation when recording
- Props: `onTranscript: (text: string) => void` callback
- Browser support check: hides button if no `getUserMedia` or `AudioWorkletNode`
- `$effect` cleanup: stops recording on component unmount

### A6. Integration — TaskSelector + Interview

**Files to modify:**
- `frontend/src/lib/components/TaskSelector.svelte` — add VoiceButton in toolbar
- `frontend/src/lib/components/Interview.svelte` — add VoiceButton next to textarea

**Pattern:** VoiceButton's `onTranscript` callback appends text to the textarea's bound value.

## Phase B: PDF Upload + GCP Storage

### B1. Backend — Add Dependencies

```bash
cd backend && uv add pymupdf google-cloud-storage
```

### B2. Backend — PDF Text Extraction

**File:** `backend/src/proof_editor/api/styles.py` (modify)

- Add `.pdf` to `ALLOWED_EXTENSIONS`
- Add async PDF text extraction using PyMuPDF:
  - `_extract_pdf_text(data: bytes, max_pages: int = 100) -> str`
  - Run in thread pool via `asyncio.to_thread` (PyMuPDF is sync/C-level)
  - Safety: 100-page limit, 1MB text cap
  - Warning if extracted text is empty (scanned PDF)

### B3. Backend — GCP Storage Integration

**File:** `backend/src/proof_editor/storage.py` (new)

- `upload_to_gcs(data: bytes, blob_name: str, content_type: str) -> str`
- `generate_signed_url(blob_name: str, expiration_minutes: int = 60) -> str`
- Uses `google-cloud-storage` with `GOOGLE_APPLICATION_CREDENTIALS` env var
- Bucket: `inkwell-uploads`
- Blob naming: `styles/{style_id}/{uuid}_{safe_stem}{ext}`
- Optional: skip GCS if credentials not configured (graceful degradation for dev)

### B4. Backend — Update Upload Endpoint

**File:** `backend/src/proof_editor/api/styles.py` (modify)

- Extend `upload_sample` to handle `.pdf`:
  - If `.pdf`, call `await extract_pdf_text_async(raw_bytes)`
  - If `.txt`/`.md`, decode UTF-8 (existing)
- After text extraction, upload original file to GCS (if configured)
- Add `gcs_uri` field to `StyleSample` model (optional, nullable)
- Store extracted text in `content` field as before

### B5. Backend — Update StyleSample Model

**File:** `backend/src/proof_editor/models/style.py` (modify)

- Add optional `gcs_uri: str | None = None` field
- No migration needed (SQLite adds nullable columns fine)

### B6. Frontend — Drag-and-Drop + PDF Support

**File:** `frontend/src/lib/components/StyleEditor.svelte` (modify)

- Update `accept` attribute: `.txt,.md,.pdf`
- Add drag-and-drop zone around sample upload area:
  - Dashed border, accent color on dragover
  - `ondragover`, `ondragleave`, `ondrop` handlers
- Support multiple file selection
- Show file type badge (txt/md/pdf) on sample cards

### B7. Frontend — Multi-File Upload

**File:** `frontend/src/lib/stores/styles.svelte.ts` (modify)

- `uploadSample` already works for single file — extend to handle `.pdf` content type
- No concurrent upload pool needed for MVP (sequential is fine for 1-3 files)

### B8. Environment Setup

- `GOOGLE_APPLICATION_CREDENTIALS=./inkwell-sa-key.json` in `.env`
- Add `inkwell-sa-key.json` to `.gitignore`
- GCP project, bucket, and service account already created per user instructions

## Implementation Order

```
A1 → A2 → A3 → A4 → A5 → A6  (voice, sequential — each depends on previous)
B1 → B2 → B3 → B4 → B5       (PDF+GCS backend, sequential)
B6 → B7                        (PDF+drag-drop frontend)
```

Voice (A) and PDF (B) are independent — can be committed separately.

## Acceptance Criteria

### Voice
- [ ] Mic button visible in TaskSelector toolbar and Interview input
- [ ] Click to start recording, click again to stop
- [ ] 4-state UI: idle, requesting (permission), recording (orange pulse), error
- [ ] AudioWorklet captures audio off main thread at 16kHz
- [ ] Binary PCM16 chunks sent to AssemblyAI WebSocket
- [ ] Partial transcripts visible during recording
- [ ] Final transcripts appended to textarea
- [ ] Graceful error: "Microphone access denied" with retry
- [ ] Recording stops on screen transition ($effect cleanup)
- [ ] Token rate-limited (10s cooldown)
- [ ] Voice support check hides mic button on unsupported browsers

### PDF Upload
- [ ] Upload .pdf files with text extraction (max 100 pages, 1MB text)
- [ ] Original file stored in GCS (`gs://inkwell-uploads`)
- [ ] Extracted text saved in SQLite for style analysis
- [ ] Scanned PDF warning (empty text extraction)
- [ ] Drag-and-drop zone with visual feedback in StyleEditor
- [ ] File type badge on sample cards

## Files Summary

| File | Status | Phase |
|------|--------|-------|
| `backend/src/proof_editor/api/voice.py` | New | A1 |
| `frontend/static/pcm-recorder-processor.js` | New | A2 |
| `frontend/src/lib/audio-capture.svelte.ts` | New | A3 |
| `frontend/src/lib/transcription.svelte.ts` | New | A4 |
| `frontend/src/lib/components/VoiceButton.svelte` | New | A5 |
| `frontend/src/lib/components/TaskSelector.svelte` | Modify | A6 |
| `frontend/src/lib/components/Interview.svelte` | Modify | A6 |
| `backend/src/proof_editor/main.py` | Modify | A1 |
| `backend/src/proof_editor/storage.py` | New | B3 |
| `backend/src/proof_editor/api/styles.py` | Modify | B2,B4 |
| `backend/src/proof_editor/models/style.py` | Modify | B5 |
| `frontend/src/lib/components/StyleEditor.svelte` | Modify | B6 |
| `frontend/src/lib/stores/styles.svelte.ts` | Modify | B7 |
| `backend/pyproject.toml` | Modify | B1 |
| `.env` | Modify | B8 |
| `.gitignore` | Modify | B8 |
