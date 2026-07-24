from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import boto3
import httpx
import pytest
from moto.server import ThreadedMotoServer

from tests.integration.conftest import (
    LOGIN_ATTEMPTS_TABLE,
    MILESTONES_TABLE,
    QUALIFICATIONS_TABLE,
    SESSIONS_TABLE,
    STUDY_LOGS_TABLE,
    _create_tables,
)

API_DIR = Path(__file__).resolve().parents[2]


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def moto_server_endpoint() -> Iterator[str]:
    """別プロセスからも接続できる、実際に HTTP で待ち受ける moto サーバーを起動する。"""
    server = ThreadedMotoServer(port=0, ip_address="127.0.0.1")
    server.start()
    _, port = server.get_host_and_port()
    endpoint_url = f"http://127.0.0.1:{port}"
    # moto サーバーはプロセス内でバックエンド状態を共有するため、テストごとにリセットする
    httpx.post(f"{endpoint_url}/moto-api/reset")
    yield endpoint_url
    server.stop()


@pytest.fixture
def live_api_base_url(moto_server_endpoint: str) -> Iterator[str]:
    """uvicorn でバックエンドを実際に起動し、DYNAMODB_ENDPOINT_URL 経由で moto サーバーに接続させる。"""
    resource = boto3.resource(
        "dynamodb",
        endpoint_url=moto_server_endpoint,
        region_name="ap-northeast-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
    )
    _create_tables(resource)

    port = _find_free_port()
    env = os.environ.copy()
    env.update(
        {
            "STORE_BACKEND": "dynamodb",
            "DYNAMODB_ENDPOINT_URL": moto_server_endpoint,
            "QUALIFICATIONS_TABLE": QUALIFICATIONS_TABLE,
            "STUDY_LOGS_TABLE": STUDY_LOGS_TABLE,
            "MILESTONES_TABLE": MILESTONES_TABLE,
            "LOGIN_ATTEMPTS_TABLE": LOGIN_ATTEMPTS_TABLE,
            "SESSIONS_TABLE": SESSIONS_TABLE,
            "LEARNLOG_PIN": "12345678",
            "COOKIE_SECURE": "false",
            "AWS_ACCESS_KEY_ID": "testing",
            "AWS_SECRET_ACCESS_KEY": "testing",
            "AWS_DEFAULT_REGION": "ap-northeast-1",
        }
    )

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port)],
        env=env,
        cwd=str(API_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    base_url = f"http://127.0.0.1:{port}"
    try:
        _wait_until_ready(base_url, process)
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def _wait_until_ready(
    base_url: str, process: subprocess.Popen[bytes], timeout: float = 10.0
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read().decode() if process.stdout else ""
            raise RuntimeError(f"uvicorn がすぐに終了しました:\n{output}")
        try:
            response = httpx.get(f"{base_url}/api/v1/auth/session", timeout=0.5)
            if response.status_code in (200, 401):
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    raise TimeoutError("uvicorn の起動待ちがタイムアウトしました")


def test_login_requires_session_cookie(live_api_base_url: str) -> None:
    with httpx.Client(base_url=live_api_base_url) as client:
        unauthorized = client.get("/api/v1/qualifications")
        assert unauthorized.status_code == 401

        login_response = client.post("/api/v1/auth/login", json={"pin": "12345678"})
        assert login_response.status_code == 200

        authorized = client.get("/api/v1/qualifications")
        assert authorized.status_code == 200


def test_full_qualification_and_study_log_flow(live_api_base_url: str) -> None:
    with httpx.Client(base_url=live_api_base_url) as client:
        client.post("/api/v1/auth/login", json={"pin": "12345678"})

        create_response = client.post(
            "/api/v1/qualifications",
            json={
                "name": "AWS SAP",
                "abbreviation": "SAP",
                "color": "blue",
                "status": "active",
            },
        )
        assert create_response.status_code == 201
        qualification_id = create_response.json()["id"]

        log_response = client.post(
            "/api/v1/study-logs",
            json={
                "qualificationId": qualification_id,
                "date": "2026-07-24",
                "hours": 1.5,
                "content": "IAM ポリシーを復習",
                "memo": None,
            },
        )
        assert log_response.status_code == 201

        calendar_response = client.get(
            "/api/v1/calendar/day", params={"date": "2026-07-24"}
        )
        assert calendar_response.status_code == 200
        assert (
            calendar_response.json()["items"][0]["qualificationId"] == qualification_id
        )
