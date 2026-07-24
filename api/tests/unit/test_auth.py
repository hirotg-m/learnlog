from __future__ import annotations

from fastapi.testclient import TestClient


def test_login_and_session(client: TestClient) -> None:
    login_response = client.post("/api/v1/auth/login", json={"pin": "12345678"})
    assert login_response.status_code == 200
    assert "session" in login_response.json()

    session_response = client.get("/api/v1/auth/session")
    assert session_response.status_code == 200
    assert session_response.json()["authenticated"] is True


def test_login_lock_after_five_failures(client: TestClient) -> None:
    for _ in range(4):
        response = client.post("/api/v1/auth/login", json={"pin": "99999999"})
        assert response.status_code == 401

    response = client.post("/api/v1/auth/login", json={"pin": "99999999"})
    assert response.status_code == 429
    assert response.headers.get("Retry-After") is not None
