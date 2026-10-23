"""Clinical analysis and summary endpoints."""

import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_analysis_service, get_summary_repository
from app.db.repositories.summary_repo import SummaryRepository
from app.schemas.clinical_summary import ClinicalSummary
from app.schemas.session import SummaryOut
from app.services.analysis import AnalysisService

router = APIRouter(tags=["Analysis"])


class AnalyzeRequest(BaseModel):
    use_edited: bool = True
    language: str = "en"


@router.post("/sessions/{session_id}/analyze", response_model=SummaryOut)
async def analyze_session(
    session_id: UUID,
    payload: AnalyzeRequest,
    analysis_svc: AnalysisService = Depends(get_analysis_service),
) -> SummaryOut:
    """Invokes LLM extraction over session transcript to generate a ClinicalSummary."""
    return await analysis_svc.analyze(
        session_id=session_id,
        use_edited=payload.use_edited,
        language=payload.language,
    )


@router.get("/sessions/{session_id}/summaries", response_model=list[SummaryOut])
async def list_summary_versions(
    session_id: UUID,
    summary_repo: SummaryRepository = Depends(get_summary_repository),
) -> list[SummaryOut]:
    """Lists all historical versions of the clinical summary for a session."""
    summaries = await summary_repo.list_versions(session_id)
    return [
        SummaryOut(
            id=s.id,
            version=s.version,
            source=s.source,
            model=s.model,
            prompt_version=s.prompt_version,
            data=ClinicalSummary.model_validate(s.data),
            created_at=s.created_at,
        )
        for s in summaries
    ]


@router.put("/sessions/{session_id}/summary", response_model=SummaryOut)
async def update_summary(
    session_id: UUID,
    payload: ClinicalSummary,
    summary_repo: SummaryRepository = Depends(get_summary_repository),
) -> SummaryOut:
    """Clinician edits to summary create a new version with source='clinician_edit'."""
    data_dump = payload.model_dump()
    data_str = str(data_dump)
    tx_hash = hashlib.sha256(data_str.encode("utf-8")).hexdigest()

    record = await summary_repo.create_summary(
        session_id=session_id,
        data=data_dump,
        model="clinician-review",
        transcript_hash=tx_hash,
        prompt_version="v1",
        source="clinician_edit",
    )

    return SummaryOut(
        id=record.id,
        version=record.version,
        source=record.source,
        model=record.model,
        prompt_version=record.prompt_version,
        data=payload,
        created_at=record.created_at,
    )
