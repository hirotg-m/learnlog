from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.dependencies import get_study_log_service, require_session
from app.models.study_log import StudyLogCreate, StudyLogListResponse, StudyLogOut, StudyLogUpdate
from app.services.study_log_service import StudyLogService


router = APIRouter(prefix="/study-logs", tags=["study-logs"], dependencies=[Depends(require_session)])


@router.get("", response_model=StudyLogListResponse)
def list_study_logs(
    qualificationId: str | None = Query(default=None),
    dateFrom: str | None = Query(default=None),
    dateTo: str | None = Query(default=None),
    sort: str = Query(default="date_desc"),
    service: StudyLogService = Depends(get_study_log_service),
) -> StudyLogListResponse:
    return StudyLogListResponse(
        items=service.list(
            qualification_id=qualificationId,
            date_from=dateFrom,
            date_to=dateTo,
            sort=sort,
        )
    )


@router.post("", response_model=StudyLogOut, status_code=201)
def create_study_log(payload: StudyLogCreate, service: StudyLogService = Depends(get_study_log_service)) -> StudyLogOut:
    return service.create(payload)


@router.get("/{study_log_id}", response_model=StudyLogOut)
def get_study_log(study_log_id: str, service: StudyLogService = Depends(get_study_log_service)) -> StudyLogOut:
    return service.get(study_log_id)


@router.patch("/{study_log_id}", response_model=StudyLogOut)
def update_study_log(
    study_log_id: str,
    payload: StudyLogUpdate,
    service: StudyLogService = Depends(get_study_log_service),
) -> StudyLogOut:
    return service.update(study_log_id, payload)


@router.delete("/{study_log_id}", status_code=204)
def delete_study_log(study_log_id: str, service: StudyLogService = Depends(get_study_log_service)) -> Response:
    service.delete(study_log_id)
    return Response(status_code=204)
