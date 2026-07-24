from __future__ import annotations

from pydantic import BaseModel, field_validator


def is_quarter_step(value: float) -> bool:
    scaled = round(value * 100)
    return scaled % 25 == 0


class StudyLogBase(BaseModel):
    qualificationId: str
    date: str
    hours: float
    content: str
    memo: str | None = None

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, value: float) -> float:
        if value <= 0 or not is_quarter_step(value):
            raise ValueError("hours must be in 0.25 increments")
        return value


class StudyLogCreate(StudyLogBase):
    pass


class StudyLogUpdate(BaseModel):
    qualificationId: str | None = None
    date: str | None = None
    hours: float | None = None
    content: str | None = None
    memo: str | None = None

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if value <= 0 or not is_quarter_step(value):
            raise ValueError("hours must be in 0.25 increments")
        return value


class StudyLogOut(StudyLogBase):
    id: str
    createdAt: str
    updatedAt: str


class StudyLogListResponse(BaseModel):
    items: list[StudyLogOut]
