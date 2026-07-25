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
        if payload.plannedDate is not None:
            parse_date(payload.plannedDate, field="plannedDate")
        if payload.completedDate is not None:
            parse_date(payload.completedDate, field="completedDate")

        status = payload.status
        completed_date = payload.completedDate
        if completed_date is not None:
            # 完了日が入力されている場合は状態を close にする
            status = "close"
        elif status == "close":
            completed_date = today_in_app_timezone().isoformat()

        record = self.store.create_milestone(
            qualification_id=payload.qualificationId,
            title=payload.title,
            planned_date=payload.plannedDate,
            completed_date=completed_date,
            status=status,
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
        if payload.plannedDate is not None:
            parse_date(payload.plannedDate, field="plannedDate")
            record.planned_date = payload.plannedDate
        if payload.completedDate is not None:
            parse_date(payload.completedDate, field="completedDate")
            record.completed_date = payload.completedDate
            # 完了日が入力され、状態が明示指定されていない場合は close にする
            if payload.status is None:
                record.status = "close"
        if payload.status is not None:
            record.status = payload.status
            # 完了日を明示指定していない場合、close への変更で完了日を今日に自動設定し、
            # open への変更で完了日をクリアする
            if payload.completedDate is None:
                record.completed_date = (
                    today_in_app_timezone().isoformat()
                    if payload.status == "close"
                    else None
                )

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
            plannedDate=record.planned_date,
            completedDate=record.completed_date,
            status=record.status,
            isOverdue=(
                record.status == "open"
                and record.planned_date is not None
                and record.planned_date < today
            ),
            createdAt=to_iso_z(record.created_at),
            updatedAt=to_iso_z(record.updated_at),
        )
