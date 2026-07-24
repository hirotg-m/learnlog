from __future__ import annotations

from pydantic import BaseModel


class CalendarDayItem(BaseModel):
    qualificationId: str
    qualificationName: str
    abbreviation: str | None
    color: str
    hours: float


class CalendarDay(BaseModel):
    date: str
    items: list[CalendarDayItem]


class CalendarMonthResponse(BaseModel):
    year: int
    month: int
    days: list[CalendarDay]


class CalendarDetailItem(BaseModel):
    studyLogId: str
    qualificationId: str
    qualificationName: str
    abbreviation: str | None
    color: str
    hours: float
    content: str
    memo: str | None
    createdAt: str


class CalendarDayResponse(BaseModel):
    date: str
    items: list[CalendarDetailItem]
