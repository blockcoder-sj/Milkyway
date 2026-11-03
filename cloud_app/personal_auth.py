"""Single-owner, same-origin bootstrap for the loopback personal installation."""

from urllib.parse import urlsplit

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import Settings
from .database import User, quota_allocation


LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def local_login_enabled(settings: Settings) -> bool:
    return (
        getattr(settings, "personal_local_mode", False)
        and getattr(settings, "app_env", None) == "development"
        and getattr(settings, "authority_enabled", True) is False
        and getattr(settings, "credential_backend", None) == "local"
        and getattr(settings, "max_users", None) == 1
        and urlsplit(getattr(settings, "public_base_url", "")).hostname in LOOPBACK_HOSTS
    )


def require_local_request(request: Request, settings: Settings) -> None:
    if not local_login_enabled(settings):
        raise HTTPException(404, "Not found")
    # Docker forwards through its gateway, so the peer IP is not necessarily
    # loopback. Check the browser's exact origin and Host instead. A custom
    # header makes cross-origin requests require a preflight, which we deny.
    expected_origin = f"{request.url.scheme}://{request.url.netloc}"
    if (
        request.url.hostname not in LOOPBACK_HOSTS
        or request.headers.get("origin") != expected_origin
        or request.headers.get("x-milkyway-local") != "1"
        or request.headers.get("sec-fetch-site", "same-origin") != "same-origin"
    ):
        raise HTTPException(403, "로컬 앱 화면에서 접속해 주세요")


def local_owner(session: Session) -> User:
    # Share the registration admission lock with ordinary account creation.
    with quota_allocation(session, "registration", "global"):
        owners = session.scalars(select(User).limit(2)).all()
        if len(owners) > 1:
            raise HTTPException(409, "계정이 여러 개여서 자동으로 선택할 수 없습니다")
        if owners:
            owner = owners[0]
            if not owner.active:
                raise HTTPException(403, "비활성 로컬 계정입니다")
        else:
            owner = User(
                email="local@milkyway.invalid",
                display_name="내 로컬 계정",
                # No shared/default password; ordinary password verification
                # always rejects this deliberately unusable hash.
                password_hash="!local-only",
                role="member",
            )
            session.add(owner)
        session.commit()
        return owner
