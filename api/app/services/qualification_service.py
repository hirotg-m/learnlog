from __future__ import annotations

from fastapi import HTTPException

from app.models.qualification import (
    QualificationCreate,
    QualificationOut,
    QualificationUpdate,
)
from app.repositories.base import Store
from app.repositories.records import QualificationRecord
from app.utils.time import now_utc, to_iso_z, today_in_app_timezone

COLOR_PALETTE = {
    "red",
    "orange",
    "yellow",
    "green",
    "teal",
    "blue",
    "indigo",
    "pink",
    "brown",
    "gray",
}


class QualificationService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def list(
        self, *, status: str | None, include_stats: bool
    ) -> list[QualificationOut]:
        records = self.store.list_qualifications(status=status)
        result = [self._to_out(item, include_stats=include_stats) for item in records]
        result.sort(key=lambda item: item.createdAt)
        return result

    def create(self, payload: QualificationCreate) -> QualificationOut:
        self._validate_color(payload.color)
        if payload.status not in {"active", "closed"}:
            raise HTTPException(status_code=422, detail="invalid status")
        record = self.store.create_qualification(
            name=payload.name,
            abbreviation=payload.abbreviation,
            color=payload.color,
            status=payload.status,
            now=now_utc(),
        )
        return self._to_out(record, include_stats=False)

    def get(
        self, qualification_id: str, *, include_stats: bool = False
    ) -> QualificationOut:
        record = self.store.get_qualification(qualification_id)
        if record is None:
            raise HTTPException(status_code=404, detail="qualification not found")
        return self._to_out(record, include_stats=include_stats)

    def update(
        self, qualification_id: str, payload: QualificationUpdate
    ) -> QualificationOut:
        record = self.store.get_qualification(qualification_id)
        if record is None:
            raise HTTPException(status_code=404, detail="qualification not found")

        if payload.name is not None:
            record.name = payload.name
        if payload.abbreviation is not None:
            record.abbreviation = payload.abbreviation
        if payload.color is not None:
            self._validate_color(payload.color)
            record.color = payload.color
        if payload.status is not None:
            record.status = payload.status

        updated = self.store.update_qualification(record, now=now_utc())
        return self._to_out(updated, include_stats=False)

    def delete(self, qualification_id: str) -> None:
        record = self.store.get_qualification(qualification_id)
        if record is None:
            raise HTTPException(status_code=404, detail="qualification not found")
        self.store.delete_qualification(qualification_id)

    def _validate_color(self, color: str) -> None:
        if color not in COLOR_PALETTE:
            raise HTTPException(status_code=422, detail="invalid color")

    def _to_out(
        self, record: QualificationRecord, *, include_stats: bool
    ) -> QualificationOut:
        total_hours: float | None = None
        study_log_count: int | None = None
        last_studied_at: str | None = None
        overdue_count: int | None = None
        if include_stats:
            target_logs = self.store.list_study_logs(qualification_id=record.id)
            total_hours = round(sum(item.hours for item in target_logs), 2)
            study_log_count = len(target_logs)
            if target_logs:
                last_studied_at = to_iso_z(max(item.created_at for item in target_logs))
            today = today_in_app_timezone().isoformat()
            overdue_count = len(
                [
                    item
                    for item in self.store.list_milestones(qualification_id=record.id)
                    if item.due_date is not None
                    and item.due_date < today
                    and not item.is_achieved
                ]
            )

        return QualificationOut(
            id=record.id,
            name=record.name,
            abbreviation=record.abbreviation,
            color=record.color,
            status=record.status,
            createdAt=to_iso_z(record.created_at),
            updatedAt=to_iso_z(record.updated_at),
            totalHours=total_hours,
            studyLogCount=study_log_count,
            lastStudiedAt=last_studied_at,
            overdueMilestoneCount=overdue_count,
        )
