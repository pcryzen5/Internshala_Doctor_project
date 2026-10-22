# ARCHITECTURE

## 1. System context
```
┌──────────────┐   audio    ┌─────────────────────────────────────────┐
│  Clinician   │──────────▶│  Browser (React + TS)                   │
│  (mic)       │            │  ├─ AudioCapture (getUserMedia)         │
└──────────────┘            │  ├─ VAD (Silero / vad-web, in-browser)  │
                            │  ├─ Zustand store                       │
                            │  └─ UI: Transcript panel | Summary panel│
                            └───────────┬─────────────────────────────┘
                       speech segments  │  WebSocket / REST (JSON)
                                        ▼
                            ┌─────────────────────────────────────────┐
                            │  FastAPI backend                         │
                            │  ├─ API layer (routers)                  │
                            │  ├─ Session service                      │
                            │  ├─ ASR service (faster-whisper)         │
                            │  ├─ Analysis service (LLM + validation)  │
                            │  └─ Repository layer (SQLAlchemy)        │
                            └───────┬───────────────┬─────────────────┘
                                    ▼               ▼
                             PostgreSQL        LLM provider API
                             + audio storage   (Claude / OpenAI)
```

## 2. Pipeline
1. **Capture** — mic stream opened in the browser.
2. **VAD** — Silero model flags speech frames; on end-of-speech a segment (Float32, 16 kHz) is emitted.
3. **Transport** — segment encoded as PCM16 and sent over the WebSocket with `seq` and `session_id`.
4. **ASR** — backend queues segment → faster-whisper → text + timestamps + confidence.
5. **Live display** — backend pushes `transcript.segment` event; UI appends text by `seq`.
6. **Finish** — user presses *Stop* then *Process Transcript with AI*.
7. **Analysis** — backend sends full transcript to LLM with schema → validated `ClinicalSummary`.
8. **Review** — UI renders structured fields; clinician edits; Copy to Prescription / export.
9. **Persist** — transcript, audio ref, summary versions stored.

## 3. Backend layout
```
backend/
  app/
    main.py                # FastAPI app factory, middleware, routers
    core/                  # config, logging, security, errors
    api/                   # routers: sessions, transcribe(ws), analyze, export, auth
    schemas/               # Pydantic models (request/response, ClinicalSummary)
    services/
      asr.py               # WhisperService
      llm/                 # LLMProvider interface + anthropic.py, openai.py
      analysis.py          # prompt build, call, validate, retry
      sessions.py
    db/                    # models, session, repositories, alembic/
    prompts/               # versioned prompt templates
  tests/
```

## 4. Frontend layout
```
frontend/src/
  app/                     # App shell, routing, providers
  features/
    recorder/              # useMicVAD hook, controls, counters
    transcript/            # TranscriptPanel, TranscriptEditor
    summary/               # SummaryPanel, section components, CopyToPrescription
    sessions/              # history list
    assistant/             # floating chat bubble (stretch)
  lib/                     # api client, ws client, audio utils, types
  store/                   # zustand slices: session, transcript, summary, ui
  styles/
```

## 5. Key design decisions
| Decision | Rationale |
|---|---|
| Client-side VAD | Lower bandwidth/cost, privacy (silence never leaves device), instant chunking |
| Per-segment ASR | Whisper is a batch model; VAD segments approximate streaming |
| Provider interface for LLM & ASR | Swap local ↔ hosted without touching callers |
| Pydantic schema as single source of truth | Same contract for LLM output validation, API, and TS types (generated) |
| Transcript is the source of truth | Summary can be regenerated from edited transcript at any time |
| Stateless API + DB-backed sessions | Horizontal scaling; reconnect safe |

## 6. Concurrency & scaling
- ASR is the bottleneck: run in a thread/process pool, bounded queue, backpressure via 429/`busy` event.
- Scale out by running multiple ASR workers (GPU) behind the API; keep sessions sticky for WS.
- LLM calls are async and idempotent per `(session_id, transcript_hash)`.

## 7. Failure handling
| Failure | Behaviour |
|---|---|
| Mic denied | Inline error with how to enable permissions |
| WS drops | Auto-reconnect; unsent segments buffered (bounded) and resent by `seq` |
| ASR error on a segment | Mark segment as failed, show retry chip, continue |
| LLM invalid JSON | Retry w/ error feedback ×2, then show error and keep transcript |
| LLM timeout | Show retry; transcript untouched |

## 8. Observability
Structured JSON logs (no PHI), request IDs, metrics: segment latency, queue depth, LLM latency, validation-failure rate.
