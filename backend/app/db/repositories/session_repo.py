"""Session repository for consultation session CRUD and persistence."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Session


class SessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(
        self,
        user_id: uuid.UUID,
        language: str = "en",
        patient_label: str | None = None,
    ) -> Session:
        session = Session(
            id=uuid.uuid4(),
            user_id=user_id,
            status="ready",
            language=language,
            patient_label=patient_label,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_id(
        self, session_id: uuid.UUID, user_id: uuid.UUID | None = None
    ) -> Session | None:
        stmt = (
            select(Session)
            .where(Session.id == session_id, Session.deleted_at.is_(None))
            .options(
                selectinload(Session.segments),
                selectinload(Session.summaries),
            )
        )
        if user_id is not None:
            stmt = stmt.where(Session.user_id == user_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        user_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Session], int]:
        base_query = select(Session).where(Session.deleted_at.is_(None))
        if user_id is not None:
            base_query = base_query.where(Session.user_id == user_id)

        # Count total
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        # Query items with eager loading
        query = (
            base_query.options(
                selectinload(Session.segments),
                selectinload(Session.summaries),
            )
            .order_by(desc(Session.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        sessions = list(result.scalars().all())
        return sessions, total

    async def update_session(
        self,
        session_id: uuid.UUID,
        status: str | None = None,
        patient_label: str | None = None,
        duration_seconds: int | None = None,
        user_id: uuid.UUID | None = None,
    ) -> Session | None:
        session = await self.get_by_id(session_id, user_id=user_id)
        if not session:
            return None

        if status is not None:
            session.status = status
        if patient_label is not None:
            session.patient_label = patient_label
        if duration_seconds is not None:
            session.duration_seconds = duration_seconds

        await self.db.flush()
        return session

    async def soft_delete(self, session_id: uuid.UUID, user_id: uuid.UUID | None = None) -> bool:
        session = await self.get_by_id(session_id, user_id=user_id)
        if not session:
            return False
        session.deleted_at = datetime.now(UTC)
        await self.db.flush()
        return True

    async def clear_session(self, session_id: uuid.UUID, user_id: uuid.UUID | None = None) -> bool:
        session = await self.get_by_id(session_id, user_id=user_id)
        if not session:
            return False

        # Delete all segments and summaries for this session
        for segment in list(session.segments):
            await self.db.delete(segment)
        for summary in list(session.summaries):
            await self.db.delete(summary)

        session.status = "ready"
        session.duration_seconds = 0
        await self.db.flush()
        return True
