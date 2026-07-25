from __future__ import annotations

import os
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key

from app.repositories.records import (
    LoginAttemptRecord,
    MilestoneRecord,
    QualificationRecord,
    StudyLogRecord,
)
from app.utils.time import parse_iso, to_iso_z

LOGIN_ATTEMPT_ID = "singleton"


class DynamoDBStore:
    """boto3 (Table リソース) による DynamoDB 実装。app.repositories.base.Store を満たす。

    テーブル・GSI 設計は infra/dynamodb.yaml, docs/api-spec.md 10 章を参照。
    """

    def __init__(
        self,
        *,
        qualifications_table: str | None = None,
        study_logs_table: str | None = None,
        milestones_table: str | None = None,
        login_attempts_table: str | None = None,
        sessions_table: str | None = None,
        resource: Any = None,
    ) -> None:
        # DYNAMODB_ENDPOINT_URL はローカルの DynamoDB Local / moto サーバーへの向き先を
        # 差し替えるためのテスト用オプション。本番では未設定で AWS の実エンドポイントを使う
        self._resource = resource or boto3.resource(
            "dynamodb", endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL")
        )
        self._qualifications = self._resource.Table(
            qualifications_table
            or os.getenv("QUALIFICATIONS_TABLE", "learnlog-qualifications")
        )
        self._study_logs = self._resource.Table(
            study_logs_table or os.getenv("STUDY_LOGS_TABLE", "learnlog-study-logs")
        )
        self._milestones = self._resource.Table(
            milestones_table or os.getenv("MILESTONES_TABLE", "learnlog-milestones")
        )
        self._login_attempts = self._resource.Table(
            login_attempts_table
            or os.getenv("LOGIN_ATTEMPTS_TABLE", "learnlog-login-attempts")
        )
        self._sessions = self._resource.Table(
            sessions_table or os.getenv("SESSIONS_TABLE", "learnlog-sessions")
        )

    # --- 資格 ---
    def get_qualification(self, qualification_id: str) -> QualificationRecord | None:
        item = self._qualifications.get_item(Key={"id": qualification_id}).get("Item")
        return self._qualification_from_item(item) if item else None

    def list_qualifications(
        self, *, status: str | None = None
    ) -> list[QualificationRecord]:
        # 件数が少ない個人利用規模を前提に Scan を許容する (docs/api-spec.md 10.1 参照)
        items = self._qualifications.scan().get("Items", [])
        records = [self._qualification_from_item(item) for item in items]
        if status is not None:
            records = [record for record in records if record.status == status]
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
        self._qualifications.put_item(Item=self._qualification_to_item(record))
        return record

    def update_qualification(
        self, record: QualificationRecord, *, now: datetime
    ) -> QualificationRecord:
        record.updated_at = now
        self._qualifications.put_item(Item=self._qualification_to_item(record))
        return record

    def delete_qualification(self, qualification_id: str) -> None:
        self._qualifications.delete_item(Key={"id": qualification_id})
        for log in self.list_study_logs(qualification_id=qualification_id):
            self.delete_study_log(log.id)
        for milestone in self.list_milestones(qualification_id=qualification_id):
            self.delete_milestone(milestone.id)

    @staticmethod
    def _qualification_to_item(record: QualificationRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "name": record.name,
            "abbreviation": record.abbreviation,
            "color": record.color,
            "status": record.status,
            "createdAt": to_iso_z(record.created_at),
            "updatedAt": to_iso_z(record.updated_at),
        }

    @staticmethod
    def _qualification_from_item(item: dict[str, Any]) -> QualificationRecord:
        return QualificationRecord(
            id=item["id"],
            name=item["name"],
            abbreviation=item.get("abbreviation"),
            color=item["color"],
            status=item["status"],
            created_at=parse_iso(item["createdAt"]),
            updated_at=parse_iso(item["updatedAt"]),
        )

    # --- 学習記録 ---
    def get_study_log(self, study_log_id: str) -> StudyLogRecord | None:
        item = self._study_logs.get_item(Key={"id": study_log_id}).get("Item")
        return self._study_log_from_item(item) if item else None

    def list_study_logs(
        self,
        *,
        qualification_id: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[StudyLogRecord]:
        if qualification_id is not None:
            key_condition = Key("qualificationId").eq(qualification_id)
            if date_from is not None and date_to is not None:
                key_condition &= Key("date").between(date_from, date_to)
            elif date_from is not None:
                key_condition &= Key("date").gte(date_from)
            elif date_to is not None:
                key_condition &= Key("date").lte(date_to)
            items = self._query_all(
                "ByQualification", key_condition, table=self._study_logs
            )
            return [self._study_log_from_item(item) for item in items]

        if date_from is None or date_to is None:
            # 資格・期間のどちらも未指定: 件数が少ない個人利用規模を前提に Scan を許容する
            # (docs/api-spec.md 10.1 の qualifications と同じ方針)
            items = self._study_logs.scan().get("Items", [])
            records = [self._study_log_from_item(item) for item in items]
            if date_from is not None:
                records = [record for record in records if record.date >= date_from]
            if date_to is not None:
                records = [record for record in records if record.date <= date_to]
            return records

        # qualificationId 未指定・期間指定あり: ByMonth を月ごとに Query する (docs/api-spec.md 10.2 参照)
        items = self._query_by_month_range(date_from, date_to)
        records = [self._study_log_from_item(item) for item in items]
        records = [record for record in records if record.date >= date_from]
        records = [record for record in records if record.date <= date_to]
        return records

    def _query_by_month_range(
        self, date_from: str, date_to: str
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for month in self._months_between(date_from, date_to):
            items.extend(
                self._query_all(
                    "ByMonth", Key("month").eq(month), table=self._study_logs
                )
            )
        return items

    @staticmethod
    def _months_between(date_from: str, date_to: str) -> list[str]:
        start = date.fromisoformat(date_from).replace(day=1)
        end = date.fromisoformat(date_to)
        months: list[str] = []
        cursor = start
        while cursor <= end:
            months.append(f"{cursor.year:04d}-{cursor.month:02d}")
            if cursor.month == 12:
                cursor = cursor.replace(year=cursor.year + 1, month=1)
            else:
                cursor = cursor.replace(month=cursor.month + 1)
        return months

    def list_study_logs_by_date(self, target_date: str) -> list[StudyLogRecord]:
        month = target_date[:7]
        key_condition = Key("month").eq(month) & Key("date").eq(target_date)
        items = self._query_all("ByMonth", key_condition, table=self._study_logs)
        records = [self._study_log_from_item(item) for item in items]
        records.sort(key=lambda record: record.created_at)
        return records

    def aggregate_calendar_month(
        self, year: int, month: int
    ) -> dict[str, dict[str, float]]:
        target_month = f"{year:04d}-{month:02d}"
        items = self._query_all(
            "ByMonth", Key("month").eq(target_month), table=self._study_logs
        )
        day_to_hours: dict[str, dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        for item in items:
            day_to_hours[item["date"]][item["qualificationId"]] += float(item["hours"])
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
        self._study_logs.put_item(Item=self._study_log_to_item(record))
        return record

    def update_study_log(
        self, record: StudyLogRecord, *, now: datetime
    ) -> StudyLogRecord:
        record.updated_at = now
        self._study_logs.put_item(Item=self._study_log_to_item(record))
        return record

    def delete_study_log(self, study_log_id: str) -> None:
        self._study_logs.delete_item(Key={"id": study_log_id})

    @staticmethod
    def _study_log_to_item(record: StudyLogRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "qualificationId": record.qualification_id,
            "date": record.date,
            "month": record.month,
            "hours": Decimal(str(record.hours)),
            "content": record.content,
            "memo": record.memo,
            "createdAt": to_iso_z(record.created_at),
            "updatedAt": to_iso_z(record.updated_at),
        }

    @staticmethod
    def _study_log_from_item(item: dict[str, Any]) -> StudyLogRecord:
        return StudyLogRecord(
            id=item["id"],
            qualification_id=item["qualificationId"],
            date=item["date"],
            month=item["month"],
            hours=float(item["hours"]),
            content=item["content"],
            memo=item.get("memo"),
            created_at=parse_iso(item["createdAt"]),
            updated_at=parse_iso(item["updatedAt"]),
        )

    # --- マイルストーン ---
    def get_milestone(self, milestone_id: str) -> MilestoneRecord | None:
        item = self._milestones.get_item(Key={"id": milestone_id}).get("Item")
        return self._milestone_from_item(item) if item else None

    def list_milestones(
        self, *, qualification_id: str | None = None, status: str | None = None
    ) -> list[MilestoneRecord]:
        if qualification_id is not None:
            items = self._query_all(
                "ByQualification",
                Key("qualificationId").eq(qualification_id),
                table=self._milestones,
            )
        else:
            items = self._milestones.scan().get("Items", [])
        records = [self._milestone_from_item(item) for item in items]
        if status is not None:
            records = [record for record in records if record.status == status]
        return records

    def create_milestone(
        self,
        *,
        qualification_id: str,
        title: str,
        planned_date: str | None,
        completed_date: str | None,
        status: str,
        now: datetime,
    ) -> MilestoneRecord:
        record = MilestoneRecord(
            id=f"m_{uuid4().hex[:8]}",
            qualification_id=qualification_id,
            title=title,
            planned_date=planned_date,
            completed_date=completed_date,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self._milestones.put_item(Item=self._milestone_to_item(record))
        return record

    def update_milestone(
        self, record: MilestoneRecord, *, now: datetime
    ) -> MilestoneRecord:
        record.updated_at = now
        self._milestones.put_item(Item=self._milestone_to_item(record))
        return record

    def delete_milestone(self, milestone_id: str) -> None:
        self._milestones.delete_item(Key={"id": milestone_id})

    @staticmethod
    def _milestone_to_item(record: MilestoneRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "qualificationId": record.qualification_id,
            "title": record.title,
            "plannedDate": record.planned_date,
            "completedDate": record.completed_date,
            "status": record.status,
            "createdAt": to_iso_z(record.created_at),
            "updatedAt": to_iso_z(record.updated_at),
        }

    @staticmethod
    def _milestone_from_item(item: dict[str, Any]) -> MilestoneRecord:
        return MilestoneRecord(
            id=item["id"],
            qualification_id=item["qualificationId"],
            title=item["title"],
            planned_date=item.get("plannedDate"),
            completed_date=item.get("completedDate"),
            status=item.get("status", "open"),
            created_at=parse_iso(item["createdAt"]),
            updated_at=parse_iso(item["updatedAt"]),
        )

    # --- ログイン失敗カウンタ ---
    def get_login_attempt(self) -> LoginAttemptRecord:
        item = self._login_attempts.get_item(Key={"id": LOGIN_ATTEMPT_ID}).get("Item")
        if item is None:
            return LoginAttemptRecord(fail_count=0, locked_until=None)
        locked_until = (
            parse_iso(item["lockedUntil"]) if item.get("lockedUntil") else None
        )
        return LoginAttemptRecord(
            fail_count=int(item["failCount"]), locked_until=locked_until
        )

    def save_login_attempt(self, record: LoginAttemptRecord) -> None:
        item = {
            "id": LOGIN_ATTEMPT_ID,
            "failCount": record.fail_count,
            "lockedUntil": to_iso_z(record.locked_until)
            if record.locked_until
            else None,
        }
        self._login_attempts.put_item(Item=item)

    # --- セッション ---
    def get_session(self, token: str) -> str | None:
        item = self._sessions.get_item(Key={"token": token}).get("Item")
        return item["expiresAt"] if item else None

    def save_session(self, token: str, expires_at: str) -> None:
        # ttl は DynamoDB の TTL 属性 (infra/dynamodb.yaml 参照)。
        # アプリ側でも expiresAt を見て期限切れを判定するため、ttl はあくまで自動削除用の保険
        self._sessions.put_item(
            Item={
                "token": token,
                "expiresAt": expires_at,
                "ttl": int(parse_iso(expires_at).timestamp()),
            }
        )

    def delete_session(self, token: str) -> None:
        self._sessions.delete_item(Key={"token": token})

    # --- 内部ヘルパー ---
    @staticmethod
    def _query_all(
        index_name: str, key_condition: Any, *, table: Any
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        kwargs: dict[str, Any] = {
            "IndexName": index_name,
            "KeyConditionExpression": key_condition,
        }
        while True:
            response = table.query(**kwargs)
            items.extend(response.get("Items", []))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                return items
            kwargs["ExclusiveStartKey"] = last_key
