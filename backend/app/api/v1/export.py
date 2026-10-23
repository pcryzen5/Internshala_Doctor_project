"""Export endpoints for formatted prescription text and JSON output."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.deps import get_session_repository, get_summary_repository
from app.core.errors import NotFoundError
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.summary_repo import SummaryRepository
from app.schemas.clinical_summary import ClinicalSummary

router = APIRouter(tags=["Export"])


def format_prescription_text(summary: ClinicalSummary, patient_label: str | None = None) -> str:
    """Formats clinical summary into the exact standard Copy to Prescription layout."""
    pat_name = summary.patient.name or patient_label or "Not recorded"
    pat_age = summary.patient.age or "Unknown age"
    pat_sex = summary.patient.sex or "Unknown sex"

    chief = summary.chief_complaint.text or "None stated"

    pos_syms = (
        ", ".join(s.name for s in summary.symptoms.positive)
        if summary.symptoms.positive
        else "None"
    )
    neg_syms = (
        ", ".join(s.name for s in summary.symptoms.negative)
        if summary.symptoms.negative
        else "None"
    )
    symptoms_line = f"+ {pos_syms} ; − {neg_syms}"

    impression = summary.assessment.provisional or "Under clinical evaluation"

    if summary.medications:
        meds_lines = [
            f"{m.name} {m.dose or ''} ({m.frequency or 'daily'})".strip()
            for m in summary.medications
        ]
        meds_text = "; ".join(meds_lines)
    else:
        meds_text = "No current medications recorded"

    if summary.allergies:
        allergies_text = "; ".join(
            f"{a.substance} ({a.reaction or 'reaction unknown'})" for a in summary.allergies
        )
    else:
        allergies_text = "No known allergies stated"

    plan_parts: list[str] = []
    if summary.plan.prescriptions:
        plan_parts.append(f"Rx: {', '.join(summary.plan.prescriptions)}")
    if summary.plan.investigations:
        plan_parts.append(f"Labs: {', '.join(summary.plan.investigations)}")
    if summary.plan.follow_up:
        plan_parts.append(f"Follow-up: {summary.plan.follow_up}")
    plan_text = " | ".join(plan_parts) if plan_parts else "Follow-up as needed"

    return (
        f"Patient: {pat_name}, {pat_age}/{pat_sex}\n"
        f"Chief complaint: {chief}\n"
        f"Symptoms: {symptoms_line}\n"
        f"Impression: {impression}\n"
        f"Medications: {meds_text}\n"
        f"Allergies: {allergies_text}\n"
        f"Plan / Follow-up: {plan_text}\n"
    )


@router.get("/sessions/{session_id}/export")
async def export_session(
    session_id: UUID,
    format: str = Query("text", pattern="^(text|json)$"),
    session_repo: SessionRepository = Depends(get_session_repository),
    summary_repo: SummaryRepository = Depends(get_summary_repository),
) -> Response:
    """Exports clinical summary as plain text (Copy to Prescription) or raw JSON."""
    session = await session_repo.get_by_id(session_id)
    if not session:
        raise NotFoundError(f"Session with id {session_id} not found")

    summary_record = await summary_repo.get_latest(session_id)
    if not summary_record:
        raise NotFoundError(f"No clinical summary available for session {session_id}")

    summary_obj = ClinicalSummary.model_validate(summary_record.data)

    if format == "json":
        return Response(
            content=summary_obj.model_dump_json(indent=2),
            media_type="application/json",
            status_code=status.HTTP_200_OK,
        )

    # Format text (Copy to Prescription)
    text_content = format_prescription_text(summary_obj, session.patient_label)
    return Response(
        content=text_content,
        media_type="text/plain; charset=utf-8",
        status_code=status.HTTP_200_OK,
    )
