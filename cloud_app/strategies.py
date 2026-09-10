"""Safe strategy DSL compiled into the one canonical accounting engine.

AI output is data, never executable Python.  Every strategy produces a score
matrix and then delegates fills, stops, fees and rebalancing to backtest_core.
"""

from __future__ import annotations

import glob
import datetime as dt
import json
import threading
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backtest_core import run_backtest
from market_calendar import next_trading_day
from price_data_pipeline import (
    MAX_DATASET_COMPRESSED_BYTES,
    MAX_PRICE_FILE_BYTES,
    MAX_DATASET_ROWS,
    MAX_DATASET_UNCOMPRESSED_BYTES,
    build_strategy_eligibility_mask,
    assert_manifest_generation,
    load_price_dataset,
    load_manifest_snapshot,
    price_file_path,
    read_price_frame,
    require_price_manifest,
    validate_dataset_inventory,
)
from terminal_events import effective_verified_events, load_events
from universe_snapshot import (
    SnapshotAggregateBudgetExceeded,
    load_snapshot_with_size,
)

from .bounded_io import FileReadBudget, bounded_paths, read_bounded_json
from .config import Settings, get_settings


FactorKind = Literal[
    "momentum",
    "mean_reversion",
    "low_volatility",
    "moving_average",
    "volume_momentum",
    "rsi",
]
MAX_VALIDATION_REPORT_BYTES = 4 * 1024 * 1024
MAX_CERTIFIED_SNAPSHOTS = 1000
MAX_CERTIFIED_SNAPSHOT_BYTES = 64 * 1024 * 1024
MAX_VALIDATION_BLOCKERS = 10_000


def _load_validation_report(path: Path) -> dict:
    if not path.exists():
        return {}
    value = read_bounded_json(path, maximum_bytes=MAX_VALIDATION_REPORT_BYTES)
    if not isinstance(value, dict):
        raise ValueError("dataset validation report must be an object")
    blockers = value.get("strategy_candidate_data_blockers", [])
    if not isinstance(blockers, list) or len(blockers) > MAX_VALIDATION_BLOCKERS:
        raise ValueError("dataset validation report blocker limit exceeded")
    return value


class StrictSpecModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FactorSpec(StrictSpecModel):
    kind: FactorKind
    lookback: int = Field(default=20, ge=2, le=252)
    weight: float = Field(default=1.0, ge=-5.0, le=5.0)


class FilterSpec(StrictSpecModel):
    min_price: float = Field(default=5.0, ge=1.0, le=1000.0)
    min_average_volume: float = Field(default=200_000, ge=0, le=1_000_000_000)
    history_days: int = Field(default=60, ge=20, le=252)


class PortfolioSpec(StrictSpecModel):
    initial_cash: float = Field(default=100_000, ge=1_000, le=10_000_000)
    max_positions: int = Field(default=10, ge=1, le=50)
    rebalance_days: int = Field(default=10, ge=1, le=30)
    cost_per_side: float = Field(default=0.003, ge=0, le=0.02)
    stop_loss_pct: float | None = Field(default=-0.05, ge=-0.50, le=-0.005)


class StrategySpec(StrictSpecModel):
    schema_version: Literal[1] = 1
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=1000)
    factors: list[FactorSpec] = Field(min_length=1, max_length=5)
    filters: FilterSpec = Field(default_factory=FilterSpec)
    portfolio: PortfolioSpec = Field(default_factory=PortfolioSpec)

    @field_validator("name", "description")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def require_nonzero_factor(self):
        if not any(abs(factor.weight) > 1e-12 for factor in self.factors):
            raise ValueError("at least one factor weight must be non-zero")
        return self


