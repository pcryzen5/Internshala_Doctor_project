# TRD — Technical Requirements Document

## 1. Stack
| Layer | Choice | Why |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite | Required JS/TS; fast dev loop |
| State | Zustand | Small, simple, satisfies "state management" |
| Styling | CSS Modules / Tailwind + CSS variables | Responsive two-panel UI; matches screenshot |
| VAD | `@ricky0123/vad-web` (Silero VAD, ONNX in browser) | Runs client-side; no silence uploaded |
| Backend | Python 3.11 + FastAPI + Uvicorn | Required Python; async + WebSocket support |
| ASR | `faster-whisper` (local) with optional OpenAI Whisper API fallback | Fast, free locally, swappable |
| LLM | Anthropic Claude (default) behind an `LLMProvider` interface; OpenAI pluggable | Strong structured extraction |
| Validation | Pydantic v2 | Schema = contract between LLM and UI |
| DB | PostgreSQL (SQLite for dev) + SQLAlchemy 2 + Alembic | Reliable, migratable |
| Tests | pytest, vitest, Playwright | Unit, component, E2E |
| Packaging | Docker Compose | One-command run |

## 2. Audio specification
- Capture: `getUserMedia({audio:{channelCount:1, echoCancellation:true, noiseSuppression:true}})`.
- VAD output: mono Float32, **16 kHz**.
- Upload format: 16-bit PCM WAV (or raw PCM frames over WebSocket).
- VAD parameters (tunable): positive speech threshold 0.5, negative 0.35, min speech 250 ms, redemption (end-of-speech silence) 700 ms, pre-speech pad 300 ms, max segment 25 s (force split).
- Segments are numbered (`seq`) so the UI can order out-of-order responses.

## 3. ASR requirements
- Model default: `small.en` or `small` (multilingual); configurable via `WHISPER_MODEL`.
- Device auto: CUDA float16 if available, else CPU int8.
- Settings: `beam_size=5`, `vad_filter=False` (VAD already done client-side), `condition_on_previous_text=False` for segment independence, `initial_prompt` containing a short medical vocabulary hint.
- Drop output when `no_speech_prob > 0.6` or text matches known hallucinations ("Thanks for watching", repeated tokens).
- Concurrency: single model instance, bounded queue (worker pool size configurable), reject with 429 when overloaded.

## 4. LLM requirements
- Input: full ordered transcript (plus optional clinician-edited text).
- Output: JSON conforming to `ClinicalSummary` (see API.md / DATABASE.md). Use tool-use / JSON-schema mode; validate with Pydantic; on failure retry up to 2 times with the validation error appended.
- Temperature 0–0.2.
- Hard rules in system prompt: extract only what is stated; never infer diagnoses not stated by the clinician; use `null`/empty list when absent; keep positive and negative symptoms separate; quote supporting evidence (short span) per item.
- Long transcripts: if > model context budget, chunk → map-reduce summarise, then final extraction pass.
- Timeouts: 60 s; surface a clear error and allow retry.

## 5. Performance targets
| Metric | Target |
|---|---|
| Segment → text (GPU) | ≤ 1.5 s for a 10 s segment |
| Segment → text (CPU, small model) | ≤ 5 s for a 10 s segment |
| Analyze call (10-min consult) | ≤ 20 s |
| Frontend bundle | ≤ 400 kB gzipped excluding VAD/ONNX assets |

## 6. Communication
- **WebSocket** `/ws/sessions/{id}/audio` for live segments → transcript events.
- **REST** for everything else (sessions, analyze, export).
- JSON everywhere except audio frames.

## 7. Configuration (env)
`WHISPER_MODEL`, `WHISPER_DEVICE`, `LLM_PROVIDER`, `ANTHROPIC_API_KEY`, `LLM_MODEL`, `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `MAX_AUDIO_SECONDS`, `RETENTION_DAYS`, `LOG_LEVEL`.

## 8. Browser requirements
Secure context (HTTPS or `localhost`), `MediaDevices`, `AudioWorklet`, `WebAssembly`.

## 9. Constraints & decisions log
- VAD on the client to save bandwidth and satisfy "silence never reaches the recogniser".
- Whisper is not truly streaming; "live" = per-VAD-segment transcription.
- The LLM provider is abstracted so it can be swapped without UI changes.
