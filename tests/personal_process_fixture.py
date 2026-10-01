"""Isolated process boundary for native integration checks; all provider data is synthetic."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import socket
from unittest.mock import patch


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=("app", "paper", "backtest", "personal-data", "company-data", "seed"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--port", type=int, default=8768)
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / "OFFLINE_TEST_ONLY").is_file():
        raise SystemExit("Requires a fresh offline fixture root")
    # Patch configuration before any application module obtains settings.
    from cloud_app import config
    config.ROOT = root
    config.get_settings.cache_clear()

    def local(host):
        if host in (None, "localhost", "testserver"):
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False

    original_resolve, original_connect = socket.getaddrinfo, socket.socket.connect

    def resolve(host, *positional, **keywords):
        if not local(host):
            raise RuntimeError("Offline fixture blocked external network")
        return original_resolve(host, *positional, **keywords)

    def connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6) and not local(address[0]):
            raise RuntimeError("Offline fixture blocked external network")
        return original_connect(sock, address)

    from cloud_app import personal_data, research_ai
    from tests.test_personal_data import write_outcome

    def synthetic_reply(request, key):
        with (root / "synthetic-ai-calls.jsonl").open("a") as log:
            log.write(json.dumps({"model": request["model"], "synthetic": True}) + "\n")
        return {"reply": {"reply": "합성 검증용 전략", "strategy": {
            "name": "Offline research", "symbols": ["AAPL", "MSFT"],
            "factors": [{"kind": "momentum"}], "portfolio": {"max_positions": 2}}},
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}}

    with patch.object(socket, "getaddrinfo", resolve), patch.object(socket.socket, "connect", connect), \
         patch.object(personal_data._history_process, "run", side_effect=write_outcome), \
         patch.object(research_ai, "invoke_approved", side_effect=synthetic_reply):
        if args.role == "app":
            import uvicorn
            from cloud_app.main import app
            uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
        elif args.role == "seed":
            result = personal_data.refresh_personal_data(["AAPL", "MSFT"], config.get_settings())
            assert result["ready"], result
        elif args.role == "company-data":
            from cloud_app import company_worker
            from cloud_app.company_schemas import CompanyKnowledge
            from cloud_app.database import utcnow
            def synthetic_company(payload, configuration, deadline):
                relations = [dict(name="Offline private subsidiary", entity_id="Q123",
                    kind="subsidiary", source=dict(label="Offline fixture statement",
                    url="https://example.test/company-report", level="primary"))] if payload["symbol"] else []
                return CompanyKnowledge(symbol=payload["symbol"], entity_id=payload.get("entity_id"), name=payload["name"],
                    relations=relations, description="Synthetic offline company collection", fetched_at=utcnow()).model_dump(mode="json")
            with patch.object(company_worker._provider, "run", side_effect=synthetic_company):
                company_worker.main()
        else:
            os.environ["WORKER_ROLE"] = args.role
            from cloud_app.worker import main
            main()


if __name__ == "__main__":
    run()
