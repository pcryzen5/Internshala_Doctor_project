"""Sessions API router implementing consultation management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_session_service
from app.schemas.session import SessionCreate, SessionListOut, SessionOut, SessionUpdate
from app.services.sessions import SessionService

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    svc: SessionService = Depends(get_session_service),
) -> SessionOut:
    return await svc.create_session(payload)


@router.get("", response_model=SessionListOut)
async def list_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    svc: SessionService = Depends(get_session_service),
) -> SessionListOut:
    return await svc.list_sessions(limit=limit, offset=offset)


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: UUID,
    svc: SessionService = Depends(get_session_service),
) -> SessionOut:
    return await svc.get_session(session_id)


@router.patch("/{session_id}", response_model=SessionOut)
async def update_session(
    session_id: UUID,
    payload: SessionUpdate,
    svc: SessionService = Depends(get_session_service),
) -> SessionOut:
    return await svc.update_session(session_id, payload)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    svc: SessionService = Depends(get_session_service),
) -> None:
    await svc.delete_session(session_id)


@router.post("/{session_id}/clear", response_model=SessionOut)
async def clear_session(
    session_id: UUID,
    svc: SessionService = Depends(get_session_service),
) -> SessionOut:
    return await svc.clear_session(session_id)
