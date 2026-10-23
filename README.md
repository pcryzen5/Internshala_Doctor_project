# Live Medical Transcription & Clinical Summary System

An intelligent clinical scribe platform that captures live doctor–patient consultations via the browser microphone, transcribes speech in real time with sequence-ordered Voice Activity Detection (VAD), and leverages LLMs to generate structured clinical summaries conforming to standardized medical records.

---

## Key Features

- **Client-Side Voice Activity Detection (VAD)**: Powered by Silero VAD (`@ricky0123/vad-web`) running entirely in-browser. Ensures silence and ambient noise are never uploaded, streaming only true speech chunks (16 kHz mono Float32/PCM16).
- **Fast & Resilient Speech Recognition**: High-performance ASR service using `faster-whisper` with automatic hardware acceleration (CUDA/CPU fallback) and built-in hallucination filters (suppression of repeated filler loops and high `no_speech_prob` filtering).
- **Real-Time Streaming**: Binary WebSocket communication (`/ws/sessions/{id}/audio`) with sequence numbering (`seq`) to guarantee strict arrival order and out-of-order tolerance.
- **Structured Clinical Extraction**:
  - **Patient Demographics**: Name, age, sex, identifiers.
  - **Chief Complaint**: Primary reason for visit with transcript evidence quotes.
  - **History of Present Illness (HPI)**: Onset, duration, progression, aggravating/relieving factors.
  - **Strict Symptom Categorization**: Explicit separation of positive symptoms (`+`) and stated negative symptoms (`−`).
  - **Medications & Allergies**: Extraction of drug names, dosages, frequencies, adherence notes, and allergy reactions.
  - **Vitals & Observations**: Blood pressure, heart rate, temperature, respiratory rate, and SpO2.
  - **Assessment & Plan**: Provisional impression, differential diagnoses, prescriptions, lab orders, and follow-up guidance.
- **Clinician Review & Versioning**: Full in-place editing for transcript segments and multi-version storage for clinician-approved summaries.
- **Export Ready**: Instant generation of formatted "Copy to Prescription" plain text and raw JSON data.

---

## System Architecture

```
┌─────────────────────────────────┐
│   Doctor–Patient Consultation   │
└────────────────┬────────────────┘
                 │ (Microphone Audio)
                 ▼
┌─────────────────────────────────┐
│       Browser Frontend          │
│  - React 18 + TypeScript + Vite │
│  - Silero VAD (Client-side)     │
│  - Zustand State Management     │
└────────┬────────────────────────┘
         │ Binary PCM16 over WebSocket / REST
         ▼
┌─────────────────────────────────┐
│        FastAPI Backend          │
│  - ASR Service (faster-whisper) │
│  - Hallucination Filter         │
│  - Structured LLM Extraction    │
│  - SQLAlchemy 2.0 + Alembic     │
└────────┬───────────────┬────────┘
         │               │
         ▼               ▼
┌────────────────┐ ┌────────────────┐
│ SQLite/Postgres│ │  LLM Provider  │
│    Database    │ │(Anthropic/OpenAI│
└────────────────┘ └────────────────┘
```

---

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Zustand, `@ricky0123/vad-web`, Lucide Icons
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2, `faster-whisper`, NumPy
- **Database & ORM**: SQLAlchemy 2.0, Alembic, SQLite (dev) / PostgreSQL (production)
- **Quality & Testing**: Pytest, Vitest, Ruff, Mypy, Oxlint

---

## Getting Started

### Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: v18 or higher (v20+ recommended)
- **Git**

---

### Backend Setup

1. Navigate to the backend directory and set up a virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - **Windows**:
     ```powershell
     .venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Configure environment variables (optional for local testing; SQLite and Mock LLM are enabled by default):
   ```bash
   cp .env.example .env
   ```

5. Start the backend server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   The backend will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive API documentation is accessible at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
   The web application will be accessible at [http://localhost:5173](http://localhost:5173).

---

### Quick Start with Makefile

If you have `make` installed:
```bash
# Run both backend and frontend concurrently
make dev

# Run automated tests
make test

# Run code linters and type checkers
make lint
```

---

## Running with Docker Compose

To run the entire system with PostgreSQL:
```bash
docker compose up --build
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status (API, ASR, Database) |
| `POST` | `/api/v1/sessions` | Create a new consultation session |
| `GET` | `/api/v1/sessions` | List consultation sessions (paginated) |
| `GET` | `/api/v1/sessions/{id}` | Get session details, transcript, and summary |
| `PATCH` | `/api/v1/sessions/{id}` | Update session metadata (patient label, status) |
| `DELETE` | `/api/v1/sessions/{id}` | Soft-delete a session |
| `POST` | `/api/v1/sessions/{id}/clear` | Clear transcripts and summaries for a session |
| `POST` | `/api/v1/sessions/{id}/segments` | REST fallback for single WAV segment upload |
| `WS` | `/ws/sessions/{id}/audio` | Real-time WebSocket audio streaming |
| `PATCH` | `/api/v1/sessions/{id}/segments/{seq}` | Edit transcript text for a segment |
| `GET` | `/api/v1/sessions/{id}/transcript` | Get complete combined transcript |
| `POST` | `/api/v1/sessions/{id}/analyze` | Trigger LLM extraction of structured clinical summary |
| `GET` | `/api/v1/sessions/{id}/summaries` | List summary versions |
| `PUT` | `/api/v1/sessions/{id}/summary` | Save clinician edit as a new summary version |
| `GET` | `/api/v1/sessions/{id}/export?format=text` | Export summary in "Copy to Prescription" text format |
| `GET` | `/api/v1/sessions/{id}/export?format=json` | Export summary in raw JSON format |

---

## Automated Testing

### Backend Tests
```bash
cd backend
.venv\Scripts\python.exe -m pytest tests -v
```

### Frontend Tests & Type Checking
```bash
cd frontend
npm run typecheck
npm test -- --run
```

---

## Security & Privacy Considerations

- **Health Information (PHI/PII)**: Audio streams and transcript text are processed securely and isolated per session.
- **Prompt Isolation**: Consultations are sent to the LLM purely as data payload with strict schema constraints to prevent instruction injection.
- **Clinical Review Disclaimer**: Generated summaries are drafts designed to assist clinicians and must be reviewed and approved prior to prescription or medical record entry.
