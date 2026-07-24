from __future__ import annotations

from app.models.calendar import (
    CalendarDay,
    CalendarDayItem,
    CalendarDayResponse,
    CalendarDetailItem,
    CalendarMonthResponse,
)
from app.repositories.base import Store
from app.utils.time import to_iso_z


class CalendarService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def month(self, *, year: int, month: int) -> CalendarMonthResponse:
        month_map = self.store.aggregate_calendar_month(year, month)
        days: list[CalendarDay] = []
        for day in sorted(month_map.keys()):
            items: list[CalendarDayItem] = []
            for qualification_id, hours in month_map[day].items():
                qualification = self.store.get_qualification(qualification_id)
                if qualification is None:
                    continue
                items.append(
                    CalendarDayItem(
                        qualificationId=qualification_id,
                        qualificationName=qualification.name,
                        abbreviation=qualification.abbreviation,
                        color=qualification.color,
                        hours=round(hours, 2),
                    )
                )
            days.append(CalendarDay(date=day, items=items))
        return CalendarMonthResponse(year=year, month=month, days=days)

    def day(self, *, target_date: str) -> CalendarDayResponse:
        logs = self.store.list_study_logs_by_date(target_date)
        logs.sort(key=lambda item: item.created_at)
        items: list[CalendarDetailItem] = []
        for log in logs:
            qualification = self.store.get_qualification(log.qualification_id)
            if qualification is None:
                continue
            items.append(
                CalendarDetailItem(
                    studyLogId=log.id,
                    qualificationId=log.qualification_id,
                    qualificationName=qualification.name,
                    abbreviation=qualification.abbreviation,
                    color=qualification.color,
                    hours=log.hours,
                    content=log.content,
                    memo=log.memo,
                    createdAt=to_iso_z(log.created_at),
                )
            )
        return CalendarDayResponse(date=target_date, items=items)
