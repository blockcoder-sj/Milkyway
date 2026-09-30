"""Shared, quantity-based portfolio accounting for every strategy.

Strategies provide only a date-by-symbol score matrix.  This module owns the
execution clock, cash, shares, fees, stops, rebalancing, and performance
metrics so a strategy cannot silently change portfolio accounting.

Signal contract
---------------
The score at row ``D`` must be knowable before the configured fill on ``D``.
The production signal builders therefore return ``raw_signal.shift(1)``.

Execution modes
---------------
``close`` (default)
    The shifted signal at D is filled at D close.  Existing holdings carry the
    complete previous-close to D-close return before they are sold.

``next_open``
    The shifted signal at D is filled at D open.  Daily Open data is only a
    proxy for the live 09:35 fill; exact parity needs a 09:35 bar panel.

``next_0935``
    The shifted signal at D is filled from an explicitly supplied 09:35
    execution-price panel.  Daily Open/Low can still be supplied separately
    for stop-loss checks.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Optional

import numpy as np
import pandas as pd
from portfolio_allocation import plan_allocation


CandidateFilter = Callable[[str, pd.DataFrame, pd.Timestamp, bool], bool]


def _terminal_event_queue(events) -> list[dict]:
    """Normalize verified corporate-action settlements for the event loop."""
    if events is None:
        return []
    if isinstance(events, dict):
        if all(isinstance(value, dict) for value in events.values()):
            events = list(events.values())
        else:
            raise ValueError("terminal_events mapping values must be event dictionaries")
    normalized = []
    for raw in events:
        event = dict(raw)
        if str(event.get("status", "verified")) != "verified":
            continue
        ticker = str(event.get("ticker", "")).upper().strip()
        if not ticker:
            raise ValueError("terminal event ticker is required")
        try:
            effective_date = pd.Timestamp(event["effective_date"]).normalize()
        except Exception as exc:
            raise ValueError("terminal event effective_date is required") from exc
        cash = event.get("cash_per_share")
        cash = None if cash is None else float(cash)
        successor = event.get("successor_symbol")
        successor = str(successor).upper().strip() if successor else None
        ratio = event.get("share_ratio")
        ratio = None if ratio is None else float(ratio)
        if cash is not None and cash < 0:
            raise ValueError("terminal event cash_per_share must be non-negative")
        if bool(successor) != bool(ratio is not None):
            raise ValueError("successor_symbol and share_ratio must be supplied together")
        if ratio is not None and ratio <= 0:
            raise ValueError("terminal event share_ratio must be positive")
        if cash is None and successor is None:
            raise ValueError("verified terminal event needs cash and/or successor shares")
        normalized.append(
            {
                **event,
                "ticker": ticker,
                "effective_date": effective_date,
                "cash_per_share": cash,
                "successor_symbol": successor,
                "share_ratio": ratio,
            }
        )
    return sorted(normalized, key=lambda event: (event["effective_date"], event["ticker"]))


def _number(panel: Optional[pd.DataFrame], date, ticker) -> float:
    if panel is None or date not in panel.index or ticker not in panel.columns:
        return float("nan")
    value = panel.at[date, ticker]
    if pd.isna(value):
        return float("nan")
    try:
        value = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return value if np.isfinite(value) and value > 0 else float("nan")


def _metrics(port: pd.Series, capital: float, rf: float, annual_turnover: float) -> dict:
    dr = port.pct_change(fill_method=None).dropna()
    base = {
        "sharpe": 0.0,
        "ann": 0.0,
        "mdd": 0.0,
        "vol": 0.0,
        "yearly": {},
        "equity_curve": port,
        "annual_turnover": float(annual_turnover),
    }
    if len(dr) == 0:
        return base

    base["mdd"] = float(((port - port.cummax()) / port.cummax() * 100).min())
    if len(dr) < 30 or float(dr.std()) < 1e-10:
        return base

    base["ann"] = float(((port.iloc[-1] / port.iloc[0]) ** (252 / len(dr)) - 1) * 100)
    base["vol"] = float(dr.std() * np.sqrt(252) * 100)
    base["sharpe"] = float((dr.mean() * 252 - rf) / (dr.std() * np.sqrt(252)))

    yearly = {}
    # ``YE`` is unavailable in older pandas releases used by some broker
    # images. ``A`` is the equivalent legacy calendar year-end bucket.
    try:
        year_ends = port.resample("YE").last()
    except ValueError:
        year_ends = port.resample("A").last()
    previous = float(capital)
    for date, value in year_ends.items():
        yearly[int(date.year)] = float((value / previous - 1) * 100)
        previous = float(value)
    base["yearly"] = yearly
    return base


def _rebalance_dates(index: pd.DatetimeIndex, interval: int) -> set:
    """Start on the first executable row, then use calendar-day spacing."""
    dates = set()
    last = None
    for date in index[1:]:
        if last is None or (date - last).days >= interval:
            dates.add(date)
            last = date
    return dates


def _select_targets(
    scores: pd.Series,
    holdings: list[str],
    top_n: int,
    sector_cap: float,
    buffer_mult: float,
    inertia: float,
    max_replace: int,
    get_sector: Callable[[str], str],
    close: pd.DataFrame,
    date: pd.Timestamp,
    execution_prices: pd.DataFrame,
    candidate_filter: Optional[CandidateFilter],
    excluded: set[str],
    candidate_pool_mult: int,
) -> list[str]:
    scores = scores.replace([np.inf, -np.inf], np.nan).dropna()
    scores = scores.drop(labels=list(excluded), errors="ignore")
    held_set = set(holdings)

    if inertia > 0 and holdings:
        adjusted = scores.copy()
        score_range = scores.quantile(0.9) - scores.quantile(0.1)
        bonus = float(score_range) * inertia if pd.notna(score_range) else 0.0
        for ticker in holdings:
            if ticker in adjusted.index:
                adjusted.at[ticker] += bonus
        scores = adjusted

    buffer_n = max(top_n, int(top_n * buffer_mult))
    if holdings:
        ranked = scores.rank(ascending=False, method="first")
        keep = [ticker for ticker in holdings
                if ticker in ranked.index and ranked.at[ticker] <= buffer_n]
        remaining = scores.drop(labels=keep, errors="ignore")
        candidates = keep + remaining.nlargest(top_n * candidate_pool_mult).index.tolist()
    else:
        candidates = scores.nlargest(top_n * candidate_pool_mult).index.tolist()

    max_per_sector = max(1, int(top_n * sector_cap))
    other_count = sum(1 for ticker in candidates if get_sector(ticker) == "other")
    other_ratio = other_count / max(len(candidates), 1)
    max_other = max(1, int(top_n * max(0.50, min(0.80, other_ratio))))

    counts = defaultdict(int)
    selected = []
    for ticker in scores.reindex(candidates).dropna().sort_values(ascending=False).index:
        if not np.isfinite(_number(execution_prices, date, ticker)):
            continue
        if candidate_filter is not None:
            if not candidate_filter(ticker, close, date, ticker in held_set):
                continue
        sector = get_sector(ticker)
        cap = max_other if sector == "other" else max_per_sector
        if counts[sector] >= cap:
            continue
        selected.append(ticker)
        counts[sector] += 1
        if len(selected) >= top_n:
            break

    if max_replace > 0 and holdings:
        new_set = set(selected)
        removals = [ticker for ticker in holdings if ticker not in new_set]
        removals.sort(key=lambda ticker: float(scores.get(ticker, -np.inf)))
        actual_remove = set(removals[:max_replace])
        additions = [ticker for ticker in selected if ticker not in held_set][:max_replace]
        selected = [ticker for ticker in holdings if ticker not in actual_remove] + additions
        selected = selected[:top_n]

    return selected


def run_backtest(
    ensemble: pd.DataFrame,
    close: pd.DataFrame,
    start=None,
    end=None,
    config: Optional[dict] = None,
    *,
    get_sector: Callable[[str], str],
    track_positions: bool = False,
    open_prices: Optional[pd.DataFrame] = None,
    high_prices: Optional[pd.DataFrame] = None,
    low_prices: Optional[pd.DataFrame] = None,
    execution_prices: Optional[pd.DataFrame] = None,
    eligible_mask: Optional[pd.DataFrame] = None,
    terminal_events=None,
    candidate_filter: Optional[CandidateFilter] = None,
    min_targets_pct: float = 0.0,
) -> dict:
    """Run one shared, long-only portfolio ledger.

    Prices are never forward-filled.  With the default
    ``missing_price_policy='raise'``, a held security whose close disappears
    stops the backtest and forces the caller to supply a terminal/delisting
    value instead of silently receiving a 0% return.
    """
    config = dict(config or {})
    capital = float(config.get("capital", 100_000))
    top_n = int(config.get("max_positions", 25))
    cost = float(config.get("cost_per_side", 0.003))
    sector_cap = float(config.get("sector_cap_pct", 0.30))
    rf = float(config.get("risk_free_rate", 0.04))
    stop_pct = config.get("position_stop_pct", -0.10)
    stop_pct = float(stop_pct) if stop_pct is not None else None
    buffer_mult = float(config.get("buffer_mult", 2.0))
    inertia = float(config.get("inertia_bonus", 0.10))
    rebal_interval = max(1, int(config.get("rebal_interval", 10)))
    max_replace = max(0, int(config.get("max_replace_per_rebal", 0)))
    execution_timing = str(config.get("execution_timing", "close")).lower()
    stop_fill_mode = str(config.get("stop_fill_mode", "auto")).lower()
    missing_policy = str(config.get("missing_price_policy", "raise")).lower()
    fractional = bool(config.get("fractional_shares", True))
    dynamic_stop_enabled = bool(config.get("dynamic_stop_enabled", False))
    candidate_pool_mult = max(3, int(config.get("candidate_pool_mult", 3)))
    min_signal_count = max(top_n, int(config.get("min_signal_count", top_n * 2)))

    if top_n <= 0:
        raise ValueError("max_positions must be positive")
    if cost < 0 or cost >= 1:
        raise ValueError("cost_per_side must be in [0, 1)")
    if execution_timing not in {"close", "next_open", "next_0935"}:
        raise ValueError("execution_timing must be close/next_open/next_0935")
    if execution_timing == "next_open" and open_prices is None:
        raise ValueError("execution_timing='next_open' requires open_prices")
    if execution_timing == "next_0935" and execution_prices is None:
        raise ValueError("execution_timing='next_0935' requires execution_prices")
    if stop_fill_mode not in {"auto", "none", "close", "stop", "ohlc"}:
        raise ValueError("stop_fill_mode must be auto/none/close/stop/ohlc")
    if missing_policy not in {"raise", "last", "liquidate_last"}:
        raise ValueError("missing_price_policy must be raise/last/liquidate_last")

    idx = pd.DatetimeIndex(ensemble.index).sort_values().unique()
    if start is not None:
        idx = idx[idx >= pd.Timestamp(start)]
    if end is not None:
        idx = idx[idx <= pd.Timestamp(end)]
    if len(idx) < 2:
        empty = pd.Series([capital] if len(idx) else [], index=idx, dtype=float)
        return _metrics(empty, capital, rf, 0.0)

    ensemble_bt = ensemble.reindex(idx)
    close_bt = close.reindex(idx)
    open_bt = open_prices.reindex(idx) if open_prices is not None else None
    high_bt = high_prices.reindex(idx) if high_prices is not None else None
    low_bt = low_prices.reindex(idx) if low_prices is not None else None
    explicit_execution_bt = execution_prices.reindex(idx) if execution_prices is not None else None
    if execution_timing == "close":
        fill_prices = close_bt
    elif execution_timing == "next_open":
        fill_prices = open_bt
    else:
        fill_prices = explicit_execution_bt
    eligible_bt = None
    if eligible_mask is not None:
        eligible_bt = eligible_mask.reindex(
            index=idx, columns=ensemble_bt.columns, fill_value=False
        ).fillna(False).astype(bool)
    event_queue = _terminal_event_queue(terminal_events)
    event_cursor = 0
    rebal_dates = _rebalance_dates(idx, rebal_interval)

    if stop_fill_mode == "auto":
        stop_fill_mode = "ohlc" if open_bt is not None and low_bt is not None else "close"
    if stop_fill_mode == "ohlc" and (open_bt is None or low_bt is None):
        raise ValueError("stop_fill_mode='ohlc' requires open_prices and low_prices")

    cash = capital
    shares: dict[str, float] = {}
    entry_prices: dict[str, float] = {}
    last_marks: dict[str, float] = {}
    eq_list = [capital]
    dt_list = [idx[0]]
    turnover_sum = 0.0
    trade_log = []
    positions_history = [] if track_positions else None
    cost_ledger: Optional[dict[str, float]] = {} if track_positions else None

    def record_fee(ticker: str, fee: float, equity_before: float) -> None:
        if cost_ledger is not None and equity_before > 0:
            cost_ledger[ticker] = cost_ledger.get(ticker, 0.0) + fee / equity_before

    def mark_price(date, ticker) -> float:
        value = _number(close_bt, date, ticker)
        if np.isfinite(value):
            last_marks[ticker] = value
            return value
        if missing_policy == "raise":
            raise ValueError(
                f"Missing close for held ticker {ticker} on {pd.Timestamp(date).date()}; "
                "supply terminal/delisting data or choose an explicit missing_price_policy"
            )
        previous = last_marks.get(ticker, float("nan"))
        if not np.isfinite(previous):
            raise ValueError(f"No valuation price for held ticker {ticker} on {date}")
        return previous

    def equity_at(date) -> float:
        return float(cash + sum(quantity * mark_price(date, ticker)
                                for ticker, quantity in shares.items()))

    def sell(ticker: str, price: float, date, reason: str, equity_before: float, quantity=None) -> float:
        nonlocal cash
        held = shares.get(ticker, 0.0)
        quantity = held if quantity is None else min(held, quantity)
        if quantity <= 0:
            return 0.0
        if held - quantity <= 1e-9:
            shares.pop(ticker, None)
            entry_prices.pop(ticker, None)
        else:
            shares[ticker] = held - quantity
        gross = quantity * price
        fee = gross * cost
        cash += gross - fee
        record_fee(ticker, fee, equity_before)
        trade_log.append({
            "date": pd.Timestamp(date), "ticker": ticker, "side": "SELL",
            "shares": float(quantity), "price": float(price), "gross": float(gross),
            "fee": float(fee), "reason": reason,
        })
        return gross

    def buy(ticker, quantity, price, date, equity_before, reason):
        nonlocal cash
        gross = quantity * price
        fee = gross * cost
        if quantity <= 0 or gross + fee > cash + 1e-8:
            raise ValueError("Allocation exceeds available cash")
        held = shares.get(ticker, 0.0)
        entry_prices[ticker] = (entry_prices.get(ticker, price) * held + gross) / (held + quantity)
        shares[ticker] = held + quantity
        cash = max(0.0, cash - gross - fee)
        record_fee(ticker, fee, equity_before)
        trade_log.append({
            "date": pd.Timestamp(date), "ticker": ticker, "side": "BUY",
            "shares": float(quantity), "price": float(price), "gross": float(gross),
            "fee": float(fee), "reason": reason,
        })
        return gross

    def allocate(selected, date, equity_before):
        prices = {ticker: _number(fill_prices, date, ticker) for ticker in set(shares) | set(selected)}
        orders = plan_allocation(
            cash=cash, holdings=shares, prices=prices, targets=selected, cost_per_side=cost,
            investment_fraction=float(config.get("investment_fraction", 1)),
            max_position_fraction=float(config.get("max_position_fraction", 1)),
            rebalance_weights=bool(config.get("rebalance_weights", False)), fractional=fractional,
        )
        traded = 0.0
        for order in orders:
            if order.side == "SELL":
                traded += sell(order.ticker, prices[order.ticker], date, order.reason,
                               equity_before, order.shares)
            else:
                traded += buy(order.ticker, order.shares, prices[order.ticker], date, equity_before, order.reason)
        return traded

    def apply_terminal_events(date, equity_before: float) -> None:
        """Settle events effective on or before this session without trading fees."""
        nonlocal cash, event_cursor
        normalized_date = pd.Timestamp(date).normalize()
        while (
            event_cursor < len(event_queue)
            and event_queue[event_cursor]["effective_date"] <= normalized_date
        ):
            event = event_queue[event_cursor]
            event_cursor += 1
            ticker = event["ticker"]
            if ticker not in shares:
                continue
            quantity = shares.pop(ticker)
            old_entry = entry_prices.pop(ticker, None)
            last_marks.pop(ticker, None)
            cash_per_share = event.get("cash_per_share")
            cash_proceeds = quantity * cash_per_share if cash_per_share is not None else 0.0
            cash += cash_proceeds

            successor = event.get("successor_symbol")
            successor_quantity = 0.0
            successor_price = None
            if successor:
                successor_quantity = quantity * float(event["share_ratio"])
                successor_price = _number(fill_prices, date, successor)
                if not np.isfinite(successor_price):
                    successor_price = _number(close_bt, date, successor)
                if not np.isfinite(successor_price):
                    raise ValueError(
                        "No price for terminal-event successor {} on {}".format(
                            successor, pd.Timestamp(date).date()
                        )
                    )
                previous_quantity = shares.get(successor, 0.0)
                shares[successor] = previous_quantity + successor_quantity
                entry_prices[successor] = successor_price
                last_marks[successor] = successor_price

            trade_log.append(
                {
                    "date": pd.Timestamp(date),
                    "ticker": ticker,
                    "side": "CORPORATE_ACTION",
                    "shares": float(quantity),
                    "price": float(cash_per_share or 0.0),
                    "gross": float(cash_proceeds),
                    "fee": 0.0,
                    "reason": "terminal_event:{}".format(
                        event.get("event_type", "unknown")
                    ),
                    "successor_symbol": successor,
                    "successor_shares": float(successor_quantity),
                    "successor_price": (
                        float(successor_price) if successor_price is not None else None
                    ),
                    "old_entry_price": old_entry,
                    "equity_before": float(equity_before),
                    "source": event.get("source"),
                }
            )

    def effective_stop(date_index: int) -> Optional[float]:
        if stop_pct is None or not dynamic_stop_enabled:
            return stop_pct
        # Live calculates the regime from completed cached bars.  Use D-1 for
        # both fill modes so the threshold is known before any D intraday fill.
        reference_index = date_index - 1
        lookback_index = reference_index - 19
        if lookback_index < 0:
            return stop_pct
        current = close_bt.iloc[reference_index]
        previous = close_bt.iloc[lookback_index].replace(0, np.nan)
        market_returns = (current / previous - 1).replace([np.inf, -np.inf], np.nan).dropna()
        if market_returns.empty:
            return stop_pct
        market_return = float(market_returns.median())
        severe_threshold = float(config.get("dynamic_stop_severe_market_return", -0.10))
        weak_threshold = float(config.get("dynamic_stop_weak_market_return", -0.05))
        if market_return < severe_threshold:
            return float(config.get("dynamic_stop_severe_pct", -0.02))
        if market_return < weak_threshold:
            return float(config.get("dynamic_stop_weak_pct", -0.03))
        return stop_pct

    def stop_price(date, ticker, active_stop_pct) -> Optional[float]:
        if active_stop_pct is None or stop_fill_mode == "none" or ticker not in entry_prices:
            return None
        entry = entry_prices[ticker]
        level = entry * (1 + active_stop_pct)
        current_close = _number(close_bt, date, ticker)
        if stop_fill_mode == "ohlc":
            current_open = _number(open_bt, date, ticker)
            current_low = _number(low_bt, date, ticker)
            if current_open <= level:
                return current_open
            if current_low <= level:
                return level
            return None
        if not np.isfinite(current_close) or current_close > level:
            return None
        return level if stop_fill_mode == "stop" else current_close

    for i, date in enumerate(idx[1:], start=1):
        previous_date = idx[i - 1]
        previous_equity = float(eq_list[-1])
        starting_shares = dict(shares)

        # Cash remains cash after stops and partial fills; accrue it explicitly.
        cash *= 1 + rf / 252

        # Settle known cash/stock consideration before treating a missing close
        # as an unexplained data failure.
        apply_terminal_events(date, previous_equity)

        # Do not silently pad a held security through a missing terminal price.
        for ticker in list(shares):
            current_close = _number(close_bt, date, ticker)
            if np.isfinite(current_close):
                last_marks[ticker] = current_close
                continue
            if missing_policy == "liquidate_last":
                previous = last_marks.get(ticker, _number(close_bt, previous_date, ticker))
                if not np.isfinite(previous):
                    raise ValueError(f"No liquidation price for {ticker} on {date}")
                sell(ticker, previous, date, "missing_price_liquidation", previous_equity)
            elif missing_policy == "raise":
                mark_price(date, ticker)

        stopped_today = set()
        active_stop_pct = effective_stop(i)

        # At next_open the rebalance happens before the day's intraday stop check.
        if execution_timing in {"next_open", "next_0935"} and date in rebal_dates:
            scores = ensemble_bt.loc[date].dropna()
            if eligible_bt is not None:
                scores = scores[eligible_bt.loc[date].reindex(scores.index).fillna(False)]
            if len(scores) >= min_signal_count:
                holdings = list(shares)
                selected = _select_targets(
                    scores, holdings, top_n, sector_cap, buffer_mult, inertia,
                    max_replace, get_sector, close_bt, date, fill_prices,
                    candidate_filter, stopped_today, candidate_pool_mult,
                )
                min_targets = max(1, int(np.ceil(top_n * min_targets_pct))) if min_targets_pct else 1
                if len(selected) >= min_targets:
                    pre_trade_equity = cash + sum(
                        quantity * _number(fill_prices, date, ticker)
                        for ticker, quantity in shares.items()
                    )
                    old_set = set(shares)
                    traded = allocate(selected, date, pre_trade_equity)
                    if old_set and pre_trade_equity > 0:
                        turnover_sum += traded / (2 * pre_trade_equity)

        # Stop proceeds stay in cash; surviving positions are never renormalized.
        for ticker in list(shares):
            fill = stop_price(date, ticker, active_stop_pct)
            if fill is None:
                continue
            before = cash + sum(quantity * mark_price(date, held)
                                for held, quantity in shares.items())
            sell(ticker, fill, date, "stop_loss", before)
            stopped_today.add(ticker)

        # Close fills happen only after the old holdings have borne the full day.
        if execution_timing == "close" and date in rebal_dates:
            scores = ensemble_bt.loc[date].dropna()
            if eligible_bt is not None:
                scores = scores[eligible_bt.loc[date].reindex(scores.index).fillna(False)]
            if len(scores) >= min_signal_count:
                holdings = list(shares)
                selected = _select_targets(
                    scores, holdings, top_n, sector_cap, buffer_mult, inertia,
                    max_replace, get_sector, close_bt, date, fill_prices,
                    candidate_filter, stopped_today, candidate_pool_mult,
                )
                min_targets = max(1, int(np.ceil(top_n * min_targets_pct))) if min_targets_pct else 1
                if len(selected) >= min_targets:
                    pre_trade_equity = equity_at(date)
                    old_set = set(shares)
                    traded = allocate(selected, date, pre_trade_equity)
                    if old_set and pre_trade_equity > 0:
                        turnover_sum += traded / (2 * pre_trade_equity)

        end_equity = equity_at(date)
        eq_list.append(end_equity)
        dt_list.append(date)

        if track_positions:
            per_return = {}
            per_contrib = {}
            for ticker, quantity in starting_shares.items():
                prev = _number(close_bt, previous_date, ticker)
                current = _number(close_bt, date, ticker)
                if np.isfinite(prev) and np.isfinite(current) and prev > 0 and previous_equity > 0:
                    ticker_return = current / prev - 1
                    per_return[ticker] = float(ticker_return)
                    per_contrib[ticker] = float(quantity * prev / previous_equity * ticker_return)
            weights = {
                ticker: float(quantity * mark_price(date, ticker) / end_equity)
                for ticker, quantity in shares.items()
            } if end_equity > 0 else {}
            positions_history.append({
                "date": date,
                "holdings": list(shares),
                "weights": weights,
                "cash": float(cash),
                "equity": float(end_equity),
                "port_ret": float(end_equity / previous_equity - 1) if previous_equity > 0 else 0.0,
                "per_symbol_return": per_return,
                "per_symbol_contrib": per_contrib,
            })

    port = pd.Series(eq_list, index=pd.to_datetime(dt_list), dtype=float)
    annual_turnover = turnover_sum * 252 / max(len(port) - 1, 1) * 100
    result = _metrics(port, capital, rf, annual_turnover)
    result["trade_log"] = trade_log
    result["final_cash"] = float(cash)
    result["final_shares"] = {ticker: float(quantity) for ticker, quantity in shares.items()}
    if track_positions:
        result["positions_history"] = positions_history
        result["cost_ledger"] = cost_ledger
    return result
