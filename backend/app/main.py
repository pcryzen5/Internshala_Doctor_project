"""Main FastAPI application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """App lifespan context for resource startup and shutdown."""
    setup_logging(level=settings.LOG_LEVEL)
    yield


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="Live Medical Transcription & Clinical Summary API",
        version="0.1.0",
        description="Speech-to-text clinical transcription and structured summary extraction.",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register standardized error handlers
    register_error_handlers(app)

    @app.get("/health", tags=["System"])
    async def health() -> dict[str, Any]:
        """Health check endpoint required by API specification."""
        return {
            "status": "ok",
            "asr": "ready",
            "db": "ok",
        }

    return app


app = create_app()
