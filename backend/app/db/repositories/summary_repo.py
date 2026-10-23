"""Summary repository for clinical summary storage and versioning."""

import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Summary


class SummaryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_next_version(self, session_id: uuid.UUID) -> int:
        stmt = (
            select(Summary.version)
            .where(Summary.session_id == session_id)
            .order_by(desc(Summary.version))
            .limit(1)
        )
        res = await self.db.execute(stmt)
        latest_version = res.scalar_one_or_none()
        return (latest_version or 0) + 1

    async def create_summary(
        self,
        session_id: uuid.UUID,
        data: dict[str, Any],
        model: str,
        transcript_hash: str,
        prompt_version: str = "v1",
        source: str = "llm",
    ) -> Summary:
        version = await self.get_next_version(session_id)
        summary = Summary(
            id=uuid.uuid4(),
            session_id=session_id,
            version=version,
            source=source,
            transcript_hash=transcript_hash,
            model=model,
            prompt_version=prompt_version,
            data=data,
        )
        self.db.add(summary)
        await self.db.flush()
        return summary

    async def get_latest(self, session_id: uuid.UUID) -> Summary | None:
        stmt = (
            select(Summary)
            .where(Summary.session_id == session_id)
            .order_by(desc(Summary.version))
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_versions(self, session_id: uuid.UUID) -> list[Summary]:
        stmt = (
            select(Summary).where(Summary.session_id == session_id).order_by(desc(Summary.version))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
