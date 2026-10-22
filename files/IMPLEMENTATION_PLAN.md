# IMPLEMENTATION_PLAN

Step-by-step build order for Claude Code. Complete each step, run its checks, commit, then move on. Read PRD.md, TRD.md, ARCHITECTURE.md and CODE_STYLE.md first.

## Step 1 — Repo scaffold
- [ ] `git init`; create `backend/`, `frontend/`, `docs/`, `docker-compose.yml`, `Makefile`, `.env.example`, `.gitignore`.
- [ ] Backend: `pyproject.toml` (fastapi, uvicorn, pydantic-settings, sqlalchemy, alembic, faster-whisper, anthropic, python-multipart, pytest, ruff, mypy).
- [ ] Frontend: `npm create vite@latest frontend -- --template react-ts`; add zustand, vitest, eslint, prettier, `@ricky0123/vad-web`, `onnxruntime-web`.
- [ ] `GET /health` + frontend shows "API OK".
- Check: `make dev`, `make test`, `make lint` all pass.

## Step 2 — Backend core
- [ ] `core/config.py` (pydantic-settings), `core/logging.py` (JSON, PHI-safe), error handlers, CORS.
- [ ] DB session + Alembic init; models for users, sessions, transcript_segments, summaries, audit_log.
- [ ] Session CRUD endpoints + tests.

## Step 3 — ASR service
- [ ] `services/asr.py`: load model once, `transcribe(pcm: np.ndarray, sr: int) -> Segment`.
- [ ] Hallucination filter + unit tests with fixture WAVs.
- [ ] `POST /sessions/{id}/segments` REST endpoint.
- [ ] `WS /ws/sessions/{id}/audio` with bounded queue and `seq` ordering.
- Check: sample WAV → expected text; overload returns `session.busy`.

## Step 4 — Frontend recorder
- [ ] `useMicVAD` hook wrapping vad-web; expose `start/stop`, `isSpeaking`, `onSegment`.
- [ ] Controls: Start Mic, Stop, Clear, Save Recording; WORDS/CHUNKS pills.
- [ ] WS client with reconnect and resend buffer.
- Check: component tests with mocked VAD; manual speak/silence test.

## Step 5 — Transcript panel
- [ ] Append-by-seq rendering, auto-scroll + "Jump to latest", editable text, ARIA live.
- [ ] Failed-segment retry chip.
- Check: out-of-order segment events render in correct order (test).

## Step 6 — LLM analysis
- [ ] `services/llm/base.py` (`LLMProvider`), `anthropic.py` implementation using tool/JSON-schema output.
- [ ] `prompts/clinical_extraction_v1.md` with anti-hallucination rules.
- [ ] `services/analysis.py`: build prompt → call → Pydantic validate → retry ×2.
- [ ] `POST /sessions/{id}/analyze`.
- Check: golden transcripts in `tests/fixtures/` produce expected JSON; missing info stays `null`.

## Step 7 — Summary panel
- [ ] Patient header, editable clinical summary, section components with empty states exactly as in DESIGN.md.
- [ ] Process Transcript button with loading/error states.
- [ ] Copy to Prescription (formatted text) + toast.
- Check: snapshot tests; full manual flow.

## Step 8 — Persistence & history
- [ ] Autosave segments/summary; `/sessions` list and reopen.
- [ ] Summary versioning and "out of date" banner.

## Step 9 — Security & hardening
- [ ] JWT auth, password hashing, rate limiting, upload limits.
- [ ] Encryption of transcript columns, retention job, audit log, consent banner.
- [ ] Go through every box in SECURITY.md.

## Step 10 — QA & release
- [ ] Playwright E2E with a fake audio device (`--use-file-for-fake-audio-capture`).
- [ ] Accuracy evaluation script (WER + field F1) over `tests/eval/`.
- [ ] Dockerfiles, README with setup + demo script, final lint/type/test pass.

## Definition of Done (per step)
1. Code + tests written, all passing.
2. `ruff`, `mypy`, `eslint`, `tsc --noEmit` clean.
3. Docs updated if behaviour/contract changed.
4. Small conventional commit.

## Working agreement for Claude Code
- Implement one step at a time; show the plan before large changes.
- Never change the API contract or DB schema without updating API.md / DATABASE.md.
- Ask before adding a new dependency not listed in TRD.md.
