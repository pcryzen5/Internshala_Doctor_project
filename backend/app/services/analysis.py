"""Clinical analysis service: prompt assembly, LLM execution, schema validation, and retry."""

import hashlib
import logging
from pathlib import Path
from uuid import UUID

from pydantic import ValidationError as PydanticValError

from app.core.errors import LLMFailedError, NotFoundError, ValidationError
from app.db.models import Summary
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.summary_repo import SummaryRepository
from app.db.repositories.transcript_repo import TranscriptRepository
from app.schemas.clinical_summary import ClinicalSummary
from app.schemas.session import SummaryOut
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "clinical_extraction_v1.md"


class AnalysisService:
    def __init__(
        self,
        session_repo: SessionRepository,
        transcript_repo: TranscriptRepository,
        summary_repo: SummaryRepository,
        llm_provider: LLMProvider,
    ) -> None:
        self.session_repo = session_repo
        self.transcript_repo = transcript_repo
        self.summary_repo = summary_repo
        self.llm_provider = llm_provider

    def _load_prompt_template(self) -> str:
        if PROMPT_FILE.exists():
            return PROMPT_FILE.read_text(encoding="utf-8")
        return (
            "You are an expert clinical documentation assistant. "
            "Extract structured medical summary data from the transcript."
        )

    async def analyze(
        self,
        session_id: UUID,
        use_edited: bool = True,
        language: str = "en",
    ) -> SummaryOut:
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(f"Session with id {session_id} not found")

        # Fetch transcript segments
        segments = await self.transcript_repo.list_segments(session_id)
        if not segments:
            raise ValidationError("Cannot analyze an empty transcript with no segments")

        # Assemble full text
        if use_edited:
            parts = [s.edited_text if s.edited_text is not None else s.text for s in segments]
        else:
            parts = [s.text for s in segments]

        full_transcript = " ".join(t.strip() for t in parts if t.strip()).strip()
        if not full_transcript:
            raise ValidationError("Transcript text is empty")

        # Compute SHA256 hash of transcript
        transcript_hash = hashlib.sha256(full_transcript.encode("utf-8")).hexdigest()

        # Update session status to analyzing
        await self.session_repo.update_session(session_id, status="analyzing")

        system_prompt = self._load_prompt_template()

        # Validation loop: up to 2 retries with feedback on Pydantic errors
        max_attempts = 3
        validated_summary: ClinicalSummary | None = None
        last_error: str | None = None

        for attempt in range(max_attempts):
            try:
                raw_data = await self.llm_provider.extract_clinical_summary(
                    transcript=full_transcript,
                    system_prompt=system_prompt,
                    error_feedback=last_error,
                )

                # Validate with Pydantic v2
                validated_summary = ClinicalSummary.model_validate(raw_data)
                break

            except PydanticValError as val_err:
                last_error = str(val_err)
                logger.warning(
                    "ClinicalSummary validation failed on attempt %d for session %s: %s",
                    attempt + 1,
                    session_id,
                    last_error,
                )
                if attempt == max_attempts - 1:
                    await self.session_repo.update_session(session_id, status="failed")
                    raise LLMFailedError(
                        f"LLM output failed ClinicalSummary schema validation after "
                        f"{max_attempts} attempts: {last_error}"
                    ) from val_err

            except Exception as exc:
                logger.error("LLM extraction failed on attempt %d: %s", attempt + 1, str(exc))
                if attempt == max_attempts - 1:
                    await self.session_repo.update_session(session_id, status="failed")
                    raise LLMFailedError(f"LLM extraction service failed: {exc}") from exc

        assert validated_summary is not None

        # Persist summary version to repository
        summary_record: Summary = await self.summary_repo.create_summary(
            session_id=session_id,
            data=validated_summary.model_dump(),
            model=self.llm_provider.model_name,
            transcript_hash=transcript_hash,
            prompt_version="v1",
            source="llm",
        )

        # Update session status to reviewed
        await self.session_repo.update_session(session_id, status="reviewed")

        return SummaryOut(
            id=summary_record.id,
            version=summary_record.version,
            source=summary_record.source,
            model=summary_record.model,
            prompt_version=summary_record.prompt_version,
            data=validated_summary,
            created_at=summary_record.created_at,
        )
