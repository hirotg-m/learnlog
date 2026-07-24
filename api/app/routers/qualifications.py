from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.dependencies import get_qualification_service, require_session
from app.models.qualification import (
    QualificationCreate,
    QualificationListResponse,
    QualificationOut,
    QualificationUpdate,
)
from app.services.qualification_service import QualificationService

router = APIRouter(
    prefix="/qualifications",
    tags=["qualifications"],
    dependencies=[Depends(require_session)],
)


@router.get("", response_model=QualificationListResponse)
def list_qualifications(
    status: str | None = Query(default=None),
    includeStats: bool = Query(default=False),
    service: QualificationService = Depends(get_qualification_service),
) -> QualificationListResponse:
    return QualificationListResponse(
        items=service.list(status=status, include_stats=includeStats)
    )


@router.post("", response_model=QualificationOut, status_code=201)
def create_qualification(
    payload: QualificationCreate,
    service: QualificationService = Depends(get_qualification_service),
) -> QualificationOut:
    return service.create(payload)


@router.get("/{qualification_id}", response_model=QualificationOut)
def get_qualification(
    qualification_id: str,
    includeStats: bool = Query(default=False),
    service: QualificationService = Depends(get_qualification_service),
) -> QualificationOut:
    return service.get(qualification_id, include_stats=includeStats)


@router.patch("/{qualification_id}", response_model=QualificationOut)
def update_qualification(
    qualification_id: str,
    payload: QualificationUpdate,
    service: QualificationService = Depends(get_qualification_service),
) -> QualificationOut:
    return service.update(qualification_id, payload)


@router.delete("/{qualification_id}", status_code=204)
def delete_qualification(
    qualification_id: str,
    service: QualificationService = Depends(get_qualification_service),
) -> Response:
    service.delete(qualification_id)
    return Response(status_code=204)
