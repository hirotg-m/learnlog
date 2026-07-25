from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

QualificationStatus = Literal["open", "close"]


class QualificationBase(BaseModel):
    name: str
    abbreviation: str | None = None
    color: str
    status: QualificationStatus = "open"


class QualificationCreate(QualificationBase):
    pass


class QualificationUpdate(BaseModel):
    name: str | None = None
    abbreviation: str | None = None
    color: str | None = None
    status: QualificationStatus | None = None


class QualificationOut(QualificationBase):
    id: str
    createdAt: str
    updatedAt: str
    totalHours: float | None = None
    studyLogCount: int | None = None
    lastStudiedAt: str | None = None


class QualificationListResponse(BaseModel):
    items: list[QualificationOut]
