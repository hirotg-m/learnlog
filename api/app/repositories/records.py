from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class QualificationRecord:
    id: str
    name: str
    abbreviation: str | None
    color: str
    status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class StudyLogRecord:
    id: str
    qualification_id: str
    date: str
    month: str
    hours: float
    content: str
    memo: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class MilestoneRecord:
    id: str
    qualification_id: str
    title: str
    due_date: str | None
    is_achieved: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class LoginAttemptRecord:
    fail_count: int
    locked_until: datetime | None
