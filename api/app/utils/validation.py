from __future__ import annotations

from datetime import date

from fastapi import HTTPException


def parse_date(value: str, *, field: str) -> date:
    """ISO 8601 の日付文字列を検証しつつ date に変換する。不正な形式は 422 を返す。"""
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail=f"{field} must be a valid ISO 8601 date"
        ) from exc
