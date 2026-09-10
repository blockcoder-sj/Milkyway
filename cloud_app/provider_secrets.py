"""Broker-only OCI Vault retrieval; never fall back after a denied secret read."""

import base64
from functools import lru_cache
import logging
import multiprocessing
import time

from .config import _weak_secret, valid_vault_secret_id


class ProviderSecretUnavailable(RuntimeError):
    pass


_PURPOSES = {
    "shared_ai": ("oci_shared_ai_secret_id", "shared_ai_api_key"),
    "broker_key": ("oci_broker_api_key_secret_id", "broker_api_key"),
    "broker_secret": ("oci_broker_api_secret_secret_id", "broker_api_secret"),
}


@lru_cache(maxsize=1)
def _client():
    import oci

    logging.getLogger("oci").setLevel(logging.WARNING)
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner(
        retry_strategy=oci.retry.NoneRetryStrategy(),
        federation_client_retry_strategy=oci.retry.NoneRetryStrategy(),
    )
    return oci.secrets.SecretsClient(
        {}, signer=signer, timeout=(3, 10), retry_strategy=oci.retry.NoneRetryStrategy(),
    )


def _delivery_fields(settings, purpose: str) -> tuple[str, str]:
    try:
        identifier_field, local_field = _PURPOSES[purpose]
    except KeyError:
        raise ProviderSecretUnavailable("Unknown provider-secret purpose") from None
    # This guards accidental execution in a client. The actual release boundary
    # is the broker instance principal's restricted Vault IAM policy.
    if settings.service_role != "broker":
        raise ProviderSecretUnavailable("Provider secrets are restricted to the broker")
    identifier = getattr(settings, identifier_field)
    if not valid_vault_secret_id(identifier) or getattr(settings, local_field):
        raise ProviderSecretUnavailable("Invalid provider-secret delivery configuration")
    return identifier, local_field


def _fetch_oci_secret(settings, purpose: str) -> str:
    identifier, _local_field = _delivery_fields(settings, purpose)
    try:
        import oci

        data = _client().get_secret_bundle(
            identifier, stage="CURRENT", retry_strategy=oci.retry.NoneRetryStrategy(),
        ).data
        content = data.secret_bundle_content
        encoded = content.content
        if content.content_type != "BASE64" or not isinstance(encoded, str) or len(encoded) > 5464:
            raise ValueError("invalid bundle")
        decoded = base64.b64decode(encoded, validate=True)
        if len(decoded) > 4096:
            raise ValueError("invalid bundle size")
        value = decoded.decode("utf-8")
        if value != value.strip() or any(ord(char) < 33 or ord(char) > 126 for char in value):
            raise ValueError("invalid key text")
        if _weak_secret(value, 20) or value in (
            settings.credential_broker_app_token, settings.credential_broker_paper_token,
            settings.local_ai_api_key,
        ):
            raise ValueError("invalid key")
        return value
    except Exception:
        # Neither SDK exception text, bundle content nor secret ID reaches logs
        # or HTTP errors. Do not retain or reuse plaintext after a failed fetch.
        raise ProviderSecretUnavailable("OCI provider-secret retrieval failed") from None


def _release_worker(sender, settings, purpose: str) -> None:
    # SDK identity acquisition has hardcoded HTTP timeouts. This isolated child
    # can be terminated even during metadata, certificate or federation refresh.
    logging.disable(logging.CRITICAL)
    try:
        sender.send_bytes(_fetch_oci_secret(settings, purpose).encode("ascii"))
    except Exception:
        sender.send_bytes(b"")
    finally:
        sender.close()


def _run_retrieval(settings, purpose: str, timeout_seconds: float) -> str:
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_release_worker, args=(sender, settings, purpose), daemon=True)
    deadline = time.monotonic() + max(0.0, min(8.0, timeout_seconds))
    try:
        process.start()
        sender.close()
        if not receiver.poll(max(0.0, deadline - time.monotonic())):
            raise ProviderSecretUnavailable("OCI provider-secret retrieval deadline exceeded")
        payload = receiver.recv_bytes(maxlength=4096)
        if not payload:
            raise ProviderSecretUnavailable("OCI provider-secret retrieval failed")
        return payload.decode("ascii")
    except (EOFError, OSError, UnicodeDecodeError):
        raise ProviderSecretUnavailable("OCI provider-secret retrieval failed") from None
    finally:
        receiver.close()
        sender.close()
        if process.pid is not None:
            if process.is_alive():
                process.kill()
            process.join()
            process.close()


def provider_secret(settings, purpose: str, *, timeout_seconds: float = 8.0) -> str:
    if not getattr(settings, "production", False):
        try:
            return getattr(settings, _PURPOSES[purpose][1])
        except KeyError:
            raise ProviderSecretUnavailable("Unknown provider-secret purpose") from None
    _delivery_fields(settings, purpose)
    if timeout_seconds <= 0:
        raise ProviderSecretUnavailable("OCI provider-secret retrieval deadline exceeded")
    return _run_retrieval(settings, purpose, timeout_seconds)


def verify_provider_secret_delivery(settings) -> None:
    if settings.shared_ai_enabled and settings.shared_ai_provider in {"openai", "anthropic"}:
        provider_secret(settings, "shared_ai")
    if settings.quote_provider == "kis":
        key = provider_secret(settings, "broker_key")
        secret = provider_secret(settings, "broker_secret")
        if key == secret:
            raise ProviderSecretUnavailable("Provider credentials must be independent")
