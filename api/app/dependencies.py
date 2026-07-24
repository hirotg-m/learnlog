from __future__ import annotations

import os

from fastapi import Cookie, Depends, HTTPException

from app.repositories.base import Store
from app.repositories.memory_store import MemoryStore
from app.services.auth_service import AuthService
from app.services.calendar_service import CalendarService
from app.services.milestone_service import MilestoneService
from app.services.qualification_service import QualificationService
from app.services.study_log_service import StudyLogService


def _create_store() -> Store:
    if os.getenv("STORE_BACKEND", "memory") == "dynamodb":
        from app.repositories.dynamodb_store import DynamoDBStore

        return DynamoDBStore()
    return MemoryStore()


store = _create_store()
auth_service = AuthService(store)
qualification_service = QualificationService(store)
study_log_service = StudyLogService(store)
milestone_service = MilestoneService(store)
calendar_service = CalendarService(store)


def get_auth_service() -> AuthService:
    return auth_service


def get_qualification_service() -> QualificationService:
    return qualification_service


def get_study_log_service() -> StudyLogService:
    return study_log_service


def get_milestone_service() -> MilestoneService:
    return milestone_service


def get_calendar_service() -> CalendarService:
    return calendar_service


def require_session(
    session_token: str | None = Cookie(default=None),
    service: AuthService = Depends(get_auth_service),
) -> str:
    if session_token is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return service.validate_session(session_token)
