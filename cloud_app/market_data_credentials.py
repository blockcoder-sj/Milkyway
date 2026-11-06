"""Validation, encryption and verification for member-owned quote feeds."""

from __future__ import annotations

import requests

from .config import Settings
from .credential_store import decrypt_credential, encrypt_credential
from .kis_quotes import KisCredentials, KisQuoteClient
from .toss_quotes import (
    TossAuthenticationError,
    TossCredentials,
    TossIpNotAllowedError,
    TossOpenApiError,
    TossPermissionError,
    TossEdgeBlockedError,
    TossQuoteClient,
    TossRateLimitError,
)


PROVIDERS = {
    "kis": {
        "label": "한국투자증권 Open API",
        "environments": [
            {"id": "real", "label": "실전투자 시세"},
            {"id": "paper", "label": "모의투자 환경"},
        ],
        "credential_labels": {"key": "App Key", "secret": "App Secret"},
        "credential_placeholders": {"key": "App Key 입력", "secret": "App Secret 입력"},
        "setup_help": "한국투자증권 개발자센터에서 발급한 키를 입력합니다.",
        "setup_url": "https://apiportal.koreainvestment.com/",
        "requires_allowed_ip": False,
    },
    "toss": {
        "label": "토스증권 Open API",
        "environments": [
            {"id": "live", "label": "실시간 시세 · 내부 페이퍼 체결 전용"},
        ],
        "credential_labels": {"key": "Client ID", "secret": "Client Secret"},
        "credential_placeholders": {
            "key": "Client ID 입력",
            "secret": "Client Secret 입력",
        },
        "setup_help": "토스증권 WTS에서 키를 발급하고 이 서버의 고정 공인 IP를 허용 IP로 등록합니다.",
        "setup_url": "https://corp.tossinvest.com/ko/open-api",
        "requires_allowed_ip": True,
    },
}


class MarketDataProviderError(RuntimeError):
    pass


def provider_catalog() -> list[dict]:
    return [
        {
            "id": provider,
            "label": details["label"],
            "environments": details["environments"],
            "credential_labels": details["credential_labels"],
            "credential_placeholders": details["credential_placeholders"],
            "setup_help": details["setup_help"],
            "setup_url": details["setup_url"],
            "requires_allowed_ip": details["requires_allowed_ip"],
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
    value: str,
    label: str,
    settings: Settings | None = None,
    *,
    owner_id: str = "legacy-unscoped",
    provider: str = "market",
    environment: str = "default",
) -> str:
    return encrypt_credential(
        validate_market_credential(value, label),
        settings,
        purpose="market",
        owner_id=owner_id,
        field="{}:{}:{}".format(provider, environment, label.lower()),
    )


def decrypt_market_credential(
    ciphertext: str,
    settings: Settings | None = None,
    *,
    owner_id: str = "legacy-unscoped",
    provider: str = "market",
    environment: str = "default",
    label: str = "credential",
) -> str:
    return decrypt_credential(
        ciphertext,
        settings,
        purpose="market",
        owner_id=owner_id,
        field="{}:{}:{}".format(provider, environment, label.lower()),
        error_message="시세 API 자격증명을 읽을 수 없습니다. 설정에서 다시 연결해 주세요",
    )


def credential_hint(value: str) -> str:
    return "••••" + value[-4:]


def verify_connection(provider: str, environment: str, api_key: str, api_secret: str) -> None:
    if provider == "kis":
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
        return
    if provider == "toss":
        client = TossQuoteClient(TossCredentials(client_id=api_key, client_secret=api_secret))
        try:
            client.authenticate(force=True)
        except TossIpNotAllowedError as exc:
            raise MarketDataProviderError(
                "토스증권이 서버 IP를 차단했습니다. WTS의 Open API 허용 IP에 이 서버의 고정 공인 IP를 등록해 주세요"
            ) from exc
        except TossEdgeBlockedError as exc:
            raise MarketDataProviderError("토스가 요청을 거부했습니다 (edge-blocked). IP 차단으로 확정할 수 없습니다. Client ID·Secret 입력값과 VPN·프록시·보안 프로그램을 확인해 주세요") from exc
        except TossPermissionError as exc:
            raise MarketDataProviderError("토스 Open API 접근 권한이 거부되었습니다 (403). IP 차단으로 확정할 수 없습니다. 키의 활성 상태·이용 권한을 확인해 주세요") from exc
        except TossAuthenticationError as exc:
            raise MarketDataProviderError(
                "토스증권 인증에 실패했습니다. Client ID와 Client Secret을 확인해 주세요"
            ) from exc
        except TossRateLimitError as exc:
            raise MarketDataProviderError(
                "토스증권 인증 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요"
            ) from exc
        except (TossOpenApiError, requests.RequestException) as exc:
            raise MarketDataProviderError("토스증권 Open API 연결 확인에 실패했습니다") from exc
        return
    raise MarketDataProviderError("지원하지 않는 시세 공급자입니다")
