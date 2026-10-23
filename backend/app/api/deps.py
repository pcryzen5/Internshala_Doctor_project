"""FastAPI dependency providers."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.summary_repo import SummaryRepository
from app.db.repositories.transcript_repo import TranscriptRepository
from app.db.repositories.user_repo import UserRepository
from app.db.session import get_db
from app.services.asr import ASRService
from app.services.sessions import SessionService


def get_asr_service() -> ASRService:
    return ASRService.get_instance()


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_session_repository(db: AsyncSession = Depends(get_db)) -> SessionRepository:
    return SessionRepository(db)


def get_transcript_repository(db: AsyncSession = Depends(get_db)) -> TranscriptRepository:
    return TranscriptRepository(db)


def get_summary_repository(db: AsyncSession = Depends(get_db)) -> SummaryRepository:
    return SummaryRepository(db)


def get_session_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> SessionService:
    return SessionService(session_repo=session_repo, user_repo=user_repo)
