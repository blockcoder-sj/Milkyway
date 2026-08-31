"""Environment-only configuration with production fail-closed checks."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
AI_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,99}$")
PUBLIC_EXAMPLE_SECRETS = frozenset(
    {
        "dev-only-change-me",
        "local-club",
        "replace-with-32-plus-random-characters",
        "replace-with-at-least-20-random-characters",
        "replace-with-at-least-32-random-characters",
        "replace-with-a-different-32-plus-random-value",
        "replace-with-private-club-invite",
        "replace-with-url-encoded-password",
    }
)
EXAMPLE_HOSTNAMES = frozenset({"example.com", "quant.example.com"})


def _example_hostname(hostname: str | None) -> bool:
    value = (hostname or "").lower()
    return value in EXAMPLE_HOSTNAMES or value.endswith(".example") or value.endswith(
        ".example.com"
    )


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _weak_secret(value: str, minimum_length: int) -> bool:
    value = value.strip()
    return (
        len(value) < minimum_length
        or value in PUBLIC_EXAMPLE_SECRETS
        or len(set(value)) < 8
    )


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
    credential_backend: str
    ai_credential_secret: str
    market_credential_secret: str
    oci_kms_crypto_endpoint: str
    oci_ai_credential_key_id: str
    oci_market_credential_key_id: str
    credential_broker_url: str
    credential_broker_app_token: str
    credential_broker_paper_token: str
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
    max_request_body_bytes: int
    max_streams_per_user: int
    max_streams_total: int

    @property
    def production(self) -> bool:
        return self.app_env == "production"

    def startup_errors(self, service: str = "app") -> list[str]:
        if service not in {
            "app",
            "paper",
            "backtest",
            "scheduler",
            "broker",
            "deployment",
        }:
            raise ValueError("unknown service validation scope: {}".format(service))
        errors: list[str] = []
        if service != "broker" and not self.dataset_dir.joinpath("manifest.json").exists():
            errors.append("DATASET_DIR/manifest.json is missing")
        if self.production:
            needs_web_secrets = service in {"app", "deployment"}
            needs_market_secret = service in {"app", "paper", "deployment"}
            if needs_web_secrets and _weak_secret(self.session_secret, 32):
                errors.append("SESSION_SECRET must be an unguessable deployment-specific value")
            if needs_web_secrets and _weak_secret(self.invite_code, 20):
                errors.append("CLUB_INVITE_CODE must be an unguessable deployment-specific value")
            public_url = urlsplit(self.public_base_url)
            if needs_web_secrets and (
                public_url.scheme != "https"
                or not public_url.hostname
                or public_url.username
                or public_url.password
                or public_url.query
                or public_url.fragment
            ):
                errors.append("PUBLIC_BASE_URL must be a credential-free https origin in production")
            if needs_web_secrets and _example_hostname(public_url.hostname):
                errors.append("PUBLIC_BASE_URL must not use an example hostname")
            if service != "broker" and self.database_url.startswith("sqlite"):
                errors.append("production requires PostgreSQL, not SQLite")
            database_password = (
                ""
                if service == "broker"
                else unquote(urlsplit(self.database_url).password or "")
            )
            if service != "broker" and _weak_secret(database_password, 20):
                errors.append("DATABASE_URL must contain an unguessable deployment-specific password")
            if needs_web_secrets and (not self.allowed_hosts or "*" in self.allowed_hosts):
                errors.append("ALLOWED_HOSTS must explicitly list the public hostname")
            if needs_web_secrets and public_url.hostname not in self.allowed_hosts:
                errors.append("PUBLIC_BASE_URL hostname must be present in ALLOWED_HOSTS")
            broker_client = service in {"app", "paper", "deployment"}
            broker_service = service == "broker"
            if broker_client and self.credential_backend != "broker":
                errors.append("production app and paper services require CREDENTIAL_BACKEND=broker")
            if broker_service and self.credential_backend != "oci-kms":
                errors.append("production credential broker requires CREDENTIAL_BACKEND=oci-kms")
            if needs_web_secrets and self.ai_credential_secret:
                errors.append("AI_CREDENTIAL_SECRET must not be present in a production app process")
            if needs_market_secret and self.market_credential_secret:
                errors.append(
                    "MARKET_CREDENTIAL_SECRET must not be present in a production app process"
                )
            if broker_service and (self.ai_credential_secret or self.market_credential_secret):
                errors.append("legacy credential roots must not be present in the broker runtime")
            if broker_client:
                broker_url = urlsplit(self.credential_broker_url)
                if (
                    broker_url.scheme != "https"
                    or not broker_url.hostname
                    or broker_url.username
                    or broker_url.password
                    or broker_url.path not in {"", "/"}
                    or broker_url.query
                    or broker_url.fragment
                ):
                    errors.append("CREDENTIAL_BROKER_URL must be a credential-free https origin")
                if _example_hostname(broker_url.hostname):
                    errors.append("CREDENTIAL_BROKER_URL must not use an example hostname")
                if service in {"app", "deployment"} and _weak_secret(
                    self.credential_broker_app_token, 32
                ):
                    errors.append("CREDENTIAL_BROKER_APP_TOKEN must be an unguessable value")
                if service in {"paper", "deployment"} and _weak_secret(
                    self.credential_broker_paper_token, 32
                ):
                    errors.append("CREDENTIAL_BROKER_PAPER_TOKEN must be an unguessable value")
                if (
                    service == "deployment"
                    and self.credential_broker_app_token
                    and self.credential_broker_app_token == self.credential_broker_paper_token
                ):
                    errors.append("credential broker app and paper tokens must be independent")
                if any(
                    (
                        self.oci_kms_crypto_endpoint,
                        self.oci_ai_credential_key_id,
                        self.oci_market_credential_key_id,
                    )
                ):
                    errors.append("OCI KMS configuration must not be present in broker clients")
            if broker_service and self.credential_backend == "oci-kms":
                kms_url = urlsplit(self.oci_kms_crypto_endpoint)
                if (
                    kms_url.scheme != "https"
                    or not kms_url.hostname
                    or kms_url.username
                    or kms_url.password
                    or kms_url.query
                    or kms_url.fragment
                ):
                    errors.append("OCI_KMS_CRYPTO_ENDPOINT must be a credential-free https origin")
                if not self.oci_ai_credential_key_id.startswith(
                    "ocid1.key."
                ):
                    errors.append("OCI_AI_CREDENTIAL_KEY_ID must be a Vault key OCID")
                if not self.oci_market_credential_key_id.startswith(
                    "ocid1.key."
                ):
                    errors.append("OCI_MARKET_CREDENTIAL_KEY_ID must be a Vault key OCID")
                if (
                    self.oci_ai_credential_key_id == self.oci_market_credential_key_id
                ):
                    errors.append("AI and market credentials must use different OCI Vault keys")
                if _weak_secret(self.credential_broker_app_token, 32):
                    errors.append("CREDENTIAL_BROKER_APP_TOKEN must be an unguessable value")
                if _weak_secret(self.credential_broker_paper_token, 32):
                    errors.append("CREDENTIAL_BROKER_PAPER_TOKEN must be an unguessable value")
                if (
                    self.credential_broker_app_token
                    and self.credential_broker_app_token == self.credential_broker_paper_token
                ):
                    errors.append("credential broker app and paper tokens must be independent")
            independent = [
                value
                for value in (
                    self.session_secret if needs_web_secrets else "",
                    self.invite_code if needs_web_secrets else "",
                    database_password,
                    (
                        self.credential_broker_app_token
                        if service in {"app", "broker", "deployment"}
                        else ""
                    ),
                    (
                        self.credential_broker_paper_token
                        if service in {"paper", "broker", "deployment"}
                        else ""
                    ),
                )
                if value
            ]
            if len(independent) != len(set(independent)):
                errors.append("session, invite, database, and broker secrets must be independent")
        elif self.credential_backend not in {"local", "oci-kms", "broker"}:
            errors.append("CREDENTIAL_BACKEND must be local, oci-kms, or broker")
        if service in {"paper", "broker", "deployment"} and self.quote_provider not in {"mock", "kis"}:
            errors.append("QUOTE_PROVIDER must be mock or kis")
        if (
            service in {"paper", "broker", "deployment"}
            and self.quote_provider == "kis"
            and not self.market_data_sharing_allowed
        ):
            errors.append(
                "KIS quote sharing is disabled until MARKET_DATA_SHARING_ALLOWED=true "
                "is set after checking the broker/data licence"
            )
        if service in {"app", "broker", "deployment"} and self.local_ai_enabled:
            parsed = urlsplit(self.local_ai_base_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                errors.append("LOCAL_AI_BASE_URL must be an http(s) URL")
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                errors.append("LOCAL_AI_BASE_URL must not contain credentials, a query, or a fragment")
            if not AI_MODEL_PATTERN.fullmatch(self.local_ai_model):
                errors.append("LOCAL_AI_MODEL has an invalid model ID")
            if self.production and _weak_secret(self.local_ai_api_key, 20):
                errors.append("LOCAL_AI_API_KEY must be an unguessable deployment-specific value")
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
        credential_backend=os.getenv("CREDENTIAL_BACKEND", "local").strip().lower(),
        ai_credential_secret=os.getenv("AI_CREDENTIAL_SECRET", ""),
        market_credential_secret=os.getenv("MARKET_CREDENTIAL_SECRET", ""),
        oci_kms_crypto_endpoint=os.getenv("OCI_KMS_CRYPTO_ENDPOINT", "").rstrip("/"),
        oci_ai_credential_key_id=os.getenv("OCI_AI_CREDENTIAL_KEY_ID", "").strip(),
        oci_market_credential_key_id=os.getenv("OCI_MARKET_CREDENTIAL_KEY_ID", "").strip(),
        credential_broker_url=os.getenv("CREDENTIAL_BROKER_URL", "").rstrip("/"),
        credential_broker_app_token=os.getenv("CREDENTIAL_BROKER_APP_TOKEN", ""),
        credential_broker_paper_token=os.getenv("CREDENTIAL_BROKER_PAPER_TOKEN", ""),
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
        max_request_body_bytes=max(1024, _int("MAX_REQUEST_BODY_BYTES", 16 * 1024)),
        max_streams_per_user=max(1, _int("MAX_STREAMS_PER_USER", 2)),
        max_streams_total=max(1, _int("MAX_STREAMS_TOTAL", 64)),
    )
