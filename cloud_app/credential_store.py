"""Shared encryption primitive for member-owned provider credentials."""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from .config import ROOT, Settings, get_settings


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
            raise RuntimeError("Local credential secret is invalid")
        return existing


def _fernet(settings: Settings | None = None) -> Fernet:
    settings = settings or get_settings()
    secret = _master_secret(settings)
    # Keep the original derivation label so existing encrypted AI keys remain readable.
    material = hashlib.sha256(("milkyway-ai-credential:" + secret).encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(material))


def encrypt_credential(value: str, settings: Settings | None = None) -> str:
    return _fernet(settings).encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_credential(
    ciphertext: str,
    settings: Settings | None = None,
    *,
    error_message: str = "저장된 자격증명을 읽을 수 없습니다. 설정에서 다시 연결해 주세요",
) -> str:
    try:
        return _fernet(settings).decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError, UnicodeError) as exc:
        raise RuntimeError(error_message) from exc
