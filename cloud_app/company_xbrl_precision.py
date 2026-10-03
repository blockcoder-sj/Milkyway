"""Select a reported value only when its coarser repetitions agree by rounding."""
from decimal import Decimal
import re


def decimals(fact):
    value = fact.get('decimals', '')
    if value == 'INF':
        return 17
    if re.fullmatch(r'-?\d{1,2}', value) and -16 <= int(value) <= 16:
        return int(value)
    return None


def reported_value(facts):
    """Return an actual most precise fact, never an estimated or averaged number.

    Conflicting equally precise values, missing precision, and a coarse interval
    that cannot contain the finer reported interval require manual review.
    Decimal arithmetic keeps large scaled financial facts exact.
    """
    values = {value for value, _ in facts}
    if len(values) == 1:
        return next(iter(values))
    if not facts or any(precision is None for _, precision in facts):
        return None
    best = max(precision for _, precision in facts)
    candidates = {value for value, precision in facts if precision == best}
    if len(candidates) != 1:
        return None
    chosen = next(iter(candidates))
    fine = Decimal(0) if best == 17 else Decimal(10) ** -best / 2
    for value, precision in facts:
        margin = Decimal(0) if precision == 17 else Decimal(10) ** -precision / 2
        if chosen - fine < value - margin or chosen + fine > value + margin:
            return None
    return chosen
