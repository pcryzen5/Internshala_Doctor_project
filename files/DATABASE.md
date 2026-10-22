# DATABASE

PostgreSQL 15+ (SQLite allowed for local dev). SQLAlchemy 2.0 models, Alembic migrations. All PKs are UUIDv4. All timestamps are `timestamptz` UTC.

## 1. Entity overview
```
users 1──* sessions 1──* transcript_segments
                    1──* summaries (versioned)
                    1──* audit_log
```

## 2. Tables

### users
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| email | text unique not null | |
| password_hash | text not null | argon2id |
| display_name | text | |
| role | text | `clinician` \| `admin` |
| created_at | timestamptz | default now() |

### sessions
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK → users | indexed |
| status | text | `recording` \| `ready` \| `analyzing` \| `reviewed` \| `failed` |
| language | text | default `en` |
| patient_label | text null | optional display name only; avoid extra identifiers |
| audio_path | text null | object-storage key; encrypted at rest |
| duration_seconds | int null | |
| started_at / ended_at | timestamptz | |
| deleted_at | timestamptz null | soft delete; hard-purge by retention job |
| created_at / updated_at | timestamptz | |

### transcript_segments
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| session_id | uuid FK | indexed |
| seq | int not null | unique with session_id |
| text | text not null | encrypted column (app-level) |
| edited_text | text null | clinician correction |
| start_ms / end_ms | int | offsets in session |
| confidence | real null | derived from Whisper |
| status | text | `done` \| `failed` |
| created_at | timestamptz | |

### summaries
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| session_id | uuid FK | indexed |
| version | int | 1,2,3… (re-process or edit creates new version) |
| source | text | `llm` \| `clinician_edit` |
| transcript_hash | text | sha256 of transcript used |
| model | text | LLM identifier |
| prompt_version | text | |
| data | jsonb | `ClinicalSummary` (below) |
| created_at | timestamptz | |
Unique `(session_id, version)`.

### audit_log
| Column | Type | Notes |
|---|---|---|
| id | bigserial PK | |
| user_id | uuid | |
| session_id | uuid null | |
| action | text | `view`, `create`, `analyze`, `export`, `delete` |
| ip | inet null | |
| created_at | timestamptz | |

## 3. `ClinicalSummary` JSON (stored in `summaries.data`)
```json
{
  "patient": {"name": null, "age": null, "sex": null, "identifiers": []},
  "chief_complaint": {"text": null, "evidence": null},
  "hpi": {"onset": null, "duration": null, "progression": null,
          "aggravating": [], "relieving": [], "narrative": null},
  "symptoms": {"positive": [{"name": "", "evidence": ""}],
               "negative": [{"name": "", "evidence": ""}]},
  "past_medical_history": {"conditions": [], "surgeries": [], "hospitalisations": []},
  "medications": [{"name": "", "dose": null, "frequency": null, "adherence": null, "evidence": ""}],
  "allergies": [{"substance": "", "reaction": null, "evidence": ""}],
  "observations": {"vitals": {"bp": null, "hr": null, "temp": null, "rr": null, "spo2": null, "other": []},
                   "examination": [], "tests_mentioned": []},
  "assessment": {"provisional": null, "differentials": [], "stated_by_clinician": true},
  "plan": {"investigations": [], "prescriptions": [], "advice": [], "follow_up": null},
  "clinical_summary": "",
  "warnings": []
}
```
Rules: absent info → `null` or `[]`; never fabricate. `evidence` = short verbatim quote from the transcript.

## 4. UI section ↔ field mapping
| UI section | Source field |
|---|---|
| Patient Name / Age / Gender | `patient` |
| Clinical Summary | `clinical_summary` |
| Chief Complaints | `chief_complaint` |
| Symptoms | `symptoms.positive` / `symptoms.negative` |
| Clinical Impression | `assessment` |
| Medications | `medications` |
| Examinations & Tests | `observations` |
| Allergies | `allergies` |
| Past Medical History | `past_medical_history` |
| History & Follow-up | `hpi` + `plan.follow_up` |

## 5. Indexes
- `sessions(user_id, created_at desc)`
- `transcript_segments(session_id, seq)` unique
- `summaries(session_id, version)` unique
- `audit_log(session_id, created_at)`

## 6. Retention & deletion
- Default retention `RETENTION_DAYS` (e.g., 30) for audio; transcripts/summaries per policy.
- Nightly job hard-deletes soft-deleted rows and audio objects older than retention.
- "Delete session" removes segments, summaries, audio.

## 7. Migrations
`alembic revision --autogenerate -m "..."`; review manually; never edit applied migrations.
