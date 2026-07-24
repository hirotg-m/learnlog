from __future__ import annotations

from fastapi import HTTPException

from app.models.study_log import StudyLogCreate, StudyLogOut, StudyLogUpdate
from app.repositories.base import Store
from app.repositories.records import StudyLogRecord
from app.utils.time import now_utc, to_iso_z
from app.utils.validation import parse_date


class StudyLogService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def list(
        self,
        *,
        qualification_id: str | None,
        date_from: str | None,
        date_to: str | None,
        sort: str,
    ) -> list[StudyLogOut]:
        if qualification_id is None and date_from is not None and date_to is not None:
            from_value = parse_date(date_from, field="dateFrom")
            to_value = parse_date(date_to, field="dateTo")
            months = (
                (to_value.year - from_value.year) * 12
                + to_value.month
                - from_value.month
            )
            if months > 12:
                raise HTTPException(
                    status_code=400, detail="date range must be within 12 months"
                )

        records = self.store.list_study_logs(
            qualification_id=qualification_id, date_from=date_from, date_to=date_to
        )

        is_desc = sort != "date_asc"
        records.sort(key=lambda item: (item.date, item.created_at), reverse=is_desc)
        return [self._to_out(item) for item in records]

    def create(self, payload: StudyLogCreate) -> StudyLogOut:
        qualification = self.store.get_qualification(payload.qualificationId)
        if qualification is None:
            raise HTTPException(status_code=404, detail="qualification not found")
        if qualification.status == "closed":
            raise HTTPException(
                status_code=400, detail="closed qualification cannot accept new logs"
            )

        parsed_date = parse_date(payload.date, field="date")
        record = self.store.create_study_log(
            qualification_id=payload.qualificationId,
            date=payload.date,
            month=f"{parsed_date.year:04d}-{parsed_date.month:02d}",
            hours=payload.hours,
            content=payload.content,
            memo=payload.memo,
            now=now_utc(),
        )
        return self._to_out(record)

    def get(self, study_log_id: str) -> StudyLogOut:
        record = self.store.get_study_log(study_log_id)
        if record is None:
            raise HTTPException(status_code=404, detail="study log not found")
        return self._to_out(record)

    def update(self, study_log_id: str, payload: StudyLogUpdate) -> StudyLogOut:
        record = self.store.get_study_log(study_log_id)
        if record is None:
            raise HTTPException(status_code=404, detail="study log not found")

        if payload.qualificationId is not None:
            qualification = self.store.get_qualification(payload.qualificationId)
            if qualification is None:
                raise HTTPException(status_code=404, detail="qualification not found")
            record.qualification_id = payload.qualificationId
        if payload.date is not None:
            parsed_date = parse_date(payload.date, field="date")
            record.date = payload.date
            record.month = f"{parsed_date.year:04d}-{parsed_date.month:02d}"
        if payload.hours is not None:
            record.hours = payload.hours
        if payload.content is not None:
            record.content = payload.content
        if payload.memo is not None:
            record.memo = payload.memo

        updated = self.store.update_study_log(record, now=now_utc())
        return self._to_out(updated)

    def delete(self, study_log_id: str) -> None:
        record = self.store.get_study_log(study_log_id)
        if record is None:
            raise HTTPException(status_code=404, detail="study log not found")
        self.store.delete_study_log(study_log_id)

    def _to_out(self, record: StudyLogRecord) -> StudyLogOut:
        return StudyLogOut(
            id=record.id,
            qualificationId=record.qualification_id,
            date=record.date,
            hours=record.hours,
            content=record.content,
            memo=record.memo,
            createdAt=to_iso_z(record.created_at),
            updatedAt=to_iso_z(record.updated_at),
        )
