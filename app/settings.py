"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name, str(default)).lower()
    return value in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    debug: bool
    telegram_bot_token: str
    admin_id: int
    rss_url: str
    check_interval_hours: int
    rss_keywords: list[str]


def load_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN not found. "
            "Create a .env file with TELEGRAM_BOT_TOKEN=your_token"
        )

    admin_id_raw = os.getenv("ADMIN_ID", "").strip()
    if not admin_id_raw:
        raise RuntimeError(
            "ADMIN_ID not found. "
            "Create a .env file with ADMIN_ID=your_chat_id"
        )
    try:
        admin_id = int(admin_id_raw)
    except ValueError as exc:
        raise RuntimeError(
            f"ADMIN_ID must be an integer, got: {admin_id_raw!r}"
        ) from exc

    rss_url = os.getenv("RSS_URL", "").strip()
    if not rss_url:
        raise RuntimeError(
            "RSS_URL not found. "
            "Create a .env file with RSS_URL=https://example.com/feed.xml"
        )

    interval_raw = os.getenv("CHECK_INTERVAL_HOURS", "24").strip()
    try:
        check_interval_hours = int(interval_raw)
    except ValueError as exc:
        raise RuntimeError(
            f"CHECK_INTERVAL_HOURS must be an integer, got: {interval_raw!r}"
        ) from exc
    if check_interval_hours < 1:
        raise RuntimeError("CHECK_INTERVAL_HOURS must be >= 1")

    keywords_raw = os.getenv("RSS_KEYWORDS", "Октябрьский,Тульская")
    rss_keywords = [
        keyword.strip()
        for keyword in keywords_raw.split(",")
        if keyword.strip()
    ]
    if not rss_keywords:
        raise RuntimeError("RSS_KEYWORDS must contain at least one keyword")

    return Settings(
        debug=_env_bool("DEBUG"),
        telegram_bot_token=token,
        admin_id=admin_id,
        rss_url=rss_url,
        check_interval_hours=check_interval_hours,
        rss_keywords=rss_keywords,
    )


settings = load_settings()
