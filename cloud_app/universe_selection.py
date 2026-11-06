"""One diagnostic interface for current and previously saved market strategies.

The saved identifier is retained so existing accounts keep their original rules.
New strategies use us_all. This adapter never migrates accounts or performs I/O
against a provider; it only reads the appropriate prepared local checkpoint.
"""
AUTOMATIC_UNIVERSES = frozenset({"us_market", "us_all"})


def status(settings, owner, spec, *, now=None):
    if spec.universe == "us_market":
        from .us_universe import status as legacy_status
        return legacy_status(settings, owner, spec)
    if spec.universe == "us_all":
        from .auto_universe import decision_for, status as prepared_status
        result = prepared_status(settings)
        try:
            decision = decision_for(settings, spec, now)
        except (ValueError, OSError):
            return {**result, "ready": False, "candidates": []}
        return {**result, "ready": result.get("status") == "screened",
                "candidates": decision["targets"]}
    return {"ready": True, "candidates": list(spec.symbols)}
