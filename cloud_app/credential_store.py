"""Shared encryption primitive for member-owned provider credentials."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
from functools import lru_cache
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.fernet import Fernet

from .config import ROOT, Settings, get_settings


OCI_KMS_PREFIX = "v3:oci-kms:"
LOCAL_PREFIX = "v2:"
# OCI debug HTTP logging can include cryptographic request bodies. Credential
# operations therefore never inherit an application-wide DEBUG log level.
logging.getLogger("oci").setLevel(logging.WARNING)


def _credential_backend(settings: Settings) -> str:
    backend = getattr(settings, "credential_backend", "local") or "local"
    if backend not in {"local", "oci-kms", "broker"}:
        raise RuntimeError("Unsupported credential encryption backend")
    if bool(getattr(settings, "production", False)) and backend not in {"oci-kms", "broker"}:
        raise RuntimeError("Production credentials require an external credential service")
    return backend


def _master_secret(settings: Settings, purpose: str) -> str:
    if purpose not in {"ai", "market"}:
        raise ValueError("Unsupported credential purpose")
    production = bool(getattr(settings, "production", False))
    configured = (
        settings.ai_credential_secret
        if purpose == "ai"
        else getattr(settings, "market_credential_secret", "")
    )
    if configured:
        return configured
    if production:
        variable = "AI_CREDENTIAL_SECRET" if purpose == "ai" else "MARKET_CREDENTIAL_SECRET"
        raise RuntimeError("{} is required in production".format(variable))
    path = Path(ROOT) / "runtime/.{}_credential_secret".format(purpose)
    try:
        value = path.read_text(encoding="utf-8").strip()
        if len(value) >= 32:
            os.chmod(path.parent, 0o700)
            os.chmod(path, 0o600)
            return value
    except FileNotFoundError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
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


def _legacy_fernet(settings: Settings | None = None) -> Fernet:
    settings = settings or get_settings()
    secret = _master_secret(settings, "ai")
    # Keep the original derivation label so existing encrypted AI keys remain readable.
    material = hashlib.sha256(("milkyway-ai-credential:" + secret).encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(material))


def _context_fields(purpose: str, owner_id: str, field: str, version: int) -> dict[str, str]:
    if purpose not in {"ai", "market"}:
        raise ValueError("Unsupported credential purpose")
    if not owner_id or len(owner_id) > 128 or not field or len(field) > 128:
        raise ValueError("Credential context is invalid")
    return {
        "field": field,
        "owner": owner_id,
        "purpose": purpose,
        "version": str(version),
    }


def _context(purpose: str, owner_id: str, field: str) -> bytes:
    return json.dumps(
        _context_fields(purpose, owner_id, field, 2),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _context_key(settings: Settings, purpose: str, context: bytes) -> bytes:
    master = _master_secret(settings, purpose).encode("utf-8")
    return hmac.new(master, b"milkyway-credential-v2\0" + context, hashlib.sha256).digest()


def _oci_key_id(settings: Settings, purpose: str) -> str:
    if purpose not in {"ai", "market"}:
        raise ValueError("Unsupported credential purpose")
    key_id = (
        getattr(settings, "oci_ai_credential_key_id", "")
        if purpose == "ai"
        else getattr(settings, "oci_market_credential_key_id", "")
    )
    if not key_id.startswith("ocid1.key."):
        raise RuntimeError("OCI Vault credential key is not configured")
    return key_id


@lru_cache(maxsize=4)
def _oci_kms_client(endpoint: str):
    if not endpoint.startswith("https://"):
        raise RuntimeError("OCI KMS cryptographic endpoint is not configured")
    try:
        import oci
    except ImportError as exc:  # pragma: no cover - production image installs the SDK
        raise RuntimeError("OCI SDK is unavailable") from exc
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    return oci.key_management.KmsCryptoClient(
        config={},
        service_endpoint=endpoint,
        signer=signer,
        retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY,
        timeout=(5, 20),
    )


def _encrypt_with_oci_kms(
    value: str,
    settings: Settings,
    purpose: str,
    owner_id: str,
    field: str,
) -> str:
    import oci

    endpoint = getattr(settings, "oci_kms_crypto_endpoint", "")
    details = oci.key_management.models.EncryptDataDetails(
        key_id=_oci_key_id(settings, purpose),
        plaintext=base64.b64encode(value.encode("utf-8")).decode("ascii"),
        associated_data=_context_fields(purpose, owner_id, field, 3),
        encryption_algorithm="AES_256_GCM",
        logging_context={"application": "milkyway", "purpose": purpose},
    )
    response = _oci_kms_client(endpoint).encrypt(details)
    ciphertext = getattr(response.data, "ciphertext", "")
    if not ciphertext or len(ciphertext) > 16_384:
        raise RuntimeError("OCI KMS returned an invalid credential ciphertext")
    return OCI_KMS_PREFIX + ciphertext


def _decrypt_with_oci_kms(
    ciphertext: str,
    settings: Settings,
    purpose: str,
    owner_id: str,
    field: str,
) -> str:
    import oci

    payload = ciphertext[len(OCI_KMS_PREFIX) :]
    if not payload or len(payload) > 16_384:
        raise ValueError("credential ciphertext is invalid")
    endpoint = getattr(settings, "oci_kms_crypto_endpoint", "")
    details = oci.key_management.models.DecryptDataDetails(
        key_id=_oci_key_id(settings, purpose),
        ciphertext=payload,
        associated_data=_context_fields(purpose, owner_id, field, 3),
        encryption_algorithm="AES_256_GCM",
        logging_context={"application": "milkyway", "purpose": purpose},
    )
    response = _oci_kms_client(endpoint).decrypt(details)
    plaintext = getattr(response.data, "plaintext", "")
    if not plaintext or len(plaintext) > 4096:
        raise ValueError("credential plaintext is invalid")
    return base64.b64decode(plaintext.encode("ascii"), validate=True).decode("utf-8")


def credential_ciphertext_prefix(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    return OCI_KMS_PREFIX if _credential_backend(settings) in {"oci-kms", "broker"} else LOCAL_PREFIX


def encrypt_credential(
    value: str,
    settings: Settings | None = None,
    *,
    purpose: str = "ai",
    owner_id: str = "legacy-unscoped",
    field: str = "api-key",
) -> str:
    settings = settings or get_settings()
    backend = _credential_backend(settings)
    if backend == "broker":
        raise RuntimeError("Credential encryption is restricted to the credential broker")
    if backend == "oci-kms":
        try:
            return _encrypt_with_oci_kms(value, settings, purpose, owner_id, field)
        except Exception as exc:
            raise RuntimeError(
                "Credential encryption service is unavailable ({})".format(
                    type(exc).__name__
                )
            ) from None
    context = _context(purpose, owner_id, field)
    nonce = os.urandom(12)
    encrypted = AESGCM(_context_key(settings, purpose, context)).encrypt(
        nonce, value.encode("utf-8"), context
    )
    return LOCAL_PREFIX + base64.urlsafe_b64encode(nonce + encrypted).decode("ascii")


def decrypt_credential(
    ciphertext: str,
    settings: Settings | None = None,
    *,
    purpose: str = "ai",
    owner_id: str = "legacy-unscoped",
    field: str = "api-key",
    error_message: str = "저장된 자격증명을 읽을 수 없습니다. 설정에서 다시 연결해 주세요",
) -> str:
    settings = settings or get_settings()
    try:
        backend = _credential_backend(settings)
        if backend == "broker":
            raise RuntimeError("Credential decryption is restricted to the credential broker")
        if ciphertext.startswith(OCI_KMS_PREFIX):
            if backend != "oci-kms":
                raise RuntimeError("OCI KMS credential backend is not configured")
            return _decrypt_with_oci_kms(ciphertext, settings, purpose, owner_id, field)
        if backend != "local":
            raise RuntimeError("Legacy credentials require offline migration")
        if not ciphertext.startswith(LOCAL_PREFIX):
            return _legacy_fernet(settings).decrypt(ciphertext.encode("ascii")).decode("utf-8")
        context = _context(purpose, owner_id, field)
        raw = base64.urlsafe_b64decode(ciphertext[len(LOCAL_PREFIX) :].encode("ascii"))
        if len(raw) < 29:
            raise ValueError("credential ciphertext is too short")
        return AESGCM(_context_key(settings, purpose, context)).decrypt(
            raw[:12], raw[12:], context
        ).decode("utf-8")
    except Exception:
        raise RuntimeError(error_message) from None


def validate_credential_backend(
    settings: Settings | None = None, *, purposes: tuple[str, ...] = ("ai", "market")
) -> None:
    """Prove configured KMS encrypt/decrypt access without persisting a credential."""

    settings = settings or get_settings()
    if _credential_backend(settings) != "oci-kms":
        return
    for purpose in purposes:
        value = secrets.token_urlsafe(32)
        ciphertext = encrypt_credential(
            value,
            settings,
            purpose=purpose,
            owner_id="deployment-preflight",
            field="kms-round-trip",
        )
        recovered = decrypt_credential(
            ciphertext,
            settings,
            purpose=purpose,
            owner_id="deployment-preflight",
            field="kms-round-trip",
        )
        if not hmac.compare_digest(value, recovered):
            raise RuntimeError("Credential KMS round trip did not preserve plaintext")
