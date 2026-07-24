from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from app.repositories.dynamodb_store import DynamoDBStore
from tests.integration.conftest import (
    LOGIN_ATTEMPTS_TABLE,
    MILESTONES_TABLE,
    QUALIFICATIONS_TABLE,
    STUDY_LOGS_TABLE,
)

NOW = datetime(2026, 7, 24, 12, 0, tzinfo=UTC)


def _create_qualification(store: DynamoDBStore, *, name: str = "AWS SAP") -> str:
    record = store.create_qualification(
        name=name, abbreviation=None, color="blue", status="active", now=NOW
    )
    return record.id


def test_qualification_crud_roundtrip(dynamodb_store: DynamoDBStore) -> None:
    qualification_id = _create_qualification(dynamodb_store)

    fetched = dynamodb_store.get_qualification(qualification_id)
    assert fetched is not None
    assert fetched.name == "AWS SAP"

    fetched.name = "AWS SAP 更新"
    updated = dynamodb_store.update_qualification(fetched, now=NOW)
    assert updated.name == "AWS SAP 更新"

    listed = dynamodb_store.list_qualifications(status="active")
    assert [item.id for item in listed] == [qualification_id]

    dynamodb_store.delete_qualification(qualification_id)
    assert dynamodb_store.get_qualification(qualification_id) is None


def test_study_log_by_qualification_gsi_filters_by_date_range(
    dynamodb_store: DynamoDBStore,
) -> None:
    qualification_id = _create_qualification(dynamodb_store)
    other_id = _create_qualification(dynamodb_store, name="GitHub Copilot")

    dynamodb_store.create_study_log(
        qualification_id=qualification_id,
        date="2026-07-10",
        month="2026-07",
        hours=1.0,
        content="a",
        memo=None,
        now=NOW,
    )
    dynamodb_store.create_study_log(
        qualification_id=qualification_id,
        date="2026-07-24",
        month="2026-07",
        hours=1.5,
        content="b",
        memo=None,
        now=NOW,
    )
    dynamodb_store.create_study_log(
        qualification_id=other_id,
        date="2026-07-24",
        month="2026-07",
        hours=2.0,
        content="c",
        memo=None,
        now=NOW,
    )

    result = dynamodb_store.list_study_logs(
        qualification_id=qualification_id, date_from="2026-07-20", date_to="2026-07-31"
    )

    assert [item.content for item in result] == ["b"]


def test_calendar_month_aggregation_uses_by_month_gsi(
    dynamodb_store: DynamoDBStore,
) -> None:
    # 同日複数セッションの並び順は createdAt で決まる (docs/api-spec.md 10.2 参照) ため、
    # 意図的に異なる createdAt を与えて検証する
    qualification_id = _create_qualification(dynamodb_store)
    dynamodb_store.create_study_log(
        qualification_id=qualification_id,
        date="2026-07-24",
        month="2026-07",
        hours=1.0,
        content="a",
        memo=None,
        now=NOW,
    )
    dynamodb_store.create_study_log(
        qualification_id=qualification_id,
        date="2026-07-24",
        month="2026-07",
        hours=0.5,
        content="b",
        memo=None,
        now=NOW + timedelta(minutes=1),
    )
    dynamodb_store.create_study_log(
        qualification_id=qualification_id,
        date="2026-08-01",
        month="2026-08",
        hours=3.0,
        content="c",
        memo=None,
        now=NOW,
    )

    july = dynamodb_store.aggregate_calendar_month(2026, 7)
    assert july["2026-07-24"][qualification_id] == 1.5

    day_items = dynamodb_store.list_study_logs_by_date("2026-07-24")
    assert [item.content for item in day_items] == ["a", "b"]


def test_updating_date_without_recomputing_month_breaks_calendar_lookup(
    dynamodb_store: DynamoDBStore,
) -> None:
    """docs/api-spec.md 10.2 の注意点を検証する。

    date を更新する際に month を一緒に再計算し忘れると、レコードは
    ByMonth GSI 上で古い月(7月)のパーティションに残ったまま、date だけ 8 月になる。
    結果として 8 月のカレンダーには出てこず、7 月のカレンダーに存在しない日付(8/1)として紛れ込む。
    """
    qualification_id = _create_qualification(dynamodb_store)
    log = dynamodb_store.create_study_log(
        qualification_id=qualification_id,
        date="2026-07-24",
        month="2026-07",
        hours=1.0,
        content="7月の記録",
        memo=None,
        now=NOW,
    )

    # month を再計算せずに date だけ 8 月へ更新してしまうケース
    log.date = "2026-08-01"
    dynamodb_store.update_study_log(log, now=NOW)

    august = dynamodb_store.aggregate_calendar_month(2026, 8)
    assert august == {}, "month を更新し忘れたレコードは 8 月の集計には出てこない"

    july = dynamodb_store.aggregate_calendar_month(2026, 7)
    assert "2026-07-24" not in july, "元の日付にはもう存在しない"
    assert july["2026-08-01"][qualification_id] == 1.0, (
        "date は8月なのに7月の集計に紛れ込む"
    )


def test_milestone_by_qualification_gsi(dynamodb_store: DynamoDBStore) -> None:
    qualification_id = _create_qualification(dynamodb_store)
    other_id = _create_qualification(dynamodb_store, name="GitHub Actions")

    dynamodb_store.create_milestone(
        qualification_id=qualification_id,
        title="模試 80 点",
        due_date="2026-08-01",
        is_achieved=False,
        now=NOW,
    )
    dynamodb_store.create_milestone(
        qualification_id=other_id,
        title="別資格の目標",
        due_date=None,
        is_achieved=False,
        now=NOW,
    )

    result = dynamodb_store.list_milestones(qualification_id=qualification_id)
    assert [item.title for item in result] == ["模試 80 点"]


def _build_store(resource: Any) -> DynamoDBStore:
    return DynamoDBStore(
        qualifications_table=QUALIFICATIONS_TABLE,
        study_logs_table=STUDY_LOGS_TABLE,
        milestones_table=MILESTONES_TABLE,
        login_attempts_table=LOGIN_ATTEMPTS_TABLE,
        resource=resource,
    )


def test_login_attempt_persists_across_store_instances(dynamodb_resource: Any) -> None:
    first = _build_store(dynamodb_resource)
    attempt = first.get_login_attempt()
    attempt.fail_count = 3
    first.save_login_attempt(attempt)

    second = _build_store(dynamodb_resource)
    assert second.get_login_attempt().fail_count == 3
