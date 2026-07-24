from __future__ import annotations

from pydantic import BaseModel


class MilestoneBase(BaseModel):
    qualificationId: str
    title: str
    dueDate: str | None = None
    isAchieved: bool = False


class MilestoneCreate(MilestoneBase):
    pass


class MilestoneUpdate(BaseModel):
    qualificationId: str | None = None
    title: str | None = None
    dueDate: str | None = None
    isAchieved: bool | None = None


class MilestoneOut(MilestoneBase):
    id: str
    isOverdue: bool
    createdAt: str
    updatedAt: str


class MilestoneListResponse(BaseModel):
    items: list[MilestoneOut]
