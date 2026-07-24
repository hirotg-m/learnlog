from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from uuid import uuid4

from app.repositories.records import (
    LoginAttemptRecord,
    MilestoneRecord,
    QualificationRecord,
    StudyLogRecord,
)

__all__ = [
    "LoginAttemptRecord",
    "MemoryStore",
    "MilestoneRecord",
    "QualificationRecord",
    "StudyLogRecord",
]


class MemoryStore:
    """開発・単体テスト用のインメモリ実装。app.repositories.base.Store を満たす。"""

    def __init__(self) -> None:
        self._qualifications: dict[str, QualificationRecord] = {}
        self._study_logs: dict[str, StudyLogRecord] = {}
        self._milestones: dict[str, MilestoneRecord] = {}
        self._login_attempt = LoginAttemptRecord(fail_count=0, locked_until=None)
        self._sessions: dict[str, str] = {}

    def reset(self) -> None:
        """テスト間の状態リセット用。"""
        self._qualifications.clear()
        self._study_logs.clear()
        self._milestones.clear()
        self._login_attempt = LoginAttemptRecord(fail_count=0, locked_until=None)
        self._sessions.clear()

    # --- 資格 ---
    def get_qualification(self, qualification_id: str) -> QualificationRecord | None:
        return self._qualifications.get(qualification_id)

    def list_qualifications(
        self, *, status: str | None = None
    ) -> list[QualificationRecord]:
        records = list(self._qualifications.values())
        if status is not None:
            records = [item for item in records if item.status == status]
        return records

    def create_qualification(
        self,
        *,
        name: str,
        abbreviation: str | None,
        color: str,
        status: str,
        now: datetime,
    ) -> QualificationRecord:
        record = QualificationRecord(
            id=f"q_{uuid4().hex[:8]}",
            name=name,
            abbreviation=abbreviation,
            color=color,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self._qualifications[record.id] = record
        return record

    def update_qualification(
        self, record: QualificationRecord, *, now: datetime
    ) -> QualificationRecord:
        record.updated_at = now
        self._qualifications[record.id] = record
        return record

    def delete_qualification(self, qualification_id: str) -> None:
        self._qualifications.pop(qualification_id, None)
        self._study_logs = {
            key: value
            for key, value in self._study_logs.items()
            if value.qualification_id != qualification_id
        }
        self._milestones = {
            key: value
            for key, value in self._milestones.items()
            if value.qualification_id != qualification_id
        }

    # --- 学習記録 ---
    def get_study_log(self, study_log_id: str) -> StudyLogRecord | None:
        return self._study_logs.get(study_log_id)

    def list_study_logs(
        self,
        *,
        qualification_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[StudyLogRecord]:
        records = list(self._study_logs.values())
        if qualification_id is not None:
            records = [
                item for item in records if item.qualification_id == qualification_id
            ]
        if date_from is not None:
            records = [item for item in records if item.date >= date_from]
        if date_to is not None:
            records = [item for item in records if item.date <= date_to]
        return records

    def list_study_logs_by_date(self, target_date: str) -> list[StudyLogRecord]:
        return [item for item in self._study_logs.values() if item.date == target_date]

    def aggregate_calendar_month(
        self, year: int, month: int
    ) -> dict[str, dict[str, float]]:
        target_month = f"{year:04d}-{month:02d}"
        day_to_hours: dict[str, dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        for item in self._study_logs.values():
            if item.month != target_month:
                continue
            day_to_hours[item.date][item.qualification_id] += item.hours
        return day_to_hours

    def create_study_log(
        self,
        *,
        qualification_id: str,
        date: str,
        month: str,
        hours: float,
        content: str,
        memo: str | None,
        now: datetime,
    ) -> StudyLogRecord:
        record = StudyLogRecord(
            id=f"l_{uuid4().hex[:8]}",
            qualification_id=qualification_id,
            date=date,
            month=month,
            hours=hours,
            content=content,
            memo=memo,
            created_at=now,
            updated_at=now,
        )
        self._study_logs[record.id] = record
        return record

    def update_study_log(
        self, record: StudyLogRecord, *, now: datetime
    ) -> StudyLogRecord:
        record.updated_at = now
        self._study_logs[record.id] = record
        return record

    def delete_study_log(self, study_log_id: str) -> None:
        self._study_logs.pop(study_log_id, None)

    # --- マイルストーン ---
    def get_milestone(self, milestone_id: str) -> MilestoneRecord | None:
        return self._milestones.get(milestone_id)

    def list_milestones(
        self, *, qualification_id: str | None = None, status: str | None = None
    ) -> list[MilestoneRecord]:
        records = list(self._milestones.values())
        if qualification_id is not None:
            records = [
                item for item in records if item.qualification_id == qualification_id
            ]
        if status == "achieved":
            records = [item for item in records if item.is_achieved]
        elif status == "unachieved":
            records = [item for item in records if not item.is_achieved]
        return records

    def create_milestone(
        self,
        *,
        qualification_id: str,
        title: str,
        due_date: str | None,
        is_achieved: bool,
        now: datetime,
    ) -> MilestoneRecord:
        record = MilestoneRecord(
            id=f"m_{uuid4().hex[:8]}",
            qualification_id=qualification_id,
            title=title,
            due_date=due_date,
            is_achieved=is_achieved,
            created_at=now,
            updated_at=now,
        )
        self._milestones[record.id] = record
        return record

    def update_milestone(
        self, record: MilestoneRecord, *, now: datetime
    ) -> MilestoneRecord:
        record.updated_at = now
        self._milestones[record.id] = record
        return record

    def delete_milestone(self, milestone_id: str) -> None:
        self._milestones.pop(milestone_id, None)

    # --- ログイン失敗カウンタ ---
    def get_login_attempt(self) -> LoginAttemptRecord:
        return self._login_attempt

    def save_login_attempt(self, record: LoginAttemptRecord) -> None:
        self._login_attempt = record

    # --- セッション ---
    def get_session(self, token: str) -> str | None:
        return self._sessions.get(token)

    def save_session(self, token: str, expires_at: str) -> None:
        self._sessions[token] = expires_at

    def delete_session(self, token: str) -> None:
        self._sessions.pop(token, None)
