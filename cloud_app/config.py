"""Environment-only configuration with production fail-closed checks."""

from __future__ import annotations

import os
import re
import secrets
import stat
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, unquote, urlsplit
from .native_platform import sync_directory, mode_is_private


ROOT = Path(__file__).resolve().parents[1]
AI_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,99}$")


def valid_database_tls_query(query: str) -> bool:
    try:
        fields = parse_qsl(query, strict_parsing=True)
    except ValueError:
        return False
    return len(fields) == 2 and dict(fields) == {
        "sslmode": "verify-full", "sslrootcert": "/run/secrets/postgres_tls_ca",
    }
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
PLACEHOLDER_SECRET_PATTERN = re.compile(
    r"^(?:replace[-_ ]with(?:[-_ ]|$)|change[-_ ]me(?:[-_ ]|$)|.*not[-_ ]configured$)",
    re.IGNORECASE,
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


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _app_environment() -> str:
    """Return the explicitly supported deployment mode or fail before startup."""

    raw = os.getenv("APP_ENV")
    if raw is None:
        raise RuntimeError("APP_ENV must be explicitly set to development or production")
    value = raw.strip().lower()
    if value not in {"development", "production"}:
        raise RuntimeError("APP_ENV must be exactly development or production")
    return value


def _weak_secret(value: str, minimum_length: int) -> bool:
    value = value.strip()
    return (
        len(value) < minimum_length
        or value.lower() in PUBLIC_EXAMPLE_SECRETS
        or bool(PLACEHOLDER_SECRET_PATTERN.match(value))
        or len(set(value)) < 8
    )


def _secret(name: str) -> str:
    """Read one secret from an environment value or a bounded regular file."""

    direct = os.getenv(name, "")
    source = os.getenv(name + "_FILE", "").strip()
    if direct and source:
        raise RuntimeError("{} and {}_FILE cannot both be set".format(name, name))
    if not source:
        return direct
    path = Path(source)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError("{}_FILE must name a regular file".format(name))
        if metadata.st_size < 1 or metadata.st_size > 4096:
            raise RuntimeError("{}_FILE size is invalid".format(name))
        if not mode_is_private(metadata):
            raise RuntimeError("{}_FILE must not be accessible by group or others".format(name))
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            payload = handle.read(4097)
    finally:
        os.close(descriptor)
    if len(payload) != metadata.st_size or len(payload) > 4096:
        raise RuntimeError("{}_FILE changed while it was read".format(name))
    try:
        return payload.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise RuntimeError("{}_FILE must contain UTF-8 text".format(name)) from exc


def member_ai_credentials_enabled(settings) -> bool:
    """Shared club AI never needs a member AI key, including personal-market mode."""

    return bool(
        settings.member_credentials_enabled
        and not getattr(settings, "shared_ai_enabled", False)
        and not getattr(settings, "personal_local_mode", False)
    )


def _session_secret() -> str:
    configured = _secret("SESSION_SECRET")
    if configured or not _bool("PERSONAL_LOCAL_MODE"):
        return configured or "dev-only-change-me"
    return persistent_local_secret(ROOT / "runtime/.session_secret")


def persistent_local_secret(path: Path) -> str:
    # Every install has durable local keys, shared by all its containers.
    # Publish a fully written file atomically; simultaneous first starts cannot
    # read a half-written key or accidentally replace another process's key.
    root = path.parent
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(root, 0o700)
    if not path.exists():
        descriptor, temporary = tempfile.mkstemp(prefix=".secret-new-", dir=root)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(secrets.token_urlsafe(48))
                handle.flush()
                os.fsync(handle.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                pass
        finally:
            os.unlink(temporary)
    # Publish the directory entry durably before a caller can commit data
    # encrypted/signed with this key. This also covers a concurrent creator.
    sync_directory(root)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
        metadata = os.fstat(handle.fileno())
        if not stat.S_ISREG(metadata.st_mode) or not mode_is_private(metadata) or not 32 <= metadata.st_size <= 4096:
            raise RuntimeError("Local key must be an owner-only regular file")
        value = handle.read(4097).strip()
    if len(value) < 32 or len(value) > 4096:
        raise RuntimeError("Local key is invalid; restore its backup")
    return value


def _configured_provider_secret(name: str) -> str:
    # Reject before opening a file: production holds secret identifiers only.
    if _app_environment() == "production":
        if os.getenv(name, "") or os.getenv(name + "_FILE", ""):
            raise RuntimeError(name + " must be delivered by OCI Vault in production")
        return ""
    return _secret(name)


def valid_vault_secret_id(value: str) -> bool:
    return bool(re.fullmatch(r"ocid1\.vaultsecret\.oc[0-9]+\.[a-z0-9-]+\.[a-zA-Z0-9._-]{20,200}", value))


@dataclass(frozen=True)
class Settings:
    app_env: str
    app_name: str
    public_base_url: str
    database_url: str
    session_secret: str
    session_hours: int
    invite_code: str
    legacy_invite_enabled: bool
    allowed_hosts: tuple[str, ...]
    dataset_dir: Path
    snapshots_glob: str
    terminal_events_path: Path
    local_demo_data: bool
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
    member_credentials_enabled: bool
    shared_ai_enabled: bool
    shared_ai_provider: str
    shared_ai_model: str
    shared_ai_api_key: str
    ai_timeout_seconds: int
    local_ai_enabled: bool
    local_ai_base_url: str
    local_ai_model: str
    local_ai_api_key: str
    local_ai_max_concurrent_requests: int
    quote_provider: str
    market_data_sharing_allowed: bool
    broker_api_key: str
    broker_api_secret: str
    broker_account_id: str
    kis_environment: str
    kis_quote_transport: str
    quote_interval_seconds: int
    worker_stale_seconds: int
    max_backtests_per_user_day: int
    max_outstanding_backtests_per_user: int
    max_outstanding_backtests_total: int
    max_backtest_result_bytes: int
    max_completed_backtests_per_user: int
    backtest_retention_days: int
    backtest_timeout_seconds: int
    max_strategies_per_user: int
    max_accounts_per_user: int
    max_users: int
    max_request_body_bytes: int
    max_request_body_messages: int
    request_body_read_timeout_seconds: float
    max_streams_per_user: int
    max_streams_total: int
    database_pool_size: int
    database_max_overflow: int
    database_pool_timeout_seconds: int
    password_max_concurrent_requests: int
    registration_global_attempts: int
    login_account_attempts: int
    login_account_window_seconds: int
    login_global_attempts: int
    kms_max_concurrent_requests: int
    quote_max_concurrent_requests: int
    quote_deadline_seconds: float
    quote_max_provider_calls: int
    shared_quote_batch_size: int
    shared_quote_max_symbols_per_tick: int
    shared_quote_tick_deadline_seconds: float
    quote_max_age_seconds: int
    service_role: str = ""
    oci_shared_ai_secret_id: str = ""
    oci_broker_api_key_secret_id: str = ""
    oci_broker_api_secret_secret_id: str = ""
    authority_enabled: bool = False
    credential_broker_backtest_token: str = ""
    personal_local_mode: bool = False

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
        if service != "broker" and not self.personal_local_mode and not self.dataset_dir.joinpath("manifest.json").exists():
            errors.append("DATASET_DIR/manifest.json is missing")
        if self.personal_local_mode:
            if self.max_users != 1:
                errors.append("Personal mode is single-owner; MAX_USERS must be 1")
            if _weak_secret(self.session_secret, 32):
                errors.append("Personal mode requires its per-installation session secret")
            if (ROOT / "runtime/RESTORE_IN_PROGRESS").exists():
                errors.append("A restore was interrupted; complete recovery before starting services")
            if self.production:
                errors.append("PERSONAL_LOCAL_MODE is allowed only in development")
            if self.local_demo_data or self.quote_provider != "member":
                errors.append("Personal mode requires member quotes and cannot use demo data")
            if not self.member_credentials_enabled or self.credential_backend != "local":
                errors.append("Personal mode requires local member credentials")
            if self.authority_enabled or self.shared_ai_enabled:
                errors.append("Personal mode does not use shared cloud services")
            if not self.allowed_hosts or any(host not in {"localhost", "127.0.0.1", "[::1]", "testserver"} for host in self.allowed_hosts):
                errors.append("Personal mode must use loopback hosts only")
            if urlsplit(self.public_base_url).hostname not in {"localhost", "127.0.0.1", "::1"}:
                errors.append("Personal mode PUBLIC_BASE_URL must be loopback")
            if not self.database_url.startswith("sqlite:"):
                errors.append("Personal mode requires its local SQLite database")
        if self.production and self.local_demo_data:
            errors.append("LOCAL_DEMO_DATA is allowed only in development")
        if self.production:
            if not self.authority_enabled:
                errors.append("AUTHORITY_ENABLED must be true in production")
            needs_web_secrets = service in {"app", "deployment"}
            needs_market_secret = service in {"app", "paper", "deployment"}
            if needs_web_secrets and _weak_secret(self.session_secret, 32):
                errors.append("SESSION_SECRET must be an unguessable deployment-specific value")
            if needs_web_secrets and self.legacy_invite_enabled:
                errors.append("LEGACY_CLUB_INVITE_ENABLED must be false in production")
            if (
                needs_web_secrets
                and self.legacy_invite_enabled
                and _weak_secret(self.invite_code, 20)
            ):
                errors.append("CLUB_INVITE_CODE must be an unguessable deployment-specific value")
            public_url = urlsplit(self.public_base_url)
            if (needs_web_secrets or service == "broker") and (
                public_url.scheme != "https"
                or not public_url.hostname
                or public_url.username
                or public_url.password
                or public_url.path not in {"", "/"}
                or public_url.query
                or public_url.fragment
            ):
                errors.append("PUBLIC_BASE_URL must be a credential-free https origin in production")
            if (needs_web_secrets or service == "broker") and _example_hostname(public_url.hostname):
                errors.append("PUBLIC_BASE_URL must not use an example hostname")
            db_url = urlsplit(self.database_url)
            if db_url.scheme not in {"postgresql", "postgresql+psycopg"} or not db_url.hostname or db_url.fragment:
                errors.append("production requires a credentialed PostgreSQL URL")
            if not valid_database_tls_query(db_url.query):
                errors.append("DATABASE_URL requires sslmode=verify-full and the mounted PostgreSQL CA")
            expected_db_roles = {"app": "milkyway_app", "paper": "milkyway_paper", "backtest": "milkyway_backtest",
                                 "scheduler": "milkyway_scheduler", "broker": "milkyway_authority"}
            if service in expected_db_roles and unquote(db_url.username or "") != expected_db_roles[service]:
                errors.append("DATABASE_URL must use the dedicated " + expected_db_roles[service] + " role")
            database_password = unquote(urlsplit(self.database_url).password or "")
            if _weak_secret(database_password, 20):
                errors.append("DATABASE_URL must contain an unguessable deployment-specific password")
            if needs_web_secrets and (not self.allowed_hosts or "*" in self.allowed_hosts):
                errors.append("ALLOWED_HOSTS must explicitly list the public hostname")
            if needs_web_secrets and public_url.hostname not in self.allowed_hosts:
                errors.append("PUBLIC_BASE_URL hostname must be present in ALLOWED_HOSTS")
            broker_client = service in {"app", "paper", "backtest", "deployment"}
            broker_service = service == "broker"
            if service in {"app", "paper", "broker", "deployment"} and not self.member_credentials_enabled:
                errors.append("MEMBER_CREDENTIALS_ENABLED must be true for personal brokerage keys")
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
            shared_secrets = (
                self.shared_ai_api_key,
                self.broker_api_key,
                self.broker_api_secret,
                self.broker_account_id,
            )
            if broker_client and any(shared_secrets):
                errors.append("shared provider credentials must not be present in broker clients")
            vault_ids = (
                self.oci_shared_ai_secret_id,
                self.oci_broker_api_key_secret_id,
                self.oci_broker_api_secret_secret_id,
            )
            if service != "broker" and any(vault_ids):
                errors.append("OCI provider-secret identifiers belong only on the broker")
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
                if service in {"backtest", "deployment"} and _weak_secret(self.credential_broker_backtest_token, 32):
                    errors.append("CREDENTIAL_BROKER_BACKTEST_TOKEN must be an unguessable value")
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
            if broker_service:
                if self.service_role != "broker":
                    errors.append("SERVICE_ROLE must be broker for OCI provider-secret delivery")
                if any((self.shared_ai_api_key, self.broker_api_key, self.broker_api_secret)):
                    errors.append("provider secrets must be released by OCI Vault, not local files or environment values")
                required_vault_ids = []
                if self.shared_ai_provider in {"openai", "anthropic"}:
                    required_vault_ids.append(("OCI_SHARED_AI_SECRET_ID", self.oci_shared_ai_secret_id))
                if self.quote_provider == "kis":
                    required_vault_ids.extend((
                        ("OCI_BROKER_API_KEY_SECRET_ID", self.oci_broker_api_key_secret_id),
                        ("OCI_BROKER_API_SECRET_SECRET_ID", self.oci_broker_api_secret_secret_id),
                    ))
                for name, value in required_vault_ids:
                    if not valid_vault_secret_id(value):
                        errors.append(name + " must identify an OCI Vault secret")
                configured_vault_ids = [value for value in vault_ids if value]
                if len(configured_vault_ids) != len(set(configured_vault_ids)):
                    errors.append("provider secret identifiers must be independent")
                if (not self.oci_kms_crypto_endpoint.startswith("https://")
                        or not self.oci_ai_credential_key_id.startswith("ocid1.key.")
                        or not self.oci_market_credential_key_id.startswith("ocid1.key.")
                        or self.oci_ai_credential_key_id == self.oci_market_credential_key_id):
                    errors.append("Independent OCI credential keys and crypto endpoint are required on the broker")
                if _weak_secret(self.session_secret, 32):
                    errors.append("Authority SESSION_SECRET must be an unguessable value")
                if _weak_secret(self.credential_broker_backtest_token, 32):
                    errors.append("CREDENTIAL_BROKER_BACKTEST_TOKEN must be an unguessable value")
                if len({self.credential_broker_app_token, self.credential_broker_paper_token, self.credential_broker_backtest_token}) != 3:
                    errors.append("All broker role tokens must be independent")
                if _weak_secret(self.credential_broker_app_token, 32):
                    errors.append("CREDENTIAL_BROKER_APP_TOKEN must be an unguessable value")
                if _weak_secret(self.credential_broker_paper_token, 32):
                    errors.append("CREDENTIAL_BROKER_PAPER_TOKEN must be an unguessable value")
                if (
                    self.credential_broker_app_token
                    and self.credential_broker_app_token == self.credential_broker_paper_token
                ):
                    errors.append("credential broker app and paper tokens must be independent")
                provider_secrets = tuple(
                    value
                    for value in (
                        self.shared_ai_api_key,
                        self.local_ai_api_key,
                        self.broker_api_key,
                        self.broker_api_secret,
                    )
                    if value
                )
                role_tokens = tuple(
                    value
                    for value in (
                        self.credential_broker_app_token,
                        self.credential_broker_paper_token,
                    )
                    if value
                )
                if len(provider_secrets) != len(set(provider_secrets)) or any(
                    token in provider_secrets for token in role_tokens
                ):
                    errors.append("broker role tokens and provider secrets must be independent")
                required_file_secrets = []
                if self.shared_ai_provider == "local":
                    required_file_secrets.append("LOCAL_AI_API_KEY")
                for name in required_file_secrets:
                    if not os.getenv(name + "_FILE", "").strip():
                        errors.append(
                            "{}_FILE is required; provider secrets must not use plaintext environment values".format(
                                name
                            )
                        )
                if not self.shared_ai_enabled:
                    errors.append("SHARED_AI_ENABLED must be true for the club AI service")
                if self.shared_ai_provider not in {"openai", "anthropic", "local"}:
                    errors.append("SHARED_AI_PROVIDER must be openai, anthropic, or local")
                if not AI_MODEL_PATTERN.fullmatch(self.shared_ai_model):
                    errors.append("SHARED_AI_MODEL has an invalid model ID")
                if (
                    self.shared_ai_enabled
                    and self.shared_ai_provider == "local"
                    and not self.local_ai_enabled
                ):
                    errors.append("LOCAL_AI_ENABLED must be true when SHARED_AI_PROVIDER=local")
            independent = [
                value
                for value in (
                    self.session_secret if needs_web_secrets or broker_service else "",
                    self.invite_code
                    if needs_web_secrets and self.legacy_invite_enabled
                    else "",
                    database_password,
                    (
                        self.credential_broker_app_token
                        if service in {"app", "broker", "deployment"}
                        else ""
                    ),
                    self.credential_broker_backtest_token if service in {"backtest", "broker", "deployment"} else "",
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
        elif self.credential_backend not in {"local", "oci-kms", "broker", "shared"}:
            errors.append("CREDENTIAL_BACKEND must be local, oci-kms, broker, or shared")
        if service in {"paper", "broker", "deployment"} and self.quote_provider not in ({"member"} if self.personal_local_mode else {"mock", "kis"}):
            errors.append("QUOTE_PROVIDER must be mock or kis (member only in personal mode)")
        if (
            service in {"paper", "broker", "deployment"}
            and self.quote_provider == "kis"
            and not self.market_data_sharing_allowed
        ):
            errors.append(
                "KIS quote sharing is disabled until MARKET_DATA_SHARING_ALLOWED=true "
                "is set after checking the broker/data licence"
            )
        if (
            service in {"paper", "broker", "deployment"}
            and self.kis_quote_transport != "rest"
        ):
            errors.append("KIS_QUOTE_TRANSPORT must be rest; WebSocket is not implemented")
        if service in {"paper", "broker", "deployment"} and self.kis_environment not in {
            "paper",
            "live",
        }:
            errors.append("KIS_ENVIRONMENT must be paper or live")
        if service in {"paper", "broker", "deployment"}:
            if (
                self.quote_provider == "kis"
                and self.shared_quote_batch_size
                != self.shared_quote_max_symbols_per_tick
            ):
                errors.append(
                    "KIS shared quote work must fit exactly one broker batch per tick"
                )
            effective_tick_seconds = max(
                self.quote_interval_seconds,
                int(self.shared_quote_tick_deadline_seconds + 0.999999),
            ) + 1
            if (
                self.quote_provider == "kis"
                and self.quote_max_age_seconds <= effective_tick_seconds
            ):
                errors.append(
                    "QUOTE_MAX_AGE_SECONDS must exceed the complete paper tick bound"
                )
            if (
                service == "broker"
                and self.quote_provider == "kis"
                and self.quote_max_provider_calls
                < (self.shared_quote_batch_size * 3) + 1
            ):
                errors.append(
                    "QUOTE_MAX_PROVIDER_CALLS must cover the configured KIS batch"
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
        app_env=_app_environment(),
        app_name=os.getenv("APP_NAME", "Milkyway Quant Trading Lab"),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "http://localhost:8080").rstrip("/"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///runtime/club.sqlite3"),
        session_secret=_session_secret(),
        session_hours=_int("SESSION_HOURS", 12),
        invite_code=os.getenv("CLUB_INVITE_CODE", "local-club"),
        legacy_invite_enabled=_bool(
            "LEGACY_CLUB_INVITE_ENABLED", _app_environment() == "development"
        ),
        allowed_hosts=hosts,
        dataset_dir=Path(os.getenv("DATASET_DIR", str(dataset_default))).expanduser(),
        snapshots_glob=os.getenv(
            "SNAPSHOTS_GLOB", str(ROOT / "data_cache/universe_snapshots/*.json")
        ),
        terminal_events_path=Path(os.getenv("TERMINAL_EVENTS_PATH", str(event_default))).expanduser(),
        local_demo_data=_bool("LOCAL_DEMO_DATA", False),
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
        member_credentials_enabled=_bool("MEMBER_CREDENTIALS_ENABLED", True),
        shared_ai_enabled=_bool("SHARED_AI_ENABLED", False),
        shared_ai_provider=os.getenv("SHARED_AI_PROVIDER", "openai").strip().lower(),
        shared_ai_model=os.getenv("SHARED_AI_MODEL", "gpt-5.6-luna").strip(),
        shared_ai_api_key=_configured_provider_secret("SHARED_AI_API_KEY"),
        ai_timeout_seconds=_int("AI_TIMEOUT_SECONDS", 120),
        local_ai_enabled=_bool("LOCAL_AI_ENABLED", False),
        local_ai_base_url=os.getenv("LOCAL_AI_BASE_URL", "http://ai:8080/v1").rstrip("/"),
        local_ai_model=os.getenv(
            "LOCAL_AI_MODEL", "Qwen2.5-Coder-7B-Instruct-GGUF"
        ).strip(),
        local_ai_api_key=_secret("LOCAL_AI_API_KEY"),
        local_ai_max_concurrent_requests=max(
            1, _int("LOCAL_AI_MAX_CONCURRENT_REQUESTS", 4)
        ),
        quote_provider=os.getenv("QUOTE_PROVIDER", "mock").strip().lower(),
        market_data_sharing_allowed=_bool("MARKET_DATA_SHARING_ALLOWED", False),
        broker_api_key=_configured_provider_secret("BROKER_API_KEY"),
        broker_api_secret=_configured_provider_secret("BROKER_API_SECRET"),
        service_role=os.getenv("SERVICE_ROLE", "").strip(),
        authority_enabled=_bool("AUTHORITY_ENABLED", False),
        credential_broker_backtest_token=os.getenv("CREDENTIAL_BROKER_BACKTEST_TOKEN", ""),
        oci_shared_ai_secret_id=os.getenv("OCI_SHARED_AI_SECRET_ID", "").strip(),
        oci_broker_api_key_secret_id=os.getenv("OCI_BROKER_API_KEY_SECRET_ID", "").strip(),
        oci_broker_api_secret_secret_id=os.getenv("OCI_BROKER_API_SECRET_SECRET_ID", "").strip(),
        broker_account_id=os.getenv("BROKER_ACCOUNT_ID", ""),
        kis_environment=os.getenv("KIS_ENVIRONMENT", "paper").strip().lower(),
        kis_quote_transport=os.getenv("KIS_QUOTE_TRANSPORT", "rest").strip().lower(),
        quote_interval_seconds=max(1, _int("QUOTE_INTERVAL_SECONDS", 30)),
        worker_stale_seconds=max(30, _int("WORKER_STALE_SECONDS", 90)),
        max_backtests_per_user_day=max(1, _int("MAX_BACKTESTS_PER_USER_DAY", 20)),
        max_outstanding_backtests_per_user=max(
            1, _int("MAX_OUTSTANDING_BACKTESTS_PER_USER", 2)
        ),
        max_outstanding_backtests_total=max(
            1, _int("MAX_OUTSTANDING_BACKTESTS_TOTAL", 40)
        ),
        max_backtest_result_bytes=max(
            16 * 1024, _int("MAX_BACKTEST_RESULT_BYTES", 1024 * 1024)
        ),
        max_completed_backtests_per_user=max(
            1, _int("MAX_COMPLETED_BACKTESTS_PER_USER", 50)
        ),
        backtest_retention_days=max(1, _int("BACKTEST_RETENTION_DAYS", 30)),
        backtest_timeout_seconds=max(30, _int("BACKTEST_TIMEOUT_SECONDS", 300)),
        max_strategies_per_user=max(1, _int("MAX_STRATEGIES_PER_USER", 10)),
        max_accounts_per_user=max(1, _int("MAX_ACCOUNTS_PER_USER", 3)),
        max_users=max(1, _int("MAX_USERS", 1 if _bool("PERSONAL_LOCAL_MODE") else 40)),
        max_request_body_bytes=max(1024, _int("MAX_REQUEST_BODY_BYTES", 16 * 1024)),
        max_request_body_messages=max(2, _int("MAX_REQUEST_BODY_MESSAGES", 64)),
        request_body_read_timeout_seconds=max(
            1.0, _float("REQUEST_BODY_READ_TIMEOUT_SECONDS", 15.0)
        ),
        max_streams_per_user=max(1, _int("MAX_STREAMS_PER_USER", 2)),
        max_streams_total=max(1, _int("MAX_STREAMS_TOTAL", 64)),
        database_pool_size=max(2, _int("DATABASE_POOL_SIZE", 10)),
        database_max_overflow=max(0, _int("DATABASE_MAX_OVERFLOW", 5)),
        database_pool_timeout_seconds=max(1, _int("DATABASE_POOL_TIMEOUT_SECONDS", 10)),
        password_max_concurrent_requests=max(
            1, _int("PASSWORD_MAX_CONCURRENT_REQUESTS", 4)
        ),
        registration_global_attempts=max(
            1, _int("REGISTRATION_GLOBAL_ATTEMPTS", 20)
        ),
        login_account_attempts=max(1, _int("LOGIN_ACCOUNT_ATTEMPTS", 10)),
        login_account_window_seconds=max(
            60, _int("LOGIN_ACCOUNT_WINDOW_SECONDS", 600)
        ),
        login_global_attempts=max(10, _int("LOGIN_GLOBAL_ATTEMPTS", 400)),
        kms_max_concurrent_requests=max(1, _int("KMS_MAX_CONCURRENT_REQUESTS", 4)),
        quote_max_concurrent_requests=max(1, _int("QUOTE_MAX_CONCURRENT_REQUESTS", 2)),
        quote_deadline_seconds=max(1.0, _float("QUOTE_DEADLINE_SECONDS", 20.0)),
        quote_max_provider_calls=max(1, _int("QUOTE_MAX_PROVIDER_CALLS", 120)),
        shared_quote_batch_size=min(200, max(1, _int("SHARED_QUOTE_BATCH_SIZE", 200))),
        shared_quote_max_symbols_per_tick=max(
            1, _int("SHARED_QUOTE_MAX_SYMBOLS_PER_TICK", 1000)
        ),
        shared_quote_tick_deadline_seconds=min(
            60.0, max(1.0, _float("SHARED_QUOTE_TICK_DEADLINE_SECONDS", 30.0))
        ),
        quote_max_age_seconds=max(30, _int("QUOTE_MAX_AGE_SECONDS", 180)),
        personal_local_mode=_bool("PERSONAL_LOCAL_MODE", False),
    )
