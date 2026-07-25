from __future__ import annotations

from fastapi.testclient import TestClient

from tests.unit.conftest import login


def test_study_log_hours_validation(client: TestClient) -> None:
    login(client)
    qualification_response = client.post(
        "/api/v1/qualifications",
        json={
            "name": "AWS SAP",
            "abbreviation": "SAP",
            "color": "blue",
            "status": "open",
        },
    )
    qualification_id = qualification_response.json()["id"]

    invalid_response = client.post(
        "/api/v1/study-logs",
        json={
            "qualificationId": qualification_id,
            "date": "2026-07-24",
            "hours": 1.1,
            "content": "invalid",
            "memo": None,
        },
    )
    assert invalid_response.status_code == 422


def test_study_logs_sort_by_date_and_created_at(client: TestClient) -> None:
    login(client)
    qualification_response = client.post(
        "/api/v1/qualifications",
        json={
            "name": "GitHub Actions",
            "abbreviation": "GHA",
            "color": "green",
            "status": "open",
        },
    )
    qualification_id = qualification_response.json()["id"]

    client.post(
        "/api/v1/study-logs",
        json={
            "qualificationId": qualification_id,
            "date": "2026-07-23",
            "hours": 1.0,
            "content": "a",
            "memo": None,
        },
    )
    client.post(
        "/api/v1/study-logs",
        json={
            "qualificationId": qualification_id,
            "date": "2026-07-24",
            "hours": 1.0,
            "content": "b",
            "memo": None,
        },
    )

    response = client.get("/api/v1/study-logs", params={"sort": "date_desc"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["date"] == "2026-07-24"


def _create_qualification(client: TestClient, **overrides: object) -> dict:
    payload = {
        "name": "AWS SAP",
        "abbreviation": "SAP",
        "color": "blue",
        "status": "open",
    }
    payload.update(overrides)
    return client.post("/api/v1/qualifications", json=payload).json()


def test_get_update_and_delete_study_log(client: TestClient) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]

    created = client.post(
        "/api/v1/study-logs",
        json={
            "qualificationId": qualification_id,
            "date": "2026-07-24",
            "hours": 1.0,
            "content": "演習",
            "memo": None,
        },
    ).json()

    get_response = client.get(f"/api/v1/study-logs/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["content"] == "演習"

    update_response = client.patch(
        f"/api/v1/study-logs/{created['id']}",
        json={"hours": 2.0, "content": "演習(更新)", "memo": "メモ追加"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["hours"] == 2.0
    assert updated["content"] == "演習(更新)"
    assert updated["memo"] == "メモ追加"

    delete_response = client.delete(f"/api/v1/study-logs/{created['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/study-logs/{created['id']}").status_code == 404


def test_update_study_log_not_found_returns_404(client: TestClient) -> None:
    login(client)
    response = client.patch("/api/v1/study-logs/does-not-exist", json={"hours": 1.0})
    assert response.status_code == 404


def test_update_study_log_date_moves_it_to_new_month_in_calendar(
    client: TestClient,
) -> None:
    """study_log_service.update() が date 変更時に month を正しく再計算していることを検証する。

    (docs/api-spec.md 10.2 で注意点として書いた「再計算し忘れるとカレンダーがずれる」の裏返し。
    tests/integration/test_dynamodb_store.py は「再計算し忘れた場合に壊れる」ことを示すテストで、
    実際のサービスが正しく再計算していることの検証はこちらが担う)
    """
    login(client)
    qualification_id = _create_qualification(client)["id"]

    created = client.post(
        "/api/v1/study-logs",
        json={
            "qualificationId": qualification_id,
            "date": "2026-07-24",
            "hours": 1.0,
            "content": "7月の記録",
            "memo": None,
        },
    ).json()

    update_response = client.patch(
        f"/api/v1/study-logs/{created['id']}", json={"date": "2026-08-01"}
    )
    assert update_response.status_code == 200

    july = client.get(
        "/api/v1/calendar/month", params={"year": 2026, "month": 7}
    ).json()
    assert july["days"] == []

    august = client.get(
        "/api/v1/calendar/month", params={"year": 2026, "month": 8}
    ).json()
    assert august["days"][0]["date"] == "2026-08-01"
    assert august["days"][0]["items"][0]["qualificationId"] == qualification_id
