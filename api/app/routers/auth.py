from __future__ import annotations

import os

from fastapi import APIRouter, Cookie, Depends, Response

from app.dependencies import get_auth_service, require_session
from app.models.auth import LoginRequest, LoginResponse, SessionInfo, SessionResponse
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, service: AuthService = Depends(get_auth_service)) -> LoginResponse:
    result = service.login(payload.pin)
    secure_cookie = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    response.set_cookie(
        key="session_token",
        value=result.token,
        max_age=result.max_age,
        httponly=True,
        secure=secure_cookie,
        samesite="none",
    )
    return LoginResponse(session=SessionInfo(expiresAt=result.expires_at))


@router.get("/session", response_model=SessionResponse)
def session_check(expires_at: str = Depends(require_session)) -> SessionResponse:
    return SessionResponse(authenticated=True, expiresAt=expires_at)


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    service: AuthService = Depends(get_auth_service),
    session_token: str | None = Cookie(default=None),
) -> Response:
    service.logout(session_token)
    response.delete_cookie("session_token")
    return response
