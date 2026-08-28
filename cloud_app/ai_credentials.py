"""Encryption and validation for user-owned AI provider credentials."""

from __future__ import annotations

import base64
import hashlib
import re

from cryptography.fernet import Fernet, InvalidToken

from .config import Settings, get_settings


PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "default_model": "gpt-5.6-luna",
        "model_examples": ["gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol"],
    },
    "anthropic": {
        "label": "Anthropic",
        "default_model": "claude-sonnet-4-20250514",
        "model_examples": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"],
    },
}
_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,99}$")


def provider_catalog() -> list[dict]:
    return [
        {
            "id": provider,
            "label": details["label"],
            "default_model": details["default_model"],
            "model_examples": details["model_examples"],
        }
        for provider, details in PROVIDERS.items()
    ]


def validate_provider_model(provider: str, model: str) -> tuple[str, str]:
    provider = provider.strip().lower()
    model = model.strip()
    if provider not in PROVIDERS:
        raise ValueError("지원하지 않는 AI 공급자입니다")
    if not _MODEL_PATTERN.fullmatch(model):
        raise ValueError("모델 ID 형식이 올바르지 않습니다")
    return provider, model


def validate_api_key(api_key: str) -> str:
    value = api_key.strip()
    if len(value) < 20 or len(value) > 512 or any(character.isspace() for character in value):
        raise ValueError("API 키 형식이 올바르지 않습니다")
    return value


def _fernet(settings: Settings | None = None) -> Fernet:
    settings = settings or get_settings()
    secret = settings.ai_credential_secret or settings.session_secret
    material = hashlib.sha256(("milkyway-ai-credential:" + secret).encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(material))


def encrypt_api_key(api_key: str, settings: Settings | None = None) -> str:
    return _fernet(settings).encrypt(validate_api_key(api_key).encode("utf-8")).decode("ascii")


def decrypt_api_key(ciphertext: str, settings: Settings | None = None) -> str:
    try:
        return _fernet(settings).decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeError) as exc:
        raise RuntimeError("AI API 키를 읽을 수 없습니다. 설정에서 다시 연결해 주세요") from exc


def key_hint(api_key: str) -> str:
    value = validate_api_key(api_key)
    return "••••" + value[-4:]
