"""Reproducible candidate experiments and evidence for the approved chat."""
from __future__ import annotations

import datetime as dt
import json
import math
import re
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from .bounded_io import read_bounded_file
from .database import BacktestJob, EquityPoint, PaperAccount, PaperFill, Strategy, quota_allocation, utcnow
from .research_models import ResearchDeployment, ResearchExperiment, ResearchRun
from .strategies import StrategySpec, get_dataset_bundle, run_strategy_backtest, validate_auto_backtest_history


class ExperimentBody(BaseModel):
    request_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{8,64}$")
    strategy_ids: list[str] = Field(min_length=1, max_length=4)
    start_date: dt.date
    split_date: dt.date
    end_date: dt.date
    objective: Literal["sharpe", "return_pct", "mdd_pct"] = "sharpe"


class DeployBody(BaseModel):
    strategy_id: str
    request_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{8,64}$")
    name: str = Field(min_length=2, max_length=100)


def experiment_payload(db, experiment):
    rows = db.execute(select(ResearchRun, BacktestJob).join(BacktestJob, BacktestJob.id == ResearchRun.job_id)
                      .where(ResearchRun.experiment_id == experiment.id)).all()
    candidates = {}
    states = []
    for run, job in rows:
        result = json.loads(job.result_json) if job.result_json else {}
        consistent = not result or result.get("dataset_fingerprint") == experiment.fingerprint
        state = job.status if consistent else "failed"
        states.append(state)
        candidates.setdefault(run.strategy_id, {"strategy_id": run.strategy_id})[run.segment] = {
            "job_id": job.id, "status": state, "metrics": result.get("metrics") if consistent else None,
            "error": job.error if consistent else "비교 데이터 지문이 달라 결과를 사용할 수 없습니다"}
    status = "failed" if "failed" in states else "completed" if states and all(s == "completed" for s in states) else "running"
    ranked = []
    if status == "completed":
        for candidate in candidates.values():
            metrics = candidate.get("development", {}).get("metrics") or {}
            value = metrics.get(experiment.objective)
            if isinstance(value, (int, float)) and math.isfinite(value) and metrics.get("trade_count", 0) > 0:
                ranked.append((float(value), candidate["strategy_id"]))
    return {"id": experiment.id, "objective": experiment.objective, "status": status,
            "start_date": str(experiment.start_date), "split_date": str(experiment.split_date), "end_date": str(experiment.end_date),
            "dataset_fingerprint": experiment.fingerprint, "candidates": list(candidates.values()),
            "development_leader": max(ranked)[1] if ranked else None,
            "caveat": "개발 구간 기준 후보 순위입니다. 검증 구간은 별도 초기자금으로 실행합니다. 반복해서 본 검증 결과는 최종 미사용 데이터가 아닙니다."}


