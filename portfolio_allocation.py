"""Pure allocation planning shared by historical and personal paper execution."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class AllocationOrder:
    ticker: str
    side: str
    shares: float
    reason: str


def plan_allocation(*, cash, holdings, prices, targets, cost_per_side=0,
                    investment_fraction=1, max_position_fraction=1,
                    rebalance_weights=False, fractional=True):
    """Sell first, then proportionally fund buys while reserving cash and fees.

    Targets are equal weight, capped per position. With weight rebalancing off,
    surviving positions keep their quantities, matching legacy execution.
    Fractions describe targets at the rebalance price, not continuous limits.
    """
    targets = list(dict.fromkeys(targets))
    numbers = [cash, cost_per_side, investment_fraction, max_position_fraction,
               *holdings.values(), *[prices[t] for t in set(holdings) | set(targets)]]
    if any(isinstance(value, bool) or not math.isfinite(value) for value in numbers):
        raise ValueError("Allocation requires finite numbers")
    if cash < -1e-7 or not 0 <= cost_per_side < 1:
        raise ValueError("Invalid allocation cash or cost")
    if not 0 < investment_fraction <= 1 or not 0 < max_position_fraction <= 1:
        raise ValueError("Allocation fractions must be in (0, 1]")
    if any(q < 0 for q in holdings.values()) or any(prices[t] <= 0 for t in set(holdings) | set(targets)):
        raise ValueError("Invalid allocation holding or price")
    equity = cash + sum(q * prices[t] for t, q in holdings.items())
    if equity <= 0:
        return []
    target_value = equity * min(investment_fraction / max(len(targets), 1), max_position_fraction)
    invested = min(investment_fraction, len(targets) * max_position_fraction)
    reserve = equity * (1 - invested)
    remaining = dict(holdings)
    orders = []
    for ticker, quantity in holdings.items():
        desired = target_value / prices[ticker] if ticker in targets else 0
        if not fractional:
            desired = math.floor(desired)
        amount = quantity if ticker not in targets else max(0, quantity - desired) if rebalance_weights else 0
        if amount > 1e-9:
            orders.append(AllocationOrder(ticker, "SELL", amount,
                                         "removed_from_target" if ticker not in targets else "rebalance_weight"))
            cash += amount * prices[ticker] * (1 - cost_per_side)
            remaining[ticker] = quantity - amount
    desired_buys = {
        ticker: max(0, target_value - remaining.get(ticker, 0) * prices[ticker])
        for ticker in targets if rebalance_weights or ticker not in holdings
    }
    total = sum(desired_buys.values())
    scale = min(1, max(0, cash - reserve) / (1 + cost_per_side) / total) if total else 0
    for ticker, value in desired_buys.items():
        quantity = value * scale / prices[ticker]
        if not fractional:
            quantity = math.floor(quantity)
        if quantity > 1e-9:
            orders.append(AllocationOrder(ticker, "BUY", quantity,
                                         "rebalance_weight" if ticker in holdings else "new_target"))
    return orders
