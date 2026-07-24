from __future__ import annotations

import hmac
import os
from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException

from app.repositories.base import Store
from app.utils.time import now_utc


@dataclass
class SessionResult:
    token: str
    expires_at: str
    max_age: int


class AuthService:
    def __init__(self, store: Store) -> None:
        self.store = store
        self.pin = os.getenv("LEARNLOG_PIN", "12345678")
        self.session_hours = 12
        self.lock_threshold = 5
        self.lock_minutes = 5

    def login(self, pin: str) -> SessionResult:
        now = now_utc()
        attempt = self.store.get_login_attempt()
        if attempt.locked_until is not None and attempt.locked_until > now:
            retry_after = int((attempt.locked_until - now).total_seconds())
            raise HTTPException(
                status_code=429,
                detail="login locked",
                headers={"Retry-After": str(retry_after)},
            )

        if not hmac.compare_digest(pin, self.pin):
            if attempt.locked_until is not None and attempt.locked_until <= now:
                attempt.fail_count = 0
                attempt.locked_until = None
            attempt.fail_count += 1
            if attempt.fail_count >= self.lock_threshold:
                attempt.locked_until = now + timedelta(minutes=self.lock_minutes)
                self.store.save_login_attempt(attempt)
                raise HTTPException(
                    status_code=429,
                    detail="login locked",
                    headers={"Retry-After": str(self.lock_minutes * 60)},
                )
            self.store.save_login_attempt(attempt)
            raise HTTPException(status_code=401, detail="invalid pin")

        attempt.fail_count = 0
        attempt.locked_until = None
        self.store.save_login_attempt(attempt)
        token = uuid4().hex
        expires = now + timedelta(hours=self.session_hours)
        expires_at = expires.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        self.store.save_session(token, expires_at)
        return SessionResult(
            token=token, expires_at=expires_at, max_age=self.session_hours * 3600
        )

    def validate_session(self, token: str | None) -> str:
        if token is None:
            raise HTTPException(status_code=401, detail="unauthorized")

        expires_at = self.store.get_session(token)
        if expires_at is None:
            raise HTTPException(status_code=401, detail="unauthorized")

        if expires_at <= now_utc().replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ):
            self.store.delete_session(token)
            raise HTTPException(status_code=401, detail="session expired")
        return expires_at

    def logout(self, token: str | None) -> None:
        if token is None:
            return
        self.store.delete_session(token)
