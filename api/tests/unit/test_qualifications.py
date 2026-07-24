from __future__ import annotations

from fastapi.testclient import TestClient

from tests.unit.conftest import login


def _create_qualification(client: TestClient, **overrides: object) -> dict:
    payload = {
        "name": "AWS SAP",
        "abbreviation": "SAP",
        "color": "blue",
        "status": "active",
    }
    payload.update(overrides)
    response = client.post("/api/v1/qualifications", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_and_get_qualification(client: TestClient) -> None:
    login(client)
    created = _create_qualification(client)

    response = client.get(f"/api/v1/qualifications/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "AWS SAP"
    assert body["abbreviation"] == "SAP"
    assert body["color"] == "blue"
    assert body["status"] == "active"


def test_create_qualification_invalid_color_returns_422(client: TestClient) -> None:
    login(client)
    response = client.post(
        "/api/v1/qualifications",
        json={
            "name": "GitHub Copilot",
            "abbreviation": None,
            "color": "purple",
            "status": "active",
        },
    )
    assert response.status_code == 422


def test_create_qualification_invalid_status_returns_422(client: TestClient) -> None:
    login(client)
    response = client.post(
        "/api/v1/qualifications",
        json={
            "name": "GitHub Copilot",
            "abbreviation": None,
            "color": "blue",
            "status": "paused",
        },
    )
    assert response.status_code == 422


def test_list_filters_by_status(client: TestClient) -> None:
    login(client)
    _create_qualification(client, name="AWS SAP", status="active")
    _create_qualification(client, name="情報処理安全確保支援士", status="closed")

    response = client.get("/api/v1/qualifications", params={"status": "closed"})
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["name"] for item in items] == ["情報処理安全確保支援士"]


def test_list_include_stats(client: TestClient) -> None:
    login(client)
    qualification = _create_qualification(client)
    qualification_id = qualification["id"]

    client.post(
        "/api/v1/study-logs",
        json={
            "qualificationId": qualification_id,
            "date": "2026-07-24",
            "hours": 1.5,
            "content": "IAM ポリシーを復習",
            "memo": None,
        },
    )
    client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "模試 80 点",
            "dueDate": "2020-01-01",
            "isAchieved": False,
        },
    )

    without_stats = client.get("/api/v1/qualifications").json()["items"][0]
    assert without_stats["totalHours"] is None
    assert without_stats["studyLogCount"] is None
    assert without_stats["overdueMilestoneCount"] is None

    with_stats = client.get(
        "/api/v1/qualifications", params={"includeStats": True}
    ).json()["items"][0]
    assert with_stats["totalHours"] == 1.5
    assert with_stats["studyLogCount"] == 1
    assert with_stats["lastStudiedAt"] is not None
    assert with_stats["overdueMilestoneCount"] == 1


def test_update_qualification(client: TestClient) -> None:
    login(client)
    qualification = _create_qualification(client)

    response = client.patch(
        f"/api/v1/qualifications/{qualification['id']}",
        json={"name": "AWS SAP 更新", "color": "green", "status": "closed"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "AWS SAP 更新"
    assert body["color"] == "green"
    assert body["status"] == "closed"


def test_update_qualification_not_found_returns_404(client: TestClient) -> None:
    login(client)
    response = client.patch("/api/v1/qualifications/does-not-exist", json={"name": "x"})
    assert response.status_code == 404


def test_delete_qualification_cascades_study_logs_and_milestones(
    client: TestClient,
) -> None:
    login(client)
    qualification = _create_qualification(client)
    qualification_id = qualification["id"]

    log_response = client.post(
        "/api/v1/study-logs",
        json={
            "qualificationId": qualification_id,
            "date": "2026-07-24",
            "hours": 1.0,
            "content": "演習",
            "memo": None,
        },
    )
    study_log_id = log_response.json()["id"]

    client.post(
        "/api/v1/milestones",
        json={
            "qualificationId": qualification_id,
            "title": "目標",
            "dueDate": None,
            "isAchieved": False,
        },
    )

    delete_response = client.delete(f"/api/v1/qualifications/{qualification_id}")
    assert delete_response.status_code == 204

    assert client.get(f"/api/v1/qualifications/{qualification_id}").status_code == 404
    assert client.get(f"/api/v1/study-logs/{study_log_id}").status_code == 404
    assert (
        client.get(
            "/api/v1/milestones", params={"qualificationId": qualification_id}
        ).json()["items"]
        == []
    )


def test_closed_qualification_blocks_new_study_log(client: TestClient) -> None:
    login(client)
    qualification = _create_qualification(client, status="closed")

    response = client.post(
        "/api/v1/study-logs",
        json={
            "qualificationId": qualification["id"],
            "date": "2026-07-24",
            "hours": 1.0,
            "content": "演習",
            "memo": None,
        },
    )
    assert response.status_code == 400
