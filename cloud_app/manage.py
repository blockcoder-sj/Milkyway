"""Small administration CLI; secrets are accepted interactively only."""

from __future__ import annotations

import argparse
import getpass

from sqlalchemy import select

from .database import SessionLocal, User, initialize_database
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


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    admin = commands.add_parser("create-admin")
    admin.add_argument("--email", required=True)
    admin.add_argument("--name", required=True)
    args = parser.parse_args()
    if args.command == "create-admin":
        return create_admin(args.email, args.name)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
