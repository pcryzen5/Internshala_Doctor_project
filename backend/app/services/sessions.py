"""Session service implementing consultation lifecycle logic."""

from uuid import UUID

from app.core.errors import NotFoundError
from app.db.models import Session
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.user_repo import UserRepository
from app.schemas.clinical_summary import ClinicalSummary
from app.schemas.session import (
    SegmentOut,
    SessionCreate,
    SessionListItem,
    SessionListOut,
    SessionOut,
    SessionUpdate,
    SummaryOut,
)


class SessionService:
    def __init__(
        self,
        session_repo: SessionRepository,
        user_repo: UserRepository,
    ) -> None:
        self.session_repo = session_repo
        self.user_repo = user_repo

    def _to_session_out(self, session: Session) -> SessionOut:
        latest_summary: SummaryOut | None = None
        if session.summaries:
            latest = session.summaries[0]
            latest_summary = SummaryOut(
                id=latest.id,
                version=latest.version,
                source=latest.source,
                model=latest.model,
                prompt_version=latest.prompt_version,
                data=ClinicalSummary.model_validate(latest.data),
                created_at=latest.created_at,
            )

        segments_out = [
            SegmentOut(
                id=seg.id,
                seq=seg.seq,
                text=seg.text,
                edited_text=seg.edited_text,
                start_ms=seg.start_ms,
                end_ms=seg.end_ms,
                confidence=seg.confidence,
                status=seg.status,
                created_at=seg.created_at,
            )
            for seg in sorted(session.segments, key=lambda s: s.seq)
        ]

        return SessionOut(
            id=session.id,
            user_id=session.user_id,
            status=session.status,
            language=session.language,
            patient_label=session.patient_label,
            duration_seconds=session.duration_seconds,
            started_at=session.started_at,
            ended_at=session.ended_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
            segments=segments_out,
            latest_summary=latest_summary,
        )

    async def create_session(self, payload: SessionCreate) -> SessionOut:
        user = await self.user_repo.get_or_create_dev_user()
        session = await self.session_repo.create_session(
            user_id=user.id,
            language=payload.language,
            patient_label=payload.patient_label,
        )
        loaded = await self.session_repo.get_by_id(session.id)
        assert loaded is not None
        return self._to_session_out(loaded)

    async def get_session(self, session_id: UUID) -> SessionOut:
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(f"Session with id {session_id} not found")
        return self._to_session_out(session)

    async def list_sessions(self, limit: int = 50, offset: int = 0) -> SessionListOut:
        sessions, total = await self.session_repo.list_sessions(limit=limit, offset=offset)
        items = [
            SessionListItem(
                id=s.id,
                status=s.status,
                language=s.language,
                patient_label=s.patient_label,
                duration_seconds=s.duration_seconds,
                created_at=s.created_at,
                updated_at=s.updated_at,
                segment_count=len(s.segments),
                has_summary=len(s.summaries) > 0,
            )
            for s in sessions
        ]
        return SessionListOut(items=items, total=total)

    async def update_session(self, session_id: UUID, payload: SessionUpdate) -> SessionOut:
        session = await self.session_repo.update_session(
            session_id=session_id,
            status=payload.status,
            patient_label=payload.patient_label,
        )
        if not session:
            raise NotFoundError(f"Session with id {session_id} not found")
        loaded = await self.session_repo.get_by_id(session_id)
        assert loaded is not None
        return self._to_session_out(loaded)

    async def delete_session(self, session_id: UUID) -> None:
        deleted = await self.session_repo.soft_delete(session_id)
        if not deleted:
            raise NotFoundError(f"Session with id {session_id} not found")

    async def clear_session(self, session_id: UUID) -> SessionOut:
        cleared = await self.session_repo.clear_session(session_id)
        if not cleared:
            raise NotFoundError(f"Session with id {session_id} not found")
        session = await self.session_repo.get_by_id(session_id)
        assert session is not None
        return self._to_session_out(session)
