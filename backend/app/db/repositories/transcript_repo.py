"""Transcript segments repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TranscriptSegment


class TranscriptRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add_segment(
        self,
        session_id: uuid.UUID,
        seq: int,
        text: str,
        start_ms: int = 0,
        end_ms: int = 0,
        confidence: float | None = None,
        status: str = "done",
    ) -> TranscriptSegment:
        # Check if already exists for idempotency/reconnects
        existing = await self.get_by_seq(session_id, seq)
        if existing:
            existing.text = text
            existing.start_ms = start_ms
            existing.end_ms = end_ms
            existing.confidence = confidence
            existing.status = status
            await self.db.flush()
            return existing

        segment = TranscriptSegment(
            id=uuid.uuid4(),
            session_id=session_id,
            seq=seq,
            text=text,
            start_ms=start_ms,
            end_ms=end_ms,
            confidence=confidence,
            status=status,
        )
        self.db.add(segment)
        await self.db.flush()
        return segment

    async def get_by_seq(self, session_id: uuid.UUID, seq: int) -> TranscriptSegment | None:
        stmt = select(TranscriptSegment).where(
            TranscriptSegment.session_id == session_id,
            TranscriptSegment.seq == seq,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_segments(self, session_id: uuid.UUID) -> list[TranscriptSegment]:
        stmt = (
            select(TranscriptSegment)
            .where(TranscriptSegment.session_id == session_id)
            .order_by(TranscriptSegment.seq.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_segment_text(
        self, session_id: uuid.UUID, seq: int, edited_text: str
    ) -> TranscriptSegment | None:
        segment = await self.get_by_seq(session_id, seq)
        if not segment:
            return None
        segment.edited_text = edited_text
        await self.db.flush()
        return segment
