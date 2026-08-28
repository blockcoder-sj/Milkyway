"""Encryption and validation for user-owned AI provider credentials."""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from .config import AI_MODEL_PATTERN, ROOT, Settings, get_settings


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


def _master_secret(settings: Settings) -> str:
    if settings.ai_credential_secret:
        return settings.ai_credential_secret
    if settings.production:
        raise RuntimeError("AI_CREDENTIAL_SECRET is required in production")
    path = Path(ROOT) / "runtime/.ai_credential_secret"
    try:
        value = path.read_text(encoding="utf-8").strip()
        if len(value) >= 32:
            return value
    except FileNotFoundError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    value = secrets.token_urlsafe(48)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
        return value
    except FileExistsError:
        existing = path.read_text(encoding="utf-8").strip()
        if len(existing) < 32:
            raise RuntimeError("Local AI credential secret is invalid")
        return existing


def _fernet(settings: Settings | None = None) -> Fernet:
    settings = settings or get_settings()
    secret = _master_secret(settings)
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
