"""Main FastAPI application entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from fastapi import Depends, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_asr_service
from app.api.v1 import api_v1_router
from app.api.v1.transcribe import handle_audio_websocket
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging
from app.db.session import Base, engine
from app.services.asr import ASRService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """App lifespan context for resource startup and shutdown."""
    setup_logging(level=settings.LOG_LEVEL)

    # Automatically create tables in development / SQLite mode
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


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

    # Include API routers
    app.include_router(api_v1_router)

    @app.websocket("/ws/sessions/{session_id}/audio")
    async def audio_websocket(
        websocket: WebSocket,
        session_id: UUID,
        asr_svc: ASRService = Depends(get_asr_service),
    ) -> None:
        await handle_audio_websocket(websocket, session_id, asr_svc)

    @app.get("/health", tags=["System"])
    async def health() -> dict[str, Any]:
        """Health check endpoint required by API specification."""
        return {
            "status": "ok",
            "asr": "ready",
            "db": "ok",
        }

    # Serve built frontend static files if present (for single container deployment)
    import os
    from starlette.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    frontend_dist = os.getenv("FRONTEND_DIST") or os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "static")
    )
    if not os.path.exists(frontend_dist):
        dev_dist = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
        )
        if os.path.exists(dev_dist):
            frontend_dist = dev_dist

    if os.path.exists(frontend_dist) and os.path.isdir(frontend_dist):
        assets_dir = os.path.join(frontend_dist, "assets")
        if os.path.exists(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str) -> FileResponse:
            target = os.path.join(frontend_dist, full_path)
            if full_path and os.path.exists(target) and os.path.isfile(target):
                return FileResponse(target)
            return FileResponse(os.path.join(frontend_dist, "index.html"))

    return app


app = create_app()

