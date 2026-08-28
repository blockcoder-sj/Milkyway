"""Encryption and validation for user-owned AI provider credentials."""

from __future__ import annotations

from .config import AI_MODEL_PATTERN, Settings, get_settings
from .credential_store import decrypt_credential, encrypt_credential


PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "default_model": "gpt-5.6-luna",
        "model_examples": ["gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"],
        "requires_api_key": True,
    },
    "anthropic": {
        "label": "Anthropic",
        "default_model": "claude-sonnet-4-20250514",
        "model_examples": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"],
        "requires_api_key": True,
    },
    "local": {
        "label": "로컬 AI",
        "default_model": "Qwen2.5-Coder-7B-Instruct-GGUF",
        "model_examples": ["Qwen2.5-Coder-7B-Instruct-GGUF"],
        "requires_api_key": False,
    },
}


def provider_catalog(
    settings: Settings | None = None, *, local_ready: bool | None = None
) -> list[dict]:
    settings = settings or get_settings()
    return [
        {
            "id": provider,
            "label": details["label"],
            "default_model": (
                settings.local_ai_model if provider == "local" else details["default_model"]
            ),
            "model_examples": (
                [settings.local_ai_model] if provider == "local" else details["model_examples"]
            ),
            "requires_api_key": details["requires_api_key"],
            "available": provider != "local" or settings.local_ai_enabled,
            "ready": (
                True
                if provider != "local"
                else settings.local_ai_enabled and bool(local_ready)
            ),
            "disabled_reason": (
                "서버 관리자가 로컬 AI를 활성화해야 합니다"
                if provider == "local" and not settings.local_ai_enabled
                else None
            ),
        }
        for provider, details in PROVIDERS.items()
    ]


def provider_requires_api_key(provider: str) -> bool:
    details = PROVIDERS.get(provider.strip().lower())
    if details is None:
        raise ValueError("지원하지 않는 AI 공급자입니다")
    return bool(details["requires_api_key"])


def validate_provider_model(provider: str, model: str) -> tuple[str, str]:
    provider = provider.strip().lower()
    model = model.strip()
    if provider not in PROVIDERS:
        raise ValueError("지원하지 않는 AI 공급자입니다")
    if not AI_MODEL_PATTERN.fullmatch(model):
        raise ValueError("모델 ID 형식이 올바르지 않습니다")
    return provider, model


def validate_api_key(api_key: str) -> str:
    value = api_key.strip()
    if len(value) < 20 or len(value) > 512 or any(character.isspace() for character in value):
        raise ValueError("API 키 형식이 올바르지 않습니다")
    return value


def encrypt_api_key(api_key: str, settings: Settings | None = None) -> str:
    return encrypt_credential(validate_api_key(api_key), settings)


def decrypt_api_key(ciphertext: str, settings: Settings | None = None) -> str:
    return decrypt_credential(
        ciphertext,
        settings,
        error_message="AI API 키를 읽을 수 없습니다. 설정에서 다시 연결해 주세요",
    )


def key_hint(api_key: str) -> str:
    value = validate_api_key(api_key)
    return "••••" + value[-4:]
