from __future__ import annotations

from fastapi.testclient import TestClient

from tests.unit.conftest import login


def test_multiple_milestones_per_qualification(client: TestClient) -> None:
    login(client)
    qualification_response = client.post(
        "/api/v1/qualifications",
        json={
            "name": "情報処理安全確保支援士",
            "abbreviation": "SC",
            "color": "red",
            "status": "active",
        },
    )
    qualification_id = qualification_response.json()["id"]

    first = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "午前問題を一周",
            "dueDate": "2026-08-01",
            "isAchieved": False,
        },
    )
    second = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "午後問題を一周",
            "dueDate": "2026-08-15",
            "isAchieved": False,
        },
    )
    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(
        "/api/v1/milestones", params={"qualificationId": qualification_id}
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


def _create_qualification(client: TestClient, **overrides: object) -> dict:
    payload = {
        "name": "情報処理安全確保支援士",
        "abbreviation": "SC",
        "color": "red",
        "status": "active",
    }
    payload.update(overrides)
    return client.post("/api/v1/qualifications", json=payload).json()


def test_update_milestone_achieved_and_status_filter(client: TestClient) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]

    milestone = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "午前問題を一周",
            "dueDate": "2026-08-01",
            "isAchieved": False,
        },
    ).json()

    update_response = client.patch(
        f"/api/v1/milestones/{milestone['id']}", json={"isAchieved": True}
    )
    assert update_response.status_code == 200
    assert update_response.json()["isAchieved"] is True

    achieved = client.get(
        "/api/v1/milestones",
        params={"qualificationId": qualification_id, "status": "achieved"},
    ).json()["items"]
    assert [item["id"] for item in achieved] == [milestone["id"]]

    unachieved = client.get(
        "/api/v1/milestones",
        params={"qualificationId": qualification_id, "status": "unachieved"},
    ).json()["items"]
    assert unachieved == []


def test_milestone_is_overdue_when_past_due_date_and_not_achieved(
    client: TestClient,
) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]

    milestone = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "期限切れの目標",
            "dueDate": "2020-01-01",
            "isAchieved": False,
        },
    ).json()

    assert milestone["isOverdue"] is True


def test_update_milestone_not_found_returns_404(client: TestClient) -> None:
    login(client)
    response = client.patch(
        "/api/v1/milestones/does-not-exist", json={"isAchieved": True}
    )
    assert response.status_code == 404


def test_delete_milestone(client: TestClient) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]
    milestone = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "削除対象",
            "dueDate": None,
            "isAchieved": False,
        },
    ).json()

    delete_response = client.delete(f"/api/v1/milestones/{milestone['id']}")
    assert delete_response.status_code == 204

    remaining = client.get(
        "/api/v1/milestones", params={"qualificationId": qualification_id}
    ).json()["items"]
    assert remaining == []
