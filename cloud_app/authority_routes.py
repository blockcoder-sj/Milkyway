"""Routes hosted only by the independent credential broker."""

from pathlib import Path

from fastapi import Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy import delete

from . import authority
from .database import MarketDataConnection, MemberQuote, SessionLocal, quota_allocation, utcnow
from .market_data_credentials import provider_catalog


class StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginBody(StrictBody):
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)


class RegisterBody(LoginBody):
    display_name: str = Field(min_length=2, max_length=60)
    invite_code: SecretStr = Field(min_length=20, max_length=256)


class SessionBody(StrictBody):
    session_token: SecretStr = Field(min_length=43, max_length=43)
    csrf: SecretStr = Field(min_length=1, max_length=64)


class AiPermitBody(SessionBody):
    prompt: str = Field(min_length=5, max_length=3000)
    nonce: str = Field(pattern=r"^[A-Za-z0-9_-]{32,64}$")


class MarketBody(StrictBody):
    provider: str = Field(min_length=2, max_length=30)
    environment: str = Field(min_length=2, max_length=20)
    api_key: SecretStr = Field(min_length=1, max_length=4096)
    api_secret: SecretStr = Field(min_length=1, max_length=4096)


def install_authority_routes(app, settings, app_identity, market_prepare, market_body):
    if not settings.authority_enabled:
        return

    def db():
        with SessionLocal() as session:
            yield session

    def browser_origin(request: Request):
        if request.headers.get("origin") != settings.public_base_url.rstrip("/"):
            raise HTTPException(403, "요청 출처가 올바르지 않습니다")

    def browser_member(request: Request, session):
        return authority.principal(
            session, request.cookies.get("__Host-credential-session" if settings.production else "credential-session", ""),
            request.headers.get("X-CSRF-Token", ""),
        )[0]

    def login_values(body, session):
        return authority.login_member(session, settings, email=body.email, password=body.password.get_secret_value())

    @app.post("/v1/auth/login", dependencies=[Depends(app_identity)])
    def login(body: LoginBody, session=Depends(db)):
        return login_values(body, session)

    @app.post("/v1/auth/register", dependencies=[Depends(app_identity)])
    def register(body: RegisterBody, session=Depends(db)):
        return authority.register_member(
            session, settings, email=body.email, display_name=body.display_name,
            password=body.password.get_secret_value(), invite_code=body.invite_code.get_secret_value(),
        )

    @app.post("/v1/auth/logout", dependencies=[Depends(app_identity)])
    def logout(body: SessionBody, session=Depends(db)):
        authority.revoke_session(session, body.session_token.get_secret_value(), body.csrf.get_secret_value())
        return {"status": "ok"}

    @app.post("/v1/permits/shared-ai", dependencies=[Depends(app_identity)])
    def permit(body: AiPermitBody, session=Depends(db)):
        return {"permit": authority.issue_ai_permit(
            session, settings, raw_token=body.session_token.get_secret_value(),
            csrf=body.csrf.get_secret_value(), prompt=body.prompt, nonce=body.nonce,
        )}

    @app.get("/credentials")
    def credential_page():
        return FileResponse(Path(__file__).with_name("credential_static") / "index.html", headers={"Cache-Control": "no-store"})

    @app.get("/credentials.js")
    def credential_script():
        return FileResponse(Path(__file__).with_name("credential_static") / "app.js", media_type="text/javascript")

    @app.get("/credentials/providers")
    def credential_providers():
        return {"providers": provider_catalog()}

    @app.post("/credentials/login", dependencies=[Depends(browser_origin)])
    def browser_login(body: LoginBody, response: Response, session=Depends(db)):
        result = login_values(body, session)
        response.set_cookie(
            "__Host-credential-session" if settings.production else "credential-session", result.pop("session_token"),
            max_age=settings.session_hours * 3600, httponly=True, secure=settings.production,
            samesite="strict", path="/",
        )
        return result

    @app.post("/credentials/logout", dependencies=[Depends(browser_origin)])
    def browser_logout(request: Request, response: Response, session=Depends(db)):
        name = "__Host-credential-session" if settings.production else "credential-session"
        authority.revoke_session(session, request.cookies.get(name, ""), request.headers.get("X-CSRF-Token", ""))
        response.delete_cookie(name, path="/", secure=settings.production, httponly=True, samesite="strict")
        return {"status": "ok"}

    @app.put("/credentials/market", dependencies=[Depends(browser_origin)])
    def save_market(body: MarketBody, request: Request, session=Depends(db)):
        user = browser_member(request, session)
        authority.consume_budget(session, settings, "market-save", user.id, 10, 3600)
        # Provider verification must not hold a DB transaction/lock while the
        # remote operation runs. The browser identity is rechecked afterward.
        result = market_prepare(market_body(
            owner_id=user.id, provider=body.provider, environment=body.environment,
            api_key=body.api_key, api_secret=body.api_secret,
        ), _identity="trusted-browser")
        with quota_allocation(session, "market-connection", user.id):
            session.expire_all()
            browser_member(request, session)
            row = session.get(MarketDataConnection, user.id)
            if row is None:
                row = MarketDataConnection(user_id=user.id)
            row.provider, row.environment = body.provider.strip().lower(), body.environment.strip().lower()
            for field in ("encrypted_api_key", "encrypted_api_secret", "key_hint", "secret_hint"):
                setattr(row, field, result[field])
            row.verified_at = row.updated_at = utcnow()
            session.add(row)
            session.execute(delete(MemberQuote).where(MemberQuote.user_id == user.id))
            session.commit()
            return {"status": "ok", "provider": row.provider, "environment": row.environment, "key_hint": row.key_hint}

    @app.delete("/credentials/market", dependencies=[Depends(browser_origin)])
    def delete_market(request: Request, session=Depends(db)):
        user = browser_member(request, session)
        with quota_allocation(session, "market-connection", user.id):
            session.execute(delete(MemberQuote).where(MemberQuote.user_id == user.id))
            session.execute(delete(MarketDataConnection).where(MarketDataConnection.user_id == user.id))
            session.commit()
        return {"status": "ok"}
