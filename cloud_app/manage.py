"""Small administration CLI; secrets are accepted interactively only."""

from __future__ import annotations

import argparse
import getpass
import hmac
from dataclasses import replace

from sqlalchemy import delete, select

from .ai_credentials import decrypt_api_key, encrypt_api_key, validate_api_key
from .config import get_settings
from .credential_store import OCI_KMS_PREFIX
from .database import (
    AiConnection,
    BrowserSession,
    MarketDataConnection,
    SessionLocal,
    User,
    initialize_database,
)
from .market_data_credentials import (
    decrypt_market_credential,
    encrypt_market_credential,
    validate_market_credential,
)
from .security import hash_password, normalize_email


def create_admin(email: str, display_name: str) -> int:
    initialize_database()
    email = normalize_email(email)
    password = getpass.getpass("Admin password (10+ chars): ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match")
    session = SessionLocal()
    try:
        existing = session.scalar(select(User).where(User.email == email))
        if existing:
            existing.role = "admin"
            existing.password_hash = hash_password(password)
            existing.active = True
            session.execute(delete(BrowserSession).where(BrowserSession.user_id == existing.id))
        else:
            session.add(
                User(
                    email=email,
                    display_name=display_name.strip(),
                    password_hash=hash_password(password),
                    role="admin",
                )
            )
        session.commit()
    finally:
        session.close()
    print("Admin account is ready:", email)
    return 0


def _migration_secret(prompt: str) -> str:
    value = getpass.getpass(prompt)
    if len(value) < 32:
        raise SystemExit("Legacy credential roots must contain at least 32 characters")
    return value


def migrate_credentials_to_oci(confirm: str, *, backup_confirmed: bool = False) -> int:
    """Atomically re-encrypt existing local records through OCI Vault KMS."""

    if confirm != "MIGRATE_TO_OCI_KMS":
        raise SystemExit("Pass --confirm MIGRATE_TO_OCI_KMS after stopping app and paper-worker")
    target_settings = get_settings()
    if target_settings.credential_backend != "oci-kms":
        raise SystemExit("CREDENTIAL_BACKEND must be oci-kms")
    if target_settings.ai_credential_secret or target_settings.market_credential_secret:
        raise SystemExit("Remove legacy roots from the process environment; they are prompted securely")

    initialize_database()
    session = SessionLocal()
    try:
        all_ai_rows = [
            row
            for row in session.scalars(select(AiConnection)).all()
            if row.provider != "local" and row.encrypted_api_key
        ]
        ai_rows = [
            row
            for row in all_ai_rows
            if not row.encrypted_api_key.startswith(OCI_KMS_PREFIX)
        ]
        all_market_rows = session.scalars(select(MarketDataConnection)).all()
        market_rows = [
            row
            for row in all_market_rows
            if not (
                row.encrypted_api_key.startswith(OCI_KMS_PREFIX)
                and row.encrypted_api_secret.startswith(OCI_KMS_PREFIX)
            )
        ]
        for row in all_ai_rows:
            if row.encrypted_api_key.startswith(OCI_KMS_PREFIX):
                validate_api_key(
                    decrypt_api_key(
                        row.encrypted_api_key,
                        target_settings,
                        owner_id=row.user_id,
                        provider=row.provider,
                    )
                )
        for row in all_market_rows:
            for attribute, label in (
                ("encrypted_api_key", "App Key"),
                ("encrypted_api_secret", "App Secret"),
            ):
                ciphertext = getattr(row, attribute)
                if ciphertext.startswith(OCI_KMS_PREFIX):
                    validate_market_credential(
                        decrypt_market_credential(
                            ciphertext,
                            target_settings,
                            owner_id=row.user_id,
                            provider=row.provider,
                            environment=row.environment,
                            label=label,
                        ),
                        label,
                    )
        if not ai_rows and not market_rows:
            print("All stored credentials already use OCI Vault KMS")
            return 0
        if not backup_confirmed:
            raise SystemExit(
                "Create and verify a pre-migration database dump, then pass --backup-confirmed"
            )

        needs_ai_root = bool(ai_rows) or any(
            not ciphertext.startswith((OCI_KMS_PREFIX, "v2:"))
            for row in market_rows
            for ciphertext in (row.encrypted_api_key, row.encrypted_api_secret)
        )
        needs_market_root = any(
            ciphertext.startswith("v2:")
            for row in market_rows
            for ciphertext in (row.encrypted_api_key, row.encrypted_api_secret)
        )
        legacy_ai_root = (
            _migration_secret("Legacy AI/shared credential root: ")
            if needs_ai_root
            else "unused-ai-migration-root-00000000"
        )
        legacy_market_root = (
            _migration_secret("Legacy v2 market credential root: ")
            if needs_market_root
            else "unused-market-migration-root-00000"
        )
        legacy_settings = replace(
            target_settings,
            app_env="development",
            credential_backend="local",
            ai_credential_secret=legacy_ai_root,
            market_credential_secret=legacy_market_root,
        )

        migrated_fields = 0
        for row in ai_rows:
            plaintext = decrypt_api_key(
                row.encrypted_api_key,
                legacy_settings,
                owner_id=row.user_id,
                provider=row.provider,
            )
            replacement = encrypt_api_key(
                plaintext,
                target_settings,
                owner_id=row.user_id,
                provider=row.provider,
            )
            if not hmac.compare_digest(
                decrypt_api_key(
                    replacement,
                    target_settings,
                    owner_id=row.user_id,
                    provider=row.provider,
                ),
                plaintext,
            ):
                raise RuntimeError("OCI KMS AI credential verification failed")
            row.encrypted_api_key = replacement
            migrated_fields += 1

        for row in market_rows:
            for attribute, label in (
                ("encrypted_api_key", "App Key"),
                ("encrypted_api_secret", "App Secret"),
            ):
                ciphertext = getattr(row, attribute)
                if ciphertext.startswith(OCI_KMS_PREFIX):
                    continue
                plaintext = decrypt_market_credential(
                    ciphertext,
                    legacy_settings,
                    owner_id=row.user_id,
                    provider=row.provider,
                    environment=row.environment,
                    label=label,
                )
                replacement = encrypt_market_credential(
                    plaintext,
                    label,
                    target_settings,
                    owner_id=row.user_id,
                    provider=row.provider,
                    environment=row.environment,
                )
                if not hmac.compare_digest(
                    decrypt_market_credential(
                        replacement,
                        target_settings,
                        owner_id=row.user_id,
                        provider=row.provider,
                        environment=row.environment,
                        label=label,
                    ),
                    plaintext,
                ):
                    raise RuntimeError("OCI KMS market credential verification failed")
                setattr(row, attribute, replacement)
                migrated_fields += 1
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()
    print("Migrated credential fields to OCI Vault KMS:", migrated_fields)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser("create-admin")
    admin.add_argument("--email", required=True)
    admin.add_argument("--name", required=True)
    migrate = commands.add_parser("migrate-credentials-to-oci")
    migrate.add_argument("--confirm", required=True)
    migrate.add_argument("--backup-confirmed", action="store_true")
    args = parser.parse_args()
    if args.command == "create-admin":
        return create_admin(args.email, args.name)
    if args.command == "migrate-credentials-to-oci":
        return migrate_credentials_to_oci(
            args.confirm, backup_confirmed=args.backup_confirmed
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
