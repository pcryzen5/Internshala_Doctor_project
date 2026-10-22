# PHASES — Delivery Roadmap

Each phase ends with something demonstrable. Do not start a phase until the previous phase's exit criteria pass.

## Phase 0 — Foundations (0.5 day)
- Monorepo: `/backend` (FastAPI), `/frontend` (React + TS + Vite).
- Tooling: ruff, black, mypy, pytest, eslint, prettier, vitest, pre-commit.
- `.env.example`, Docker Compose skeleton, CI (lint + tests).
- **Exit:** `make dev` starts both apps; health check returns 200; CI is green.

## Phase 1 — Audio capture + VAD (1 day)
- Mic permission flow, Start/Stop/Clear buttons.
- Browser VAD (`@ricky0123/vad-web`, Silero) emitting speech segments as 16 kHz mono Float32.
- Words / Chunks counters (chunks live, words stubbed).
- **Exit:** speaking produces chunk-count increments; silence produces none; segments can be played back for debugging.

## Phase 2 — ASR backend (1–2 days)
- `POST /api/transcribe` (single segment) then `WS /ws/sessions/{id}/audio` (streaming).
- `faster-whisper` service with model loaded once at startup, configurable size/device.
- Hallucination filters (drop empty / repeated-filler outputs, `no_speech_prob` threshold).
- **Exit:** a recorded WAV and a live mic segment both return correct text within the latency target.

## Phase 3 — Live transcript UI (1 day)
- Transcript panel appends text as segments return; auto-scroll; ARIA live region.
- Partial "transcribing…" placeholder per segment; error and retry states.
- Editable transcript; word count; Save Recording (audio + text).
- **Exit:** 5-minute simulated consultation displays live with no lost segments and correct ordering.

## Phase 4 — LLM analysis (1–2 days)
- Pydantic `ClinicalSummary` schema (see DATABASE.md / API.md).
- `POST /api/sessions/{id}/analyze` → LLM structured output → validation → retry on invalid JSON.
- Prompt with anti-hallucination rules; evidence quotes; confidence flags.
- **Exit:** golden-transcript tests pass; absent info stays empty.

## Phase 5 — Summary panel (1 day)
- Render all sections from the screenshot design: patient header, clinical summary (editable), chief complaints, symptoms, clinical impression, medications, examinations & tests, allergies, past medical history, history & follow-up.
- Loading / empty / error states; Clear; Copy to Prescription.
- **Exit:** full flow works end to end in the browser.

## Phase 6 — Persistence & history (1 day)
- PostgreSQL (SQLite in dev), Alembic migrations, session CRUD.
- Save transcript, audio reference, summary, edits (versioned).
- **Exit:** reload the page and reopen a past session intact.

## Phase 7 — Hardening (1–2 days)
- Auth (JWT), rate limits, CORS, input limits, audit log.
- Retention + delete-my-data, consent banner, PHI-safe logging.
- E2E tests (Playwright), load test of transcription endpoint.
- **Exit:** SECURITY.md checklist fully ticked.

## Phase 8 — Stretch
- Speaker diarisation (doctor/patient), multilingual (Hindi/Marathi/English code-switching), floating chat assistant, PDF export, FHIR export.

## Suggested timeline
Phases 0–5 = MVP (about 6–8 working days). Phases 6–7 = production-ready. Phase 8 optional.
