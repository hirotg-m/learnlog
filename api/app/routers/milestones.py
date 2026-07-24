from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.dependencies import get_milestone_service, require_session
from app.models.milestone import (
    MilestoneCreate,
    MilestoneListResponse,
    MilestoneOut,
    MilestoneUpdate,
)
from app.services.milestone_service import MilestoneService

router = APIRouter(
    prefix="/milestones", tags=["milestones"], dependencies=[Depends(require_session)]
)


@router.get("", response_model=MilestoneListResponse)
def list_milestones(
    qualificationId: str | None = Query(default=None),
    status: str | None = Query(default=None),
    service: MilestoneService = Depends(get_milestone_service),
) -> MilestoneListResponse:
    return MilestoneListResponse(
        items=service.list(qualification_id=qualificationId, status=status)
    )


@router.post("", response_model=MilestoneOut, status_code=201)
def create_milestone(
    payload: MilestoneCreate, service: MilestoneService = Depends(get_milestone_service)
) -> MilestoneOut:
    return service.create(payload)


@router.patch("/{milestone_id}", response_model=MilestoneOut)
def update_milestone(
    milestone_id: str,
    payload: MilestoneUpdate,
    service: MilestoneService = Depends(get_milestone_service),
) -> MilestoneOut:
    return service.update(milestone_id, payload)


@router.delete("/{milestone_id}", status_code=204)
def delete_milestone(
    milestone_id: str, service: MilestoneService = Depends(get_milestone_service)
) -> Response:
    service.delete(milestone_id)
    return Response(status_code=204)
