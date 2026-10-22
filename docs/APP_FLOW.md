# APP_FLOW — User Flows & State Machine

## 1. Primary flow (happy path)
1. User opens the app → sees empty transcript ("Ready — click Start Mic…") and empty summary states.
2. Clicks **Start Mic** → browser permission prompt → granted.
3. Status becomes *Listening*. VAD indicator idle.
4. User speaks → VAD detects speech → indicator pulses → on pause a **chunk** is emitted.
5. Chunk sent to backend → transcribed → text appended; **Words** and **Chunks** counters update.
6. Steps 4–5 repeat for the whole consultation.
7. Clicks **Stop** → capture ends; any in-flight chunks finish; status *Ready to process*.
8. (Optional) edits transcript text; (optional) **Save Recording**.
9. Clicks **Process Transcript with AI** → spinner on summary header → backend calls LLM.
10. Summary panel populates: patient header, clinical summary, chief complaints, symptoms, impression, medications, exams & tests, allergies, PMH, history & follow-up.
11. Clinician reviews/edits fields → **Copy to Prescription** → formatted text on clipboard → toast.
12. Session auto-saved; appears in history.

## 2. Session state machine
```
IDLE ──start──▶ LISTENING ──speech──▶ CAPTURING ──pause──▶ LISTENING
  ▲                │                                          │
  │              stop                                       stop
  │                ▼                                          ▼
  └──clear── READY_TO_PROCESS ◀───────────────────────────────┘
                   │ process
                   ▼
              ANALYZING ──ok──▶ REVIEW ──clear──▶ IDLE
                   │ error
                   ▼
              ANALYZE_ERROR ──retry──▶ ANALYZING
```
Segment sub-state: `queued → transcribing → done | failed(retry)`.

## 3. Alternative & error flows
| Case | Flow |
|---|---|
| Permission denied | Inline banner with browser-specific instructions; Start stays enabled to retry |
| No microphone found | Message + device selector refresh |
| Only silence | No chunks created; hint "No speech detected — check your mic" after 15 s |
| Process pressed with empty transcript | Button disabled; tooltip explains |
| Network lost mid-session | Banner "Reconnecting…"; buffered segments resent |
| Segment fails ASR | Red chip "retry" inline in transcript |
| LLM fails | Error toast + retry button; transcript preserved |
| Clear pressed | If unsaved content → confirm; then reset transcript, counters, summary |
| Page refresh while recording | Warn via `beforeunload`; session recovered from server on reload |
| Edited transcript after analysis | Show "Summary out of date — Re-process" |

## 4. Screens / routes
| Route | Purpose |
|---|---|
| `/login` | Sign in (Phase 7) |
| `/` | Main workspace (two-panel) |
| `/sessions` | Past sessions list |
| `/sessions/:id` | Reopen a session in the workspace (read/edit) |
| `/settings` | Mic device, model, language, privacy |

## 5. Events (frontend ↔ backend)
| Direction | Event | Payload |
|---|---|---|
| C→S | `audio.segment` | `{seq, sampleRate, pcm16(binary)}` |
| S→C | `transcript.segment` | `{seq, text, start, end, confidence}` |
| S→C | `transcript.error` | `{seq, code, message}` |
| S→C | `session.busy` | `{queueDepth}` |
| C→S | `session.stop` | `{}` |

## 6. Copy to Prescription format
```
Patient: <name>, <age>/<sex>
Chief complaint: ...
Symptoms: + ... ; − ...
Impression: ...
Medications: ...
Allergies: ...
Plan / Follow-up: ...
```
