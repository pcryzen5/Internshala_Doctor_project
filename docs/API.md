# API

Base URL: `/api/v1`. JSON unless noted. Auth: `Authorization: Bearer <JWT>` (Phase 7; open in dev with `AUTH_DISABLED=true`).

## Error format
```json
{"error": {"code": "validation_error", "message": "Human readable", "details": {}}}
```
Codes: `unauthorized` 401, `forbidden` 403, `not_found` 404, `validation_error` 422, `rate_limited` 429, `asr_failed` 502, `llm_failed` 502, `internal` 500.

## Auth
| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/auth/login` | `{email,password}` | `{access_token, expires_in}` |
| POST | `/auth/logout` | – | 204 |
| GET | `/auth/me` | – | user |

## Sessions
| Method | Path | Description |
|---|---|---|
| POST | `/sessions` | Create session `{language?}` → `{id, status}` |
| GET | `/sessions` | List (paginated: `?limit=&cursor=`) |
| GET | `/sessions/{id}` | Session + segments + latest summary |
| PATCH | `/sessions/{id}` | Update `patient_label`, status |
| DELETE | `/sessions/{id}` | Soft delete |
| POST | `/sessions/{id}/clear` | Remove transcript + summaries, keep session |

## Transcription
### WebSocket `WS /ws/sessions/{id}/audio?token=...`
Client → server
- Binary frame: header JSON length (4 bytes) + header `{"seq":1,"sampleRate":16000}` + PCM16 mono bytes.
- Text: `{"type":"session.stop"}`

Server → client
```json
{"type":"transcript.segment","seq":1,"text":"I have had fever since two days","start_ms":1200,"end_ms":5200,"confidence":0.91}
{"type":"transcript.error","seq":2,"code":"asr_failed","message":"..."}
{"type":"session.busy","queue_depth":4}
```
### REST fallback
`POST /sessions/{id}/segments` — `multipart/form-data`: `audio` (wav), `seq` → `{seq,text,start_ms,end_ms,confidence}`.

## Transcript editing
| Method | Path | Body |
|---|---|---|
| PATCH | `/sessions/{id}/segments/{seq}` | `{edited_text}` |
| GET | `/sessions/{id}/transcript` | → `{text, segments[]}` |

## Analysis
`POST /sessions/{id}/analyze`
```json
{"use_edited": true, "language": "en"}
```
Response 200
```json
{"summary_id":"...","version":1,"model":"...","data":{ /* ClinicalSummary — see DATABASE.md */ }}
```
Errors: 422 if transcript empty; 502 `llm_failed` after retries.

`GET /sessions/{id}/summaries` → versions list.
`PUT /sessions/{id}/summary` — clinician edit; body = `ClinicalSummary`; creates new version with `source="clinician_edit"`.

## Export
| Method | Path | Output |
|---|---|---|
| GET | `/sessions/{id}/export?format=text` | plain text (Copy to Prescription format) |
| GET | `/sessions/{id}/export?format=json` | ClinicalSummary |
| GET | `/sessions/{id}/export?format=pdf` | PDF (stretch) |
| GET | `/sessions/{id}/audio` | Recorded audio (authorised) |

## Assistant (stretch)
`POST /sessions/{id}/chat` `{message}` → `{reply}` — answers only from the session transcript/summary.

## Health
`GET /health` → `{status:"ok", asr:"ready", db:"ok"}`

## Limits
- Segment ≤ 30 s / 2 MB. Session ≤ 2 h. Transcript for analysis ≤ 100k chars.
- Rate limit: 60 req/min/user; WS ≤ 5 segments/s.

## Versioning
Breaking changes → `/api/v2`. Frontend types are generated from OpenAPI (`npm run gen:types`).
