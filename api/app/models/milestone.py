from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

MilestoneStatus = Literal["open", "close"]


class MilestoneBase(BaseModel):
    qualificationId: str
    title: str
    plannedDate: str | None = None
    completedDate: str | None = None
    status: MilestoneStatus = "open"


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneUpdate(BaseModel):
    qualificationId: str | None = None
    title: str | None = None
    plannedDate: str | None = None
    completedDate: str | None = None
    status: MilestoneStatus | None = None


class MilestoneOut(MilestoneBase):
    id: str
    isOverdue: bool
    createdAt: str
    updatedAt: str


class MilestoneListResponse(BaseModel):
    items: list[MilestoneOut]
