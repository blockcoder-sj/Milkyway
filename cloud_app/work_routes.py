"""Only a trusted schedule can issue provider and worker capabilities."""

import json

from fastapi import Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, SecretStr

from .database import MarketDataConnection, SessionLocal, quota_allocation
from .paper import store_member_quotes
from .work_authority import (
    claim_record, complete_work, consume_quote_work, credential_version, issue_work,
)


class EmptyBody(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClaimBody(EmptyBody):
    claim: SecretStr = Field(min_length=43, max_length=43)


def install_work_routes(app, settings, paper_identity, backtest_identity, fetch_quotes, cipher_body, quote_slots, safe_failure):
    if not settings.authority_enabled:
        return

    def install_claims(service, identity):
        @app.post("/v1/work/" + service + "/next", dependencies=[Depends(identity)])
        def next_work(_body: EmptyBody):
            with SessionLocal() as session:
                return {"work": issue_work(session, settings, service)}

        @app.post("/v1/work/" + service + "/complete", dependencies=[Depends(identity)])
        def complete(body: ClaimBody):
            with SessionLocal() as session:
                complete_work(session, body.claim.get_secret_value(), service)
            return {"status": "ok"}

    install_claims("paper", paper_identity)
    install_claims("backtest", backtest_identity)

    @app.post("/v1/work/paper/quotes", dependencies=[Depends(paper_identity)])
    def quotes(body: ClaimBody):
        if not quote_slots.acquire(blocking=False):
            raise HTTPException(429, "시세 처리 용량이 사용 중입니다")
        try:
            with SessionLocal() as session:
                claim = consume_quote_work(session, settings, body.claim.get_secret_value())
                row = session.get(MarketDataConnection, claim.user_id)
                # No caller-supplied owner, ciphertext, provider or symbols.
                credential = cipher_body(owner_id=claim.user_id, provider=row.provider, environment=row.environment,
                    encrypted_api_key=row.encrypted_api_key, encrypted_api_secret=row.encrypted_api_secret)
                tickers = tuple(json.loads(claim.tickers_json))
                version, user_id = claim.credential_version, claim.user_id
                session.rollback()
                values = fetch_quotes(credential, tickers) if tickers else []
                with quota_allocation(session, "market-connection", user_id):
                    session.expire_all()
                    claim_record(session, body.claim.get_secret_value(), "paper")
                    current = session.get(MarketDataConnection, user_id, populate_existing=True)
                    if credential_version(current) != version:
                        raise HTTPException(409, "시세 수집 중 증권사 연결이 변경되었습니다")
                    count = store_member_quotes(session, user_id, values)
                    session.commit()
                return {"status": "ok", "count": count}
        except Exception as exc:
            raise safe_failure(exc) from None
        finally:
            quote_slots.release()
