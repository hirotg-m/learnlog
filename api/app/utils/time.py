from __future__ import annotations

import os
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo


def now_utc() -> datetime:
    return datetime.now(UTC)


def to_iso_z(value: datetime) -> str:
    return (
        value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def today_in_app_timezone() -> date:
    """マイルストーンの期限超過判定などで使う「今日」を、アプリの想定タイムゾーンで返す。

    Lambda はデフォルトで UTC のため、`date.today()`(ローカルタイムゾーン依存)を
    そのまま使うと、日本時間の 0〜9 時台で「今日」の日付がずれる。
    """
    tz_name = os.getenv("APP_TIMEZONE", "Asia/Tokyo")
    return datetime.now(ZoneInfo(tz_name)).date()
