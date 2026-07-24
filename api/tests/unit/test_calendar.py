from __future__ import annotations

from fastapi.testclient import TestClient

from tests.unit.conftest import login


def test_calendar_month_and_day(client: TestClient) -> None:
    login(client)
    qualification_response = client.post(
        "/api/v1/qualifications",
        json={
            "name": "GitHub Copilot",
            "abbreviation": "GH-300",
            "color": "teal",
            "status": "active",
        },
    )
    qualification_id = qualification_response.json()["id"]

    create_response = client.post(
        "/api/v1/study-logs",
        json={
            "qualificationId": qualification_id,
            "date": "2026-07-24",
            "hours": 1.5,
            "content": "演習",
            "memo": "メモ",
        },
    )
    assert create_response.status_code == 201

    month_response = client.get(
        "/api/v1/calendar/month", params={"year": 2026, "month": 7}
    )
    assert month_response.status_code == 200
    assert month_response.json()["days"][0]["date"] == "2026-07-24"

    day_response = client.get("/api/v1/calendar/day", params={"date": "2026-07-24"})
    assert day_response.status_code == 200
    assert day_response.json()["items"][0]["qualificationId"] == qualification_id
