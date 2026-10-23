# ==========================================
# Stage 1: Build Frontend (React + TS + Vite)
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Unified Backend & Runtime
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio decoding and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY backend/pyproject.toml ./backend/
WORKDIR /app/backend
RUN pip install --no-cache-dir -e "."

# Copy backend source code
COPY backend/ /app/backend/

# Copy built frontend assets into backend static folder
COPY --from=frontend-builder /app/frontend/dist /app/backend/static

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000 \
    FRONTEND_DIST=/app/backend/static \
    WHISPER_MODEL=small.en \
    WHISPER_DEVICE=cpu \
    WHISPER_COMPUTE_TYPE=int8 \
    LLM_PROVIDER=mock

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