class DatasetBundle:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.manifest_path = settings.dataset_dir / "manifest.json"
        self.manifest, _manifest_bytes, manifest_sha256 = load_manifest_snapshot(
            self.manifest_path
        )
        self.data = load_price_dataset(
            settings.dataset_dir,
            manifest=self.manifest,
            manifest_sha256=manifest_sha256,
        )
        # Keep the full bundle's public dataset metadata consistent with the
        # manifest-only DatasetSummary.  Callers use this in strategy responses
        # after the price data has been loaded and integrity-checked.
        self.symbol_count = len(self.data)
        index_values = set()
        for frame in self.data.values():
            index_values.update(frame.index)
        self.index = pd.DatetimeIndex(sorted(index_values))
        self.panels = {
            column: pd.DataFrame(
                {ticker: frame[column] for ticker, frame in self.data.items()}, index=self.index
            ).astype("float32")
            for column in ("Open", "High", "Low", "Close", "Volume")
        }
        self.snapshots = _snapshots_for_settings(settings)
        if not self.snapshots:
            raise ValueError("No certified universe snapshots were found")
        self.first_snapshot_date = min(str(item["effective_date"]) for item in self.snapshots)
        self.first_certified_execution_date = next_trading_day(
            dt.date.fromisoformat(self.first_snapshot_date)
        ).isoformat()
        validation_path = settings.dataset_dir / "validation_report.json"
        self.validation = _load_validation_report(validation_path)
        if (
            settings.production
            and self.validation.get("approved_manifest_sha256") != manifest_sha256
        ):
            raise ValueError(
                "production dataset was not independently promoted for this manifest"
            )
        latest_snapshot_hash = self.snapshots[-1]["membership_sha256"]
        validation_window_end = str(self.validation.get("window", {}).get("end", ""))
        self.forward_data_gate_ready = bool(
            self.validation.get("forward_strategy_data_gate_ready", False)
            and self.validation.get("current_snapshot_membership_sha256")
            == latest_snapshot_hash
            and validation_window_end >= self.index.max().date().isoformat()
            and (
                not settings.production
                or self.validation.get("approved_manifest_sha256")
                == manifest_sha256
            )
        )
        assert_manifest_generation(self.manifest_path, manifest_sha256)
        self.fingerprint = manifest_sha256


