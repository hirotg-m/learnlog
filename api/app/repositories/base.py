from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.repositories.records import (
    LoginAttemptRecord,
    MilestoneRecord,
    QualificationRecord,
    StudyLogRecord,
)


class Store(Protocol):
    """MemoryStore と DynamoDBStore が共通で実装するリポジトリ インターフェース。"""

    # --- 資格 ---
    def get_qualification(
        self, qualification_id: str
    ) -> QualificationRecord | None: ...

    def list_qualifications(
        self, *, status: str | None = None
    ) -> list[QualificationRecord]: ...

    def create_qualification(
        self,
        *,
        name: str,
        abbreviation: str | None,
        color: str,
        status: str,
        now: datetime,
    ) -> QualificationRecord: ...

    def update_qualification(
        self, record: QualificationRecord, *, now: datetime
    ) -> QualificationRecord: ...

    def delete_qualification(self, qualification_id: str) -> None: ...

    # --- 学習記録 ---
    def get_study_log(self, study_log_id: str) -> StudyLogRecord | None: ...

    def list_study_logs(
        self,
        *,
        qualification_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[StudyLogRecord]: ...

    def list_study_logs_by_date(self, target_date: str) -> list[StudyLogRecord]: ...

    def aggregate_calendar_month(
        self, year: int, month: int
    ) -> dict[str, dict[str, float]]: ...

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
    ) -> StudyLogRecord: ...

    def update_study_log(
        self, record: StudyLogRecord, *, now: datetime
    ) -> StudyLogRecord: ...

    def delete_study_log(self, study_log_id: str) -> None: ...

    # --- マイルストーン ---
    def get_milestone(self, milestone_id: str) -> MilestoneRecord | None: ...

    def list_milestones(
        self, *, qualification_id: str | None = None, status: str | None = None
    ) -> list[MilestoneRecord]: ...

    def create_milestone(
        self,
        *,
        qualification_id: str,
        title: str,
        planned_date: str | None,
        completed_date: str | None,
        status: str,
        now: datetime,
    ) -> MilestoneRecord: ...

    def update_milestone(
        self, record: MilestoneRecord, *, now: datetime
    ) -> MilestoneRecord: ...

    def delete_milestone(self, milestone_id: str) -> None: ...

    # --- ログイン失敗カウンタ ---
    def get_login_attempt(self) -> LoginAttemptRecord: ...

    def save_login_attempt(self, record: LoginAttemptRecord) -> None: ...

    # --- セッション ---
    def get_session(self, token: str) -> str | None: ...

    def save_session(self, token: str, expires_at: str) -> None: ...

    def delete_session(self, token: str) -> None: ...
