"""Session and segment Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.clinical_summary import ClinicalSummary


class SessionCreate(BaseModel):
    language: str = "en"
    patient_label: str | None = None


class SessionUpdate(BaseModel):
    status: str | None = None
    patient_label: str | None = None


class SegmentOut(BaseModel):
    id: UUID
    seq: int
    text: str
    edited_text: str | None = None
    start_ms: int
    end_ms: int
    confidence: float | None = None
    status: str
    created_at: datetime


class SegmentEdit(BaseModel):
    edited_text: str


class SummaryOut(BaseModel):
    id: UUID
    version: int
    source: str
    model: str
    prompt_version: str
    data: ClinicalSummary
    created_at: datetime


class SessionOut(BaseModel):
    id: UUID
    user_id: UUID
    status: str
    language: str
    patient_label: str | None = None
    duration_seconds: int | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    segments: list[SegmentOut] = Field(default_factory=list)
    latest_summary: SummaryOut | None = None


class SessionListItem(BaseModel):
    id: UUID
    status: str
    language: str
    patient_label: str | None = None
    duration_seconds: int | None = None
    created_at: datetime
    updated_at: datetime
    segment_count: int = 0
    has_summary: bool = False


class SessionListOut(BaseModel):
    items: list[SessionListItem]
    total: int
