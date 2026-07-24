from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from app.dependencies import auth_service, store
from app.main import create_app


@pytest.fixture(autouse=True)
def reset_store() -> None:
    store.reset()


@pytest.fixture(autouse=True)
def setup_pin() -> None:
    os.environ["LEARNLOG_PIN"] = "12345678"
    os.environ["COOKIE_SECURE"] = "false"
    auth_service.pin = "12345678"


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def login(client: TestClient) -> None:
    response = client.post("/api/v1/auth/login", json={"pin": "12345678"})
    assert response.status_code == 200
