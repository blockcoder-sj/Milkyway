"""Environment-only configuration with production fail-closed checks."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
AI_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,99}$")


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_name: str
    public_base_url: str
    database_url: str
    session_secret: str
    session_hours: int
    invite_code: str
    allowed_hosts: tuple[str, ...]
    dataset_dir: Path
    snapshots_glob: str
    terminal_events_path: Path
    sector_map_path: Path
    news_feed_path: Path
    ai_credential_secret: str
    ai_timeout_seconds: int
    local_ai_enabled: bool
    local_ai_base_url: str
    local_ai_model: str
    local_ai_api_key: str
    local_ai_max_concurrent_requests: int
    quote_provider: str
    market_data_sharing_allowed: bool
    quote_interval_seconds: int
    worker_stale_seconds: int
    max_backtests_per_user_day: int
    max_strategies_per_user: int
    max_accounts_per_user: int
    max_users: int

    @property
    def production(self) -> bool:
        return self.app_env == "production"

    def startup_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.dataset_dir.joinpath("manifest.json").exists():
            errors.append("DATASET_DIR/manifest.json is missing")
        if self.production:
            if len(self.session_secret) < 32 or self.session_secret == "dev-only-change-me":
                errors.append("SESSION_SECRET must be a random value of at least 32 characters")
            if len(self.invite_code) < 8:
                errors.append("CLUB_INVITE_CODE must contain at least 8 characters")
            if not self.public_base_url.startswith("https://"):
                errors.append("PUBLIC_BASE_URL must use https in production")
            if self.database_url.startswith("sqlite"):
                errors.append("production requires PostgreSQL, not SQLite")
            if not self.allowed_hosts or "*" in self.allowed_hosts:
                errors.append("ALLOWED_HOSTS must explicitly list the public hostname")
            if len(self.ai_credential_secret) < 32:
                errors.append("AI_CREDENTIAL_SECRET must be a random value of at least 32 characters")
        if self.quote_provider not in {"mock", "kis"}:
            errors.append("QUOTE_PROVIDER must be mock or kis")
        if self.quote_provider == "kis" and not self.market_data_sharing_allowed:
            errors.append(
                "KIS quote sharing is disabled until MARKET_DATA_SHARING_ALLOWED=true "
                "is set after checking the broker/data licence"
            )
        if self.local_ai_enabled:
            parsed = urlsplit(self.local_ai_base_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                errors.append("LOCAL_AI_BASE_URL must be an http(s) URL")
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                errors.append("LOCAL_AI_BASE_URL must not contain credentials, a query, or a fragment")
            if not AI_MODEL_PATTERN.fullmatch(self.local_ai_model):
                errors.append("LOCAL_AI_MODEL has an invalid model ID")
            if self.production and len(self.local_ai_api_key) < 20:
                errors.append("LOCAL_AI_API_KEY must contain at least 20 characters in production")
        return errors


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    dataset_default = ROOT / "data_cache/backtest_datasets/2026_equities_pit_20260824"
    event_default = ROOT / "data_cache/universe_events/events.jsonl"
    hosts = tuple(
        item.strip() for item in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
        if item.strip()
    )
    return Settings(
        app_env=os.getenv("APP_ENV", "development").strip().lower(),
        app_name=os.getenv("APP_NAME", "Milkyway Quant Trading Lab"),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "http://localhost:8080").rstrip("/"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///runtime/club.sqlite3"),
        session_secret=os.getenv("SESSION_SECRET", "dev-only-change-me"),
        session_hours=_int("SESSION_HOURS", 12),
        invite_code=os.getenv("CLUB_INVITE_CODE", "local-club"),
        allowed_hosts=hosts,
        dataset_dir=Path(os.getenv("DATASET_DIR", str(dataset_default))).expanduser(),
        snapshots_glob=os.getenv(
            "SNAPSHOTS_GLOB", str(ROOT / "data_cache/universe_snapshots/*.json")
        ),
        terminal_events_path=Path(os.getenv("TERMINAL_EVENTS_PATH", str(event_default))).expanduser(),
        sector_map_path=Path(
            os.getenv("SECTOR_MAP_PATH", str(ROOT / "data_cache/_sector_map.json"))
        ).expanduser(),
        news_feed_path=Path(
            os.getenv("NEWS_FEED_PATH", str(ROOT / "data_cache/news/news_feed.json"))
        ).expanduser(),
        ai_credential_secret=os.getenv("AI_CREDENTIAL_SECRET", ""),
        ai_timeout_seconds=_int("AI_TIMEOUT_SECONDS", 120),
        local_ai_enabled=_bool("LOCAL_AI_ENABLED", False),
        local_ai_base_url=os.getenv("LOCAL_AI_BASE_URL", "http://ai:8080/v1").rstrip("/"),
        local_ai_model=os.getenv(
            "LOCAL_AI_MODEL", "Qwen2.5-Coder-7B-Instruct-GGUF"
        ).strip(),
        local_ai_api_key=os.getenv("LOCAL_AI_API_KEY", ""),
        local_ai_max_concurrent_requests=max(
            1, _int("LOCAL_AI_MAX_CONCURRENT_REQUESTS", 4)
        ),
        quote_provider=os.getenv("QUOTE_PROVIDER", "mock").strip().lower(),
        market_data_sharing_allowed=_bool("MARKET_DATA_SHARING_ALLOWED", False),
        quote_interval_seconds=max(5, _int("QUOTE_INTERVAL_SECONDS", 30)),
        worker_stale_seconds=max(30, _int("WORKER_STALE_SECONDS", 90)),
        max_backtests_per_user_day=max(1, _int("MAX_BACKTESTS_PER_USER_DAY", 20)),
        max_strategies_per_user=max(1, _int("MAX_STRATEGIES_PER_USER", 10)),
        max_accounts_per_user=max(1, _int("MAX_ACCOUNTS_PER_USER", 3)),
        max_users=max(1, _int("MAX_USERS", 40)),
    )
