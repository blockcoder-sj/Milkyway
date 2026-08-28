"""Validation, encryption and verification for member-owned quote feeds."""

from __future__ import annotations

from .config import Settings
from .credential_store import decrypt_credential, encrypt_credential
from .kis_quotes import KisCredentials, KisQuoteClient


PROVIDERS = {
    "kis": {
        "label": "한국투자증권 Open API",
        "environments": [
            {"id": "real", "label": "실전투자 시세"},
            {"id": "paper", "label": "모의투자 환경"},
        ],
    }
}


class MarketDataProviderError(RuntimeError):
    pass


def provider_catalog() -> list[dict]:
    return [
        {
            "id": provider,
            "label": details["label"],
            "environments": details["environments"],
        }
        for provider, details in PROVIDERS.items()
    ]


def validate_provider_environment(provider: str, environment: str) -> tuple[str, str]:
    provider = provider.strip().lower()
    environment = environment.strip().lower()
    details = PROVIDERS.get(provider)
    if details is None:
        raise ValueError("지원하지 않는 시세 공급자입니다")
    if environment not in {item["id"] for item in details["environments"]}:
        raise ValueError("시세 API 환경이 올바르지 않습니다")
    return provider, environment


def validate_market_credential(value: str, label: str) -> str:
    value = value.strip()
    if len(value) < 20 or len(value) > 512 or any(character.isspace() for character in value):
        raise ValueError(f"{label} 형식이 올바르지 않습니다")
    return value


def encrypt_market_credential(
    value: str, label: str, settings: Settings | None = None
) -> str:
    return encrypt_credential(validate_market_credential(value, label), settings)


def decrypt_market_credential(ciphertext: str, settings: Settings | None = None) -> str:
    return decrypt_credential(
        ciphertext,
        settings,
        error_message="시세 API 자격증명을 읽을 수 없습니다. 설정에서 다시 연결해 주세요",
    )


def credential_hint(value: str) -> str:
    return "••••" + value[-4:]


def verify_connection(provider: str, environment: str, api_key: str, api_secret: str) -> None:
    if provider != "kis":
        raise MarketDataProviderError("지원하지 않는 시세 공급자입니다")
    client = KisQuoteClient(
        KisCredentials(
            api_key=api_key,
            api_secret=api_secret,
            paper=environment == "paper",
        )
    )
    if not client.connect():
        raise MarketDataProviderError(
            "KIS 인증에 실패했습니다. App Key·App Secret과 실전/모의 환경을 확인해 주세요"
        )