class DatasetSummary:
    """Small manifest-only view used by the web process and readiness checks."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.manifest_path = settings.dataset_dir / "manifest.json"
        self.manifest, _manifest_bytes, manifest_sha256 = load_manifest_snapshot(
            self.manifest_path
        )
        self.data = self.manifest.get("prices", {})
        if not self.data:
            raise ValueError("Dataset manifest contains no approved prices")
        validate_dataset_inventory(settings.dataset_dir, self.manifest)
        self.price_root = (settings.dataset_dir / "prices").resolve()
        self.verified_price_paths: dict[str, Path] = {}
        total_rows = 0
        total_compressed = 0
        total_uncompressed = 0
        for ticker, metadata in self.data.items():
            if not isinstance(metadata, dict):
                raise ValueError("Dataset manifest price metadata is invalid")
            raw_path = price_file_path(self.price_root, str(ticker))
            if raw_path.is_symlink():
                raise ValueError("Dataset manifest price file is missing or unsafe")
            path = raw_path.resolve()
            if path.parent != self.price_root or not path.is_file():
                raise ValueError("Dataset manifest price file is missing or unsafe")
            if path.stat().st_size <= 0 or path.stat().st_size > MAX_PRICE_FILE_BYTES:
                raise ValueError("Dataset manifest price file size is unsafe")
            expected_hash = str(metadata.get("sha256", ""))
            metrics = {}
            frame = read_price_frame(
                path,
                require_valid=True,
                expected_sha256=expected_hash,
                metrics=metrics,
            )
            total_rows += metrics["rows"]
            total_compressed += metrics["compressed_bytes"]
            total_uncompressed += metrics["uncompressed_bytes"]
            if total_rows > MAX_DATASET_ROWS:
                raise ValueError("Dataset aggregate row limit exceeded")
            if total_compressed > MAX_DATASET_COMPRESSED_BYTES:
                raise ValueError("Dataset aggregate compressed size limit exceeded")
            if total_uncompressed > MAX_DATASET_UNCOMPRESSED_BYTES:
                raise ValueError("Dataset aggregate expanded size limit exceeded")
            if (
                int(metadata.get("rows", -1)) != len(frame)
                or str(metadata.get("first_date", ""))
                != frame.index.min().date().isoformat()
                or str(metadata.get("last_date", ""))
                != frame.index.max().date().isoformat()
            ):
                raise ValueError("Dataset price metadata does not match file contents")
            self.verified_price_paths[str(ticker)] = path
        first_date = min(str(item["first_date"]) for item in self.data.values())
        last_date = max(str(item["last_date"]) for item in self.data.values())
        self.first_completed_session = dt.date.fromisoformat(first_date)
        self.last_completed_session = dt.date.fromisoformat(last_date)
        self.index = pd.DatetimeIndex([self.first_completed_session, self.last_completed_session])
        self.symbol_count = len(self.data)
        self.snapshots = _snapshots_for_settings(settings)
        if not self.snapshots:
            raise ValueError("No certified universe snapshots were found")
        self.first_snapshot_date = min(str(item["effective_date"]) for item in self.snapshots)
        self.first_certified_execution_date = next_trading_day(
            dt.date.fromisoformat(self.first_snapshot_date)
        ).isoformat()
        validation_path = settings.dataset_dir / "validation_report.json"
        self.validation = _load_validation_report(validation_path)
        if (
            settings.production
            and self.validation.get("approved_manifest_sha256") != manifest_sha256
        ):
            raise ValueError(
                "production dataset was not independently promoted for this manifest"
            )
        latest_snapshot_hash = self.snapshots[-1]["membership_sha256"]
        validation_window_end = str(self.validation.get("window", {}).get("end", ""))
        self.forward_data_gate_ready = bool(
            self.validation.get("forward_strategy_data_gate_ready", False)
            and self.validation.get("current_snapshot_membership_sha256")
            == latest_snapshot_hash
            and validation_window_end >= self.last_completed_session.isoformat()
            and (
                not settings.production
                or self.validation.get("approved_manifest_sha256")
                == manifest_sha256
            )
        )
        assert_manifest_generation(self.manifest_path, manifest_sha256)
        self.fingerprint = manifest_sha256


class DashboardDataset(DatasetSummary):
    """Manifest metadata plus only the last two closes for sector display."""

    def __init__(self, settings: Settings, summary: DatasetSummary | None = None):
        if summary is None:
            super().__init__(settings)
        else:
            self.__dict__.update(summary.__dict__)
        closes: dict[str, pd.Series] = {}
        for ticker, path in self.verified_price_paths.items():
            try:
                frame = read_price_frame(
                    path,
                    require_valid=True,
                    expected_sha256=str(self.data[ticker].get("sha256", "")),
                )
                if "Close" not in frame.columns:
                    continue
                series = pd.to_numeric(frame["Close"], errors="coerce").dropna().tail(2)
                if len(series) == 2:
                    closes[str(ticker)] = series.astype("float32")
            except (OSError, ValueError, TypeError, EOFError):
                continue
        assert_manifest_generation(self.manifest_path, self.fingerprint)
        self.panels = {"Close": pd.DataFrame(closes, dtype="float32")}


_bundle_lock = threading.Lock()
_bundle: DatasetBundle | None = None
_bundle_mtime: tuple[int, int, int] | None = None
_summary_lock = threading.Lock()
_summary: DatasetSummary | None = None
_summary_mtime: tuple[int, int, int] | None = None
_dashboard_lock = threading.Lock()
_dashboard: DashboardDataset | None = None
_dashboard_mtime: tuple[int, int, int] | None = None


def _load_certified_snapshots(pattern: str) -> list[dict]:
    # Repeated capture attempts can produce multiple files for one effective
    # date. Keep the latest authenticated capture for that date.
    by_date: dict[str, dict] = {}
    snapshot_paths = bounded_paths(
        glob.iglob(pattern), maximum_count=MAX_CERTIFIED_SNAPSHOTS
    )
    byte_budget = FileReadBudget(MAX_CERTIFIED_SNAPSHOT_BYTES)
    for raw_path in sorted(snapshot_paths):
        try:
            snapshot, _file_size = load_snapshot_with_size(
                raw_path, byte_budget=byte_budget,
            )
        except SnapshotAggregateBudgetExceeded:
            raise
        except (ValueError, OSError, json.JSONDecodeError):
            continue
        if not snapshot.get("certification_eligible", False):
            continue
        date = str(snapshot["effective_date"])
        previous = by_date.get(date)
        if previous is None or str(snapshot.get("captured_at_utc", "")) > str(
            previous.get("captured_at_utc", "")
        ):
            by_date[date] = snapshot
    return [by_date[key] for key in sorted(by_date)]


def _load_local_demo_snapshots(pattern: str) -> list[dict]:
    """Load only explicitly marked synthetic snapshots for the local demo."""

    snapshots = []
    byte_budget = FileReadBudget(MAX_CERTIFIED_SNAPSHOT_BYTES)
    for raw_path in sorted(
        bounded_paths(glob.iglob(pattern), maximum_count=MAX_CERTIFIED_SNAPSHOTS)
    ):
        try:
            snapshot, _file_size = load_snapshot_with_size(
                raw_path, byte_budget=byte_budget
            )
        except (SnapshotAggregateBudgetExceeded, ValueError, OSError, json.JSONDecodeError):
            continue
        if snapshot.get("snapshot_type") == "local_demo_synthetic":
            snapshots.append(snapshot)
    return snapshots


def _snapshots_for_settings(settings: Settings) -> list[dict]:
    snapshots = _load_certified_snapshots(settings.snapshots_glob)
    if not snapshots and settings.local_demo_data and not settings.production:
        return _load_local_demo_snapshots(settings.snapshots_glob)
    return snapshots


def _dataset_mtime(settings: Settings) -> tuple[int, int, int]:
    manifest = settings.dataset_dir / "manifest.json"
    validation = settings.dataset_dir / "validation_report.json"
    snapshot_mtime = max(
        (
            path.stat().st_mtime_ns
            for path in bounded_paths(
                glob.iglob(settings.snapshots_glob),
                maximum_count=MAX_CERTIFIED_SNAPSHOTS,
            )
        ),
        default=0,
    )
    return (
        manifest.stat().st_mtime_ns,
        validation.stat().st_mtime_ns if validation.exists() else 0,
        snapshot_mtime,
    )


def get_dataset_summary(settings: Settings | None = None) -> DatasetSummary:
    global _summary, _summary_mtime
    settings = settings or get_settings()
    current_mtime = _dataset_mtime(settings)
    with _summary_lock:
        if _summary is None or _summary_mtime != current_mtime:
            _summary = DatasetSummary(settings)
            _summary_mtime = current_mtime
        return _summary


def get_dashboard_dataset(settings: Settings | None = None) -> DashboardDataset:
    global _dashboard, _dashboard_mtime
    settings = settings or get_settings()
    current_mtime = _dataset_mtime(settings)
    with _dashboard_lock:
        if _dashboard is None or _dashboard_mtime != current_mtime:
            _dashboard = DashboardDataset(settings, get_dataset_summary(settings))
            _dashboard_mtime = current_mtime
        return _dashboard


def get_dataset_bundle(settings: Settings | None = None) -> DatasetBundle:
    global _bundle, _bundle_mtime
    settings = settings or get_settings()
    current_mtime = _dataset_mtime(settings)
    with _bundle_lock:
        if _bundle is None or _bundle_mtime != current_mtime:
            _bundle = DatasetBundle(settings)
            _bundle_mtime = current_mtime
        return _bundle


def _rsi(close: pd.DataFrame, lookback: int) -> pd.DataFrame:
    change = close.diff()
    gain = change.clip(lower=0).rolling(lookback, min_periods=lookback).mean()
    loss = -change.clip(upper=0).rolling(lookback, min_periods=lookback).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs) - 50) / 50


def raw_factor(kind: FactorKind, lookback: int, panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    close = panels["Close"]
    if kind == "momentum":
        return close.pct_change(lookback, fill_method=None)
    if kind == "mean_reversion":
        return -close.pct_change(lookback, fill_method=None)
    if kind == "low_volatility":
        returns = close.pct_change(fill_method=None)
        return -returns.rolling(lookback, min_periods=lookback).std()
    if kind == "moving_average":
        average = close.rolling(lookback, min_periods=lookback).mean()
        return close / average - 1
    if kind == "volume_momentum":
        average = panels["Volume"].rolling(lookback, min_periods=lookback).mean()
        return panels["Volume"] / average.replace(0, np.nan) - 1
    if kind == "rsi":
        return _rsi(close, lookback)
    raise ValueError("Unsupported factor: {}".format(kind))


def compile_raw_scores(spec: StrategySpec, bundle: DatasetBundle) -> pd.DataFrame:
    combined = pd.DataFrame(0.0, index=bundle.index, columns=bundle.panels["Close"].columns)
    valid_weight = pd.DataFrame(0.0, index=combined.index, columns=combined.columns)
    for factor in spec.factors:
        values = raw_factor(factor.kind, factor.lookback, bundle.panels)
        ranked = values.rank(axis=1, pct=True, method="average")
        weight = float(factor.weight)
        combined = combined.add(ranked.fillna(0.0) * weight, fill_value=0.0)
        valid_weight = valid_weight.add(values.notna().astype(float) * abs(weight), fill_value=0.0)
    return combined.where(valid_weight > 0)


def eligibility_mask(
    spec: StrategySpec,
    bundle: DatasetBundle,
    bias_mode: Literal["strict", "exploratory"],
    *,
    delay_for_next_open: bool = True,
) -> pd.DataFrame:
    mask = build_strategy_eligibility_mask(
        bundle.data,
        bundle.snapshots,
        bundle.index,
        min_history=spec.filters.history_days,
        min_average_volume=spec.filters.min_average_volume,
        min_price=spec.filters.min_price,
        pre_snapshot_policy="none" if bias_mode == "strict" else "first",
    )
    # A D-open fill can only use listing/liquidity/price facts completed by
    # D-1. The live selector is called after D close for the next session and
    # therefore explicitly opts out of this additional row shift.
    if delay_for_next_open:
        return mask.shift(1, fill_value=False).astype(bool)
    return mask


def latest_candidates(spec: StrategySpec, bundle: DatasetBundle, limit: int | None = None) -> list[str]:
    """Live selection uses the latest completed close without an extra shift."""
    raw = compile_raw_scores(spec, bundle)
    mask = eligibility_mask(spec, bundle, "strict", delay_for_next_open=False)
    valid_rows = mask.any(axis=1) & raw.notna().any(axis=1)
    if not valid_rows.any():
        return []
    date = valid_rows[valid_rows].index[-1]
    scores = raw.loc[date].where(mask.loc[date]).dropna().sort_values(ascending=False)
    return [str(item) for item in scores.head(limit or spec.portfolio.max_positions).index]


def run_strategy_backtest(
    spec: StrategySpec,
    *,
    start: str,
    end: str,
    bias_mode: Literal["strict", "exploratory"] = "strict",
    settings: Settings | None = None,
) -> dict:
    settings = settings or get_settings()
    bundle = get_dataset_bundle(settings)
    if bias_mode == "strict" and not bundle.forward_data_gate_ready:
        raise ValueError(
            "strict PIT backtest is blocked until the latest daily data quality gate passes"
        )
    raw = compile_raw_scores(spec, bundle)
    # Canonical contract: score row D contains only information known before
    # the D fill. Raw D close therefore becomes the score on the next row.
    scores = raw.shift(1)
    mask = eligibility_mask(spec, bundle, bias_mode)
    events = []
    if settings.terminal_events_path.exists():
        events = effective_verified_events(load_events(settings.terminal_events_path), through=end)
    config = {
        "capital": spec.portfolio.initial_cash,
        "max_positions": spec.portfolio.max_positions,
        "sector_cap_pct": 1.0,
        "cost_per_side": spec.portfolio.cost_per_side,
        "position_stop_pct": spec.portfolio.stop_loss_pct,
        "buffer_mult": 1.0,
        "inertia_bonus": 0.0,
        "risk_free_rate": 0.0,
        "rebal_interval": spec.portfolio.rebalance_days,
        "max_replace_per_rebal": spec.portfolio.max_positions,
        "execution_timing": "next_open",
        "stop_fill_mode": "ohlc",
        "missing_price_policy": "raise",
        "fractional_shares": True,
        "dynamic_stop_enabled": False,
        "min_signal_count": max(2, spec.portfolio.max_positions),
    }
    result = run_backtest(
        scores,
        bundle.panels["Close"],
        start=start,
        end=end,
        config=config,
        get_sector=lambda _ticker: "all",
        open_prices=bundle.panels["Open"],
        high_prices=bundle.panels["High"],
        low_prices=bundle.panels["Low"],
        eligible_mask=mask,
        terminal_events=events,
    )
    curve = result["equity_curve"]
    certification_eligible = (
        bias_mode == "strict" and start >= bundle.first_certified_execution_date
    )
    caveat = None
    if not certification_eligible:
        caveat = (
            "첫 인증 스냅샷 다음 거래일({}) 이전은 현재 생존 종목을 소급한 탐색용 결과로, "
            "생존편향 없는 성과로 인용할 수 없습니다."
        ).format(bundle.first_certified_execution_date)
    return {
        "schema_version": 1,
        "strategy": spec.model_dump(mode="json"),
        "window": {"start": start, "end": end},
        "bias_mode": bias_mode,
        "certification_eligible": certification_eligible,
        "caveat": caveat,
        "dataset_fingerprint": bundle.fingerprint,
        "dataset_last_session": str(bundle.index.max().date()),
        "metrics": {
            "ending_equity": float(curve.iloc[-1]),
            "return_pct": float((curve.iloc[-1] / spec.portfolio.initial_cash - 1) * 100),
            "annual_return_pct": float(result["ann"]),
            "annual_volatility_pct": float(result["vol"]),
            "sharpe": float(result["sharpe"]),
            "mdd_pct": float(result["mdd"]),
            "annual_turnover_pct": float(result["annual_turnover"]),
            "trade_count": len(result["trade_log"]),
        },
        "equity_curve": [
            {"date": date.date().isoformat(), "value": round(float(value), 4)}
            for date, value in curve.items()
        ],
        "trades": result["trade_log"][-500:],
    }


def strategy_code_preview(spec: StrategySpec) -> str:
    lines = [
        "# Safe strategy DSL preview; execution always uses backtest_core.run_backtest",
        "score = 0",
    ]
    for factor in spec.factors:
        lines.append(
            "score += {weight:g} * factor('{kind}', lookback={lookback}).rank(pct=True)".format(
                weight=factor.weight, kind=factor.kind, lookback=factor.lookback
            )
        )
    lines.extend(
        [
            "score = score.shift(1)  # no same-close lookahead",
            "eligible = pit_membership & trailing_liquidity_filter(",
            "    history_days={}, min_price={}, min_average_volume={})".format(
                spec.filters.history_days,
                spec.filters.min_price,
                spec.filters.min_average_volume,
            ),
        ]
    )
    return "\n".join(lines)
