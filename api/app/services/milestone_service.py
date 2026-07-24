from __future__ import annotations

from fastapi import HTTPException

from app.models.milestone import MilestoneCreate, MilestoneOut, MilestoneUpdate
from app.repositories.base import Store
from app.repositories.records import MilestoneRecord
from app.utils.time import now_utc, to_iso_z, today_in_app_timezone
from app.utils.validation import parse_date


class MilestoneService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def list(
        self, *, qualification_id: str | None, status: str | None
    ) -> list[MilestoneOut]:
        records = self.store.list_milestones(
            qualification_id=qualification_id, status=status
        )
        records.sort(key=lambda item: item.created_at)
        return [self._to_out(item) for item in records]

    def create(self, payload: MilestoneCreate) -> MilestoneOut:
        if self.store.get_qualification(payload.qualificationId) is None:
            raise HTTPException(status_code=404, detail="qualification not found")
        if payload.dueDate is not None:
            parse_date(payload.dueDate, field="dueDate")

        record = self.store.create_milestone(
            qualification_id=payload.qualificationId,
            title=payload.title,
            due_date=payload.dueDate,
            is_achieved=payload.isAchieved,
            now=now_utc(),
        )
        return self._to_out(record)

    def update(self, milestone_id: str, payload: MilestoneUpdate) -> MilestoneOut:
        record = self.store.get_milestone(milestone_id)
        if record is None:
            raise HTTPException(status_code=404, detail="milestone not found")

        if payload.qualificationId is not None:
            if self.store.get_qualification(payload.qualificationId) is None:
                raise HTTPException(status_code=404, detail="qualification not found")
            record.qualification_id = payload.qualificationId
        if payload.title is not None:
            record.title = payload.title
        if payload.dueDate is not None:
            parse_date(payload.dueDate, field="dueDate")
            record.due_date = payload.dueDate
        if payload.isAchieved is not None:
            record.is_achieved = payload.isAchieved

        updated = self.store.update_milestone(record, now=now_utc())
        return self._to_out(updated)

    def delete(self, milestone_id: str) -> None:
        record = self.store.get_milestone(milestone_id)
        if record is None:
            raise HTTPException(status_code=404, detail="milestone not found")
        self.store.delete_milestone(milestone_id)

    def _to_out(self, record: MilestoneRecord) -> MilestoneOut:
        today = today_in_app_timezone().isoformat()
        return MilestoneOut(
            id=record.id,
            qualificationId=record.qualification_id,
            title=record.title,
            dueDate=record.due_date,
            isAchieved=record.is_achieved,
            isOverdue=(
                record.due_date is not None
                and record.due_date < today
                and not record.is_achieved
            ),
            createdAt=to_iso_z(record.created_at),
            updatedAt=to_iso_z(record.updated_at),
        )