def enqueue_experiment(db, user, room, body, settings, allowed_ids):
    canonical = body.model_dump_json()
    with quota_allocation(db, "backtests", "global"), quota_allocation(db, "backtests", user.id):
        existing = db.scalar(select(ResearchExperiment).where(ResearchExperiment.session_id == room.id,
                                                              ResearchExperiment.request_id == body.request_id))
        if existing:
            if existing.request_json != canonical:
                raise HTTPException(409, "같은 실험 요청 ID의 조건이 다릅니다")
            return experiment_payload(db, existing)
        if len(set(body.strategy_ids)) != len(body.strategy_ids) or not set(body.strategy_ids) <= allowed_ids:
            raise HTTPException(422, "이 연구의 서로 다른 전략 버전을 선택하세요")
        if not body.start_date < body.split_date < body.end_date or (body.end_date - body.start_date).days > 370:
            raise HTTPException(422, "시작일 < 검증 시작일 < 종료일, 전체 370일 이내로 설정하세요")
        if min((body.split_date - body.start_date).days, (body.end_date - body.split_date).days) < 30:
            raise HTTPException(422, "개발·검증 구간은 각각 최소 30일이어야 합니다")
        count = len(body.strategy_ids) * 2
        since = dt.datetime.combine(utcnow().date(), dt.time.min, tzinfo=dt.timezone.utc)
        daily = db.scalar(select(func.count()).select_from(BacktestJob).where(BacktestJob.user_id == user.id, BacktestJob.created_at >= since))
        active = BacktestJob.status.in_(["queued", "running"])
        outstanding = db.scalar(select(func.count()).select_from(BacktestJob).where(BacktestJob.user_id == user.id, active))
        total = db.scalar(select(func.count()).select_from(BacktestJob).where(active))
        if daily + count > settings.max_backtests_per_user_day or outstanding + count > settings.max_outstanding_backtests_per_user or total + count > settings.max_outstanding_backtests_total:
            raise HTTPException(429, "백테스트 대기열 또는 일일 한도입니다. 실행 중인 작업이 끝난 뒤 후보를 줄여 다시 시도하세요")
        try:
            candidates = [db.scalar(select(Strategy).where(Strategy.id == i, Strategy.user_id == user.id)) for i in body.strategy_ids]
            if any(row is None for row in candidates):
                raise ValueError("missing strategy")
            candidate_specs = [StrategySpec.model_validate_json(row.spec_json) for row in candidates]
            if len({spec.universe for spec in candidate_specs}) != 1:
                raise HTTPException(422, "같은 선정 범위의 전략끼리 비교하세요")
            dataset_settings = settings
            if candidate_specs[0].universe == "us_all":
                from .auto_universe import backtest_settings, prepare_backtest_generation
                prepare_backtest_generation(settings)
                dataset_settings = backtest_settings(settings)
            bundle = get_dataset_bundle(dataset_settings)
            specs = []
            for strategy_id in body.strategy_ids:
                strategy = db.scalar(select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == user.id))
                if strategy is None:
                    raise ValueError("missing strategy")
                spec = StrategySpec.model_validate_json(strategy.spec_json)
                validate_auto_backtest_history(spec, bundle, body.start_date.isoformat())
                needed = max(spec.filters.history_days, *(factor.lookback + 1 for factor in spec.factors))
                for symbol in spec.symbols:
                    frame = bundle.data.get(symbol)
                    if frame is None or frame.index.max().date() < body.end_date or len(frame.loc[frame.index.date < body.start_date]) < needed:
                        raise ValueError("insufficient history")
                specs.append(spec)
            if len({(spec.portfolio.initial_cash, spec.portfolio.cost_per_side) for spec in specs}) != 1:
                raise HTTPException(422, "공정한 비교를 위해 후보의 초기자금과 편도 비용을 같게 설정하세요")
            if body.end_date > bundle.index.max().date():
                raise ValueError("future end")
            generation = bundle.settings.dataset_dir.name
            if not re.fullmatch(r"[0-9a-f]{32}", generation):
                raise ValueError("generation not captured")
            events = read_bounded_file(settings.terminal_events_path, maximum_bytes=1024*1024, allow_empty=True).decode() if settings.terminal_events_path.exists() else ""
        except (OSError, ValueError, RuntimeError):
            raise HTTPException(409, "선택 종목의 가격 이력과 준비 기간이 부족합니다. 데이터 준비 후 시작일·종료일을 확인하세요") from None
        experiment = ResearchExperiment(session_id=room.id, request_id=body.request_id, request_json=canonical,
            objective=body.objective, start_date=body.start_date, split_date=body.split_date, end_date=body.end_date,
            generation=generation, fingerprint=bundle.fingerprint, terminal_events=events)
        db.add(experiment); db.flush()
        for strategy_id in body.strategy_ids:
            for segment, start, end in (("development", body.start_date, body.split_date-dt.timedelta(days=1)),
                                        ("validation", body.split_date, body.end_date)):
                job = BacktestJob(user_id=user.id, strategy_id=strategy_id, start_date=start, end_date=end, bias_mode="exploratory")
                db.add(job); db.flush()
                db.add(ResearchRun(job_id=job.id, experiment_id=experiment.id, strategy_id=strategy_id, segment=segment))
        db.commit()
        return experiment_payload(db, experiment)


def run_pinned_backtest(spec, arguments, experiment, settings):
    # Generation names are server-produced; never accept arbitrary paths from a request.
    if not re.fullmatch(r"[0-9a-f]{32}", experiment.generation):
        raise ValueError("invalid research generation")
    if spec.universe == "us_all":
        from .auto_universe import backtest_settings
        settings = backtest_settings(settings)
    root = settings.dataset_dir / "generations"
    generation = root / experiment.generation
    if generation.is_symlink() or generation.resolve().parent != root.resolve():
        raise ValueError("unsafe research generation")
    with tempfile.TemporaryDirectory(prefix="milkyway-research-events-") as directory:
        events = Path(directory) / "events.jsonl"
        if experiment.terminal_events:
            events.write_text(experiment.terminal_events, encoding="utf-8")
        captured = replace(settings, dataset_dir=generation, snapshots_glob=str(generation / "snapshots/*.json"), terminal_events_path=events)
        if get_dataset_bundle(captured).fingerprint != experiment.fingerprint:
            raise ValueError("research dataset changed")
        result = run_strategy_backtest(spec, **arguments, settings=captured)
        if result["dataset_fingerprint"] != experiment.fingerprint:
            raise ValueError("research dataset changed during execution")
        return result


def experiment_evidence(db, room):
    rows = db.scalars(select(ResearchExperiment).where(ResearchExperiment.session_id == room.id)
                      .order_by(ResearchExperiment.created_at.desc()).limit(3)).all()
    accounts = db.execute(select(ResearchDeployment, PaperAccount).join(PaperAccount, PaperAccount.id == ResearchDeployment.account_id)
        .where(ResearchDeployment.session_id == room.id, PaperAccount.user_id == room.user_id)).all()
    paper = []
    for deployment, account in accounts:
        latest = db.scalar(select(EquityPoint).where(EquityPoint.account_id == account.id).order_by(EquityPoint.observed_at.desc()).limit(1))
        fills = db.scalars(select(PaperFill).where(PaperFill.account_id == account.id).order_by(PaperFill.executed_at.desc()).limit(5)).all()
        paper.append({"account_id": account.id, "strategy_id": deployment.strategy_id, "status": account.status,
                      "initial_cash": account.initial_cash, "cash": account.cash,
                      "last_equity": latest.equity if latest else None, "observed_at": str(latest.observed_at) if latest else None,
                      "recent_fills": [{"symbol": f.ticker, "side": f.side, "price": f.price, "shares": f.shares,
                                        "reason": f.reason, "at": str(f.executed_at)} for f in fills]})
    return {"experiments": [experiment_payload(db, row) for row in rows], "paper": paper}
