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
            "status": "open",
        },
    )
    qualification_id = qualification_response.json()["id"]

    first = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "午前問題を一周",
            "plannedDate": "2026-08-01",
        },
    )
    second = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "午後問題を一周",
            "plannedDate": "2026-08-15",
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
        "status": "open",
    }
    payload.update(overrides)
    return client.post("/api/v1/qualifications", json=payload).json()


def test_new_milestone_defaults_to_open(client: TestClient) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]

    milestone = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "午前問題を一周",
            "plannedDate": "2026-08-01",
        },
    ).json()

    assert milestone["status"] == "open"
    assert milestone["completedDate"] is None


def test_update_milestone_status_and_status_filter(client: TestClient) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]

    milestone = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "午前問題を一周",
            "plannedDate": "2026-08-01",
        },
    ).json()

    update_response = client.patch(
        f"/api/v1/milestones/{milestone['id']}", json={"status": "close"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "close"

    closed = client.get(
        "/api/v1/milestones",
        params={"qualificationId": qualification_id, "status": "close"},
    ).json()["items"]
    assert [item["id"] for item in closed] == [milestone["id"]]

    open_items = client.get(
        "/api/v1/milestones",
        params={"qualificationId": qualification_id, "status": "open"},
    ).json()["items"]
    assert open_items == []


def test_closing_milestone_without_completed_date_sets_it_to_today(
    client: TestClient,
) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]
    milestone = client.post(
        "/api/v1/milestones",
        json={"qualificationId": qualification_id, "title": "目標"},
    ).json()

    closed = client.patch(
        f"/api/v1/milestones/{milestone['id']}", json={"status": "close"}
    ).json()
    assert closed["completedDate"] is not None

    reopened = client.patch(
        f"/api/v1/milestones/{milestone['id']}", json={"status": "open"}
    ).json()
    assert reopened["completedDate"] is None


def test_closing_milestone_with_explicit_completed_date_keeps_it(
    client: TestClient,
) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]
    milestone = client.post(
        "/api/v1/milestones",
        json={"qualificationId": qualification_id, "title": "目標"},
    ).json()

    closed = client.patch(
        f"/api/v1/milestones/{milestone['id']}",
        json={"status": "close", "completedDate": "2026-01-01"},
    ).json()
    assert closed["completedDate"] == "2026-01-01"


def test_creating_milestone_with_completed_date_sets_status_close(
    client: TestClient,
) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]

    milestone = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "目標",
            "plannedDate": "2026-08-01",
            "completedDate": "2026-07-20",
        },
    ).json()

    assert milestone["status"] == "close"
    assert milestone["completedDate"] == "2026-07-20"


def test_editing_completed_date_without_status_sets_status_close(
    client: TestClient,
) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]
    milestone = client.post(
        "/api/v1/milestones",
        json={"qualificationId": qualification_id, "title": "目標"},
    ).json()
    assert milestone["status"] == "open"

    updated = client.patch(
        f"/api/v1/milestones/{milestone['id']}",
        json={"completedDate": "2026-07-20"},
    ).json()

    assert updated["status"] == "close"
    assert updated["completedDate"] == "2026-07-20"


def test_milestone_is_overdue_when_past_planned_date_and_open(
    client: TestClient,
) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]

    milestone = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "期限切れの目標",
            "plannedDate": "2020-01-01",
        },
    ).json()

    assert milestone["isOverdue"] is True


def test_closed_milestone_past_planned_date_is_not_overdue(
    client: TestClient,
) -> None:
    login(client)
    qualification_id = _create_qualification(client)["id"]

    milestone = client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "期限切れだが完了済みの目標",
            "plannedDate": "2020-01-01",
            "status": "close",
        },
    ).json()

    assert milestone["isOverdue"] is False


def test_update_milestone_not_found_returns_404(client: TestClient) -> None:
    login(client)
    response = client.patch(
        "/api/v1/milestones/does-not-exist", json={"status": "close"}
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
        },
    ).json()

    delete_response = client.delete(f"/api/v1/milestones/{milestone['id']}")
    assert delete_response.status_code == 204

    remaining = client.get(
        "/api/v1/milestones", params={"qualificationId": qualification_id}
    ).json()["items"]
    assert remaining == []
