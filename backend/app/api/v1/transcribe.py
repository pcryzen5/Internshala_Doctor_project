"""Transcription REST and WebSocket endpoints."""

import json
import logging
import struct
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel

from app.api.deps import (
    get_asr_service,
    get_session_repository,
    get_transcript_repository,
)
from app.core.errors import ASRFailedError, NotFoundError, ValidationError
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.transcript_repo import TranscriptRepository
from app.db.session import AsyncSessionLocal
from app.schemas.session import SegmentEdit, SegmentOut
from app.services.asr import ASRService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Transcription"])


class TranscriptResponse(BaseModel):
    text: str
    segments: list[SegmentOut]


@router.post(
    "/sessions/{session_id}/segments",
    response_model=SegmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_audio_segment(
    session_id: UUID,
    seq: int = Form(...),
    audio: UploadFile = File(...),
    asr_svc: ASRService = Depends(get_asr_service),
    session_repo: SessionRepository = Depends(get_session_repository),
    transcript_repo: TranscriptRepository = Depends(get_transcript_repository),
) -> SegmentOut:
    """REST fallback for uploading an individual speech segment WAV."""
    session = await session_repo.get_by_id(session_id)
    if not session:
        raise NotFoundError(f"Session with id {session_id} not found")

    content = await audio.read()
    if not content:
        raise ValidationError("Audio file is empty")

    try:
        audio_np, sample_rate = ASRService.wav_bytes_to_np(content)
        result = await asr_svc.transcribe(audio_np, sample_rate=sample_rate)
    except Exception as exc:
        logger.error("ASR transcription error for session %s seq %d: %s", session_id, seq, str(exc))
        raise ASRFailedError(f"Failed to transcribe audio segment: {exc}") from exc

    seg = await transcript_repo.add_segment(
        session_id=session_id,
        seq=seq,
        text=result.text,
        start_ms=result.start_ms,
        end_ms=result.end_ms,
        confidence=result.confidence,
        status="done" if not result.is_hallucination else "done",
    )

    return SegmentOut(
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


@router.patch("/sessions/{session_id}/segments/{seq}", response_model=SegmentOut)
async def update_segment(
    session_id: UUID,
    seq: int,
    payload: SegmentEdit,
    transcript_repo: TranscriptRepository = Depends(get_transcript_repository),
) -> SegmentOut:
    """Edit transcript text for a specific segment."""
    seg = await transcript_repo.update_segment_text(session_id, seq, payload.edited_text)
    if not seg:
        raise NotFoundError(f"Segment seq {seq} not found for session {session_id}")

    return SegmentOut(
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


@router.get("/sessions/{session_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    session_id: UUID,
    session_repo: SessionRepository = Depends(get_session_repository),
    transcript_repo: TranscriptRepository = Depends(get_transcript_repository),
) -> TranscriptResponse:
    """Returns the ordered transcript and full combined text for a session."""
    session = await session_repo.get_by_id(session_id)
    if not session:
        raise NotFoundError(f"Session with id {session_id} not found")

    segments = await transcript_repo.list_segments(session_id)
    seg_outs = [
        SegmentOut(
            id=s.id,
            seq=s.seq,
            text=s.text,
            edited_text=s.edited_text,
            start_ms=s.start_ms,
            end_ms=s.end_ms,
            confidence=s.confidence,
            status=s.status,
            created_at=s.created_at,
        )
        for s in segments
    ]

    # Full text uses edited_text if present, else original text
    full_text = " ".join(
        s.edited_text if s.edited_text is not None else s.text for s in segments if s.text
    ).strip()
    return TranscriptResponse(text=full_text, segments=seg_outs)


async def handle_audio_websocket(
    websocket: WebSocket,
    session_id: UUID,
    asr_svc: ASRService,
) -> None:
    """Core WebSocket handler for audio streaming and transcription events."""
    await websocket.accept()
    logger.info("WebSocket connected for session: %s", session_id)

    # Validate session exists
    async with AsyncSessionLocal() as db:
        session_repo = SessionRepository(db)
        session = await session_repo.get_by_id(session_id)
        if not session:
            await websocket.send_json(
                {
                    "type": "transcript.error",
                    "seq": 0,
                    "code": "not_found",
                    "message": "Session not found",
                }
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                data: bytes = message["bytes"]

                # Check queue backpressure
                if asr_svc.active_tasks >= 4:
                    await websocket.send_json(
                        {"type": "session.busy", "queue_depth": asr_svc.active_tasks}
                    )

                # Parse binary frame: 4 bytes big endian header length + JSON header + PCM16 bytes
                if len(data) < 4:
                    continue

                header_len = struct.unpack(">I", data[:4])[0]
                if len(data) < 4 + header_len:
                    continue

                header_bytes = data[4 : 4 + header_len]
                pcm_bytes = data[4 + header_len :]

                try:
                    header = json.loads(header_bytes.decode("utf-8"))
                    seq = int(header.get("seq", 1))
                    sample_rate = int(header.get("sampleRate", 16000))
                except Exception:
                    seq = 1
                    sample_rate = 16000

                # Transcribe PCM16
                try:
                    audio_np = ASRService.pcm16_to_np(pcm_bytes)
                    result = await asr_svc.transcribe(audio_np, sample_rate=sample_rate)

                    # Persist segment to DB
                    async with AsyncSessionLocal() as db:
                        transcript_repo = TranscriptRepository(db)
                        await transcript_repo.add_segment(
                            session_id=session_id,
                            seq=seq,
                            text=result.text,
                            start_ms=result.start_ms,
                            end_ms=result.end_ms,
                            confidence=result.confidence,
                            status="done",
                        )
                        await db.commit()

                    # Push live segment event to client
                    await websocket.send_json(
                        {
                            "type": "transcript.segment",
                            "seq": seq,
                            "text": result.text,
                            "start_ms": result.start_ms,
                            "end_ms": result.end_ms,
                            "confidence": result.confidence,
                        }
                    )
                except Exception as exc:
                    logger.error("Error transcribing segment seq %d: %s", seq, str(exc))
                    await websocket.send_json(
                        {
                            "type": "transcript.error",
                            "seq": seq,
                            "code": "asr_failed",
                            "message": "Transcription failed for segment",
                        }
                    )

            elif "text" in message and message["text"]:
                try:
                    payload = json.loads(message["text"])
                    if payload.get("type") == "session.stop":
                        logger.info("Client requested session.stop for %s", session_id)
                        async with AsyncSessionLocal() as db:
                            session_repo = SessionRepository(db)
                            await session_repo.update_session(session_id, status="ready")
                            await db.commit()
                except json.JSONDecodeError:
                    pass

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for session: %s", session_id)
    except Exception as exc:
        logger.error("WebSocket unhandled exception for session %s: %s", session_id, str(exc))
