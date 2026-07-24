from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_calendar_service, require_session
from app.models.calendar import CalendarDayResponse, CalendarMonthResponse
from app.services.calendar_service import CalendarService

router = APIRouter(
    prefix="/calendar", tags=["calendar"], dependencies=[Depends(require_session)]
)


@router.get("/month", response_model=CalendarMonthResponse)
def get_month(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    service: CalendarService = Depends(get_calendar_service),
) -> CalendarMonthResponse:
    return service.month(year=year, month=month)


@router.get("/day", response_model=CalendarDayResponse)
def get_day(
    date: str, service: CalendarService = Depends(get_calendar_service)
) -> CalendarDayResponse:
    return service.day(target_date=date)
