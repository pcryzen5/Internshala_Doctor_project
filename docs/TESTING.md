# TESTING

## 1. Strategy (pyramid)
| Level | Tools | Scope |
|---|---|---|
| Unit | pytest, vitest | Pure functions, services, hooks, components |
| Integration | pytest + httpx + test DB | API ↔ DB, ASR service with fixture audio, LLM with mock provider |
| E2E | Playwright | Full browser flow with fake mic |
| Evaluation | custom scripts | ASR WER, extraction F1, hallucination checks |
| Non-functional | locust/k6, axe | Load, accessibility |

Coverage targets: backend ≥ 80 %, frontend ≥ 70 %, critical paths (analysis validation, segment ordering) ≈ 100 %.

## 2. Backend tests
- **ASR:** fixture WAVs (clean speech, silence, noise, accented speech); assert text similarity ≥ threshold; silence/noise returns empty; hallucination filter drops known phrases.
- **Analysis:** mock `LLMProvider` returning valid, invalid, truncated JSON → verify validation, retry count, error mapping.
- **Prompt regression:** golden transcripts → expected `ClinicalSummary` (field-level assertions, not exact text).
- **API:** auth required, 404/422 cases, pagination, soft delete, rate limit, size limits.
- **DB:** migrations apply/rollback; unique `(session_id, seq)`; versioning.
- **WS:** ordering by `seq`, reconnect resend, backpressure `session.busy`.

## 3. Frontend tests
- `useMicVAD` with mocked vad-web: emits segments, handles permission denied.
- Store slices: counters, append-by-seq, clear.
- TranscriptPanel: auto-scroll, jump-to-latest, edit.
- SummaryPanel: every empty state text, populated state, editable fields, Copy to Prescription output format.
- Button state matrix from DESIGN.md.

## 4. E2E (Playwright)
Chromium flags: `--use-fake-ui-for-media-stream --use-fake-device-for-media-stream --use-file-for-fake-audio-capture=tests/fixtures/consult_01.wav`
Scenarios:
1. Start → transcript appears → Stop → Process → summary populated.
2. Mic permission denied → error banner.
3. Network drop mid-session → reconnect → no lost/duplicate segments.
4. LLM failure → retry succeeds.
5. Clear with unsaved edits → confirm dialog.
6. Reopen past session.

## 5. Evaluation sets
Create `tests/eval/` with 20+ **synthetic** consultations (scripted + recorded by team; no real patient data) covering: simple fever, diabetes follow-up, chest pain with negatives, multiple medications, allergy mentions, no allergies stated, patient corrects themselves, noisy background, Hinglish phrases.
Metrics:
- **WER** per transcript.
- **Field precision/recall/F1** for symptoms, medications, allergies, diagnosis.
- **Hallucination rate** = items in output not supported by transcript (target 0 for meds/allergies).
- **Negation accuracy** — "no fever" must land in negative symptoms.

## 6. Non-functional
- Load: 10 concurrent sessions, 1 segment / 5 s each; p95 segment latency within TRD targets.
- Accessibility: axe on main screens, keyboard-only walkthrough.
- Browser matrix: Chrome, Edge, Firefox, Safari latest.

## 7. CI
On every PR: lint → type check → unit → integration → E2E (headless) → build. Block merge on failure. Nightly: evaluation suite + dependency audit.

## 8. Manual QA checklist
- [ ] Speak, pause, speak: chunks increment only on speech.
- [ ] Silence 30 s: no chunks, hint shown.
- [ ] Drug names ("metformin 500 mg twice daily") captured correctly.
- [ ] Negations placed correctly.
- [ ] Copy to Prescription pastes cleanly into a text editor.
- [ ] Works on phone browser over HTTPS.
