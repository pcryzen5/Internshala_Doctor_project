# Live Medical Transcription & Clinical Summary Backend

FastAPI backend providing real-time speech transcription (faster-whisper), LLM clinical summary extraction (Anthropic / OpenAI), and session storage.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Running
```bash
uvicorn app.main:app --reload --port 8000
```
