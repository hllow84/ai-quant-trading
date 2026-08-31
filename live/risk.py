"""
risk.py -- hard, code-enforced risk limits. Every function here either passes
data through unchanged or refuses to proceed; none of them silently "fix" a
malformed signal into something plausible-looking.
"""
from __future__ import annotations

import pandas as pd

from live.config import KILL_SWITCH_DRAWDOWN, POSITION_CAP, WEIGHT_SUM_TOLERANCE


class RiskViolation(Exception):
    """Raised when a signal or account state fails a hard risk check."""


def validate_weights(weights: pd.Series) -> None:
    """
    Sanity check on the raw model output. Raises RiskViolation (never trades)
    if weights don't sum to ~1.0 or contain a negative -- this is the guard
    against a malformed signal caused by a data error, not a strategy choice.
    """
    if weights.isna().any():
        raise RiskViolation(f"target weights contain NaN: {weights[weights.isna()].index.tolist()}")
    if (weights < 0).any():
        raise RiskViolation(f"target weights contain negative values: {weights[weights < 0].to_dict()}")
    total = float(weights.sum())
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        raise RiskViolation(
            f"target weights sum to {total:.4f}, outside 1.0 +/- {WEIGHT_SUM_TOLERANCE} tolerance"
        )


def apply_position_cap(weights: pd.Series, cap: float = POSITION_CAP) -> pd.Series:
    """
    Hard ceiling: no single position may exceed `cap` of account value, even
    when the model's defensive filter calls for 100% into one instrument
    (IEF). Excess is left UNINVESTED (cash), never redistributed to other
    names -- redistributing would silently invent a different strategy.

    NOTE, stated plainly: the audited strategy's market-filter defensive leg
    is a 100% allocation to IEF during risk-off periods. This cap overrides
    that by design per the task's explicit instruction ("even if the model
    calls for more"), so a risk-off signal will hold ~25% IEF / ~75% cash
    live, not 100% IEF as backtested. Cash still avoids equity drawdown risk
    (the mechanism this filter exists for), so this is a conservative
    departure from the audited allocation, not a defeat of its purpose -- but
    it IS a departure, and live decay-monitoring (monitor.py) should account
    for it when comparing live performance to backtest expectations.
    """
    capped = weights.clip(upper=cap)
    return capped


def update_peak_and_check_kill_switch(
    current_equity: float, peak_equity: float | None
) -> tuple[float, bool, float]:
    """
    Returns (new_peak_equity, kill_switch_triggered, drawdown_fraction).
    Kill switch triggers if current equity is more than KILL_SWITCH_DRAWDOWN
    below the highest equity ever observed (peak is monotonic, never reset
    automatically -- only a manual clear in state.json un-triggers it).
    """
    if peak_equity is None or current_equity > peak_equity:
        peak_equity = current_equity
    drawdown = 1.0 - (current_equity / peak_equity) if peak_equity > 0 else 0.0
    triggered = drawdown > KILL_SWITCH_DRAWDOWN
    return peak_equity, triggered, drawdown
