from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    pin: str = Field(pattern=r"^\d{8}$")


class SessionInfo(BaseModel):
    expiresAt: str


class LoginResponse(BaseModel):
    session: SessionInfo


class SessionResponse(BaseModel):
    authenticated: bool
    expiresAt: str
