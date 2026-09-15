"""
momentum_rotation_long_short.py -- STATE_OF_PLAY section 34.

Extends research/momentum_rotation.py's audited ranking/rebalance mechanism
(section 12/12.1-12.5) with a short leg on the bottom-ranked funds. The
ranking, causal signal-date, and one-extra-trading-day execution-lag logic
is REUSED UNCHANGED from momentum_rotation.py (signal_dates, next_trading_day,
the trailing N-month return computation, the causal 200d-SMA market filter)
-- only the final weight-assignment step is new (there is no way to reuse
code that only ever assigns positive weights to build a short leg; every
other input is shared).

SPLIT (stated, per the task): LONG top 5 ranked funds at +20% each (5*20% =
100% gross long, unchanged from the existing long-only baseline). SHORT
bottom 3 ranked funds at -10% each (3*10% = 30% gross short). Total gross
exposure 130%. Risk-off (SPY below its causal 200d SMA): identical to the
baseline -- 100% into IEF, no shorts -- so the ONLY thing this test isolates
is what the short leg does during risk-on regimes, not a redesign of the
market filter.

Reuses simulate() and look_ahead_guard() from momentum_rotation.py
UNCHANGED -- both are generic to any signed weights_at_exec frame.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.momentum_rotation import (
    signal_dates, next_trading_day, SMA_WINDOW,
)

LONG_K = 5
SHORT_K = 3
LONG_WEIGHT = 0.20   # 5 x 0.20 = 100% gross long
SHORT_WEIGHT = -0.10  # 3 x 0.10 = 30% gross short


def build_weights_long_short(
    adjclose: pd.DataFrame,
    n_months: int,
    long_k: int = LONG_K,
    short_k: int = SHORT_K,
    long_weight: float = LONG_WEIGHT,
    short_weight: float = SHORT_WEIGHT,
    market_filter: bool = True,
    universe: list[str] | None = None,
    sma_window: int = SMA_WINDOW,
    benchmark: str = "SPY",
    defensive: str = "IEF",
) -> tuple[pd.DataFrame, pd.Series]:
    """Long/short variant of momentum_rotation.build_weights. Same causal
    signal dates, same trailing N-month ranking, same market filter; adds a
    short sleeve on the bottom `short_k` ranked names at `short_weight` each
    (negative), alongside the unchanged top `long_k` long sleeve at
    `long_weight` each. Risk-off behaviour is byte-identical to the
    long-only baseline (100% IEF, no shorts)."""
    from research.momentum_rotation import UNIVERSE as DEFAULT_UNIVERSE
    uni = universe if universe is not None else DEFAULT_UNIVERSE
    daily_index = adjclose.index
    sig_dates = signal_dates(daily_index, "M")

    spy = adjclose[benchmark]
    spy_sma = spy.rolling(sma_window, min_periods=sma_window).mean()

    rows, exec_dates = [], []
    prev_w = pd.Series(0.0, index=uni)

    for t in sig_dates:
        target_month = (pd.Timestamp(t).to_period("M") - n_months).to_timestamp("M")
        past_candidates = [d for d in sig_dates if d <= np.datetime64(target_month) + np.timedelta64(6, "D")]
        past_candidates = [d for d in past_candidates if pd.Timestamp(d).to_period("M") == pd.Timestamp(target_month).to_period("M")]
        if not past_candidates:
            continue
        t_past = past_candidates[-1]

        px_now = adjclose.loc[t, uni]
        px_past = adjclose.loc[t_past, uni]
        valid = px_now.notna() & px_past.notna() & (px_past != 0)
        if valid.sum() < (long_k + short_k):
            continue

        trailing_ret = (px_now[valid] / px_past[valid] - 1.0).sort_values(ascending=False)
        longs = trailing_ret.index[:long_k]
        shorts = trailing_ret.index[-short_k:]

        risk_off = False
        if market_filter:
            sma_t = spy_sma.loc[t]
            if pd.isna(sma_t):
                continue
            risk_off = spy.loc[t] < sma_t

        w = pd.Series(0.0, index=uni)
        if risk_off:
            if pd.isna(adjclose.loc[t, defensive]):
                continue
            w[defensive] = 1.0
        else:
            w[longs] = long_weight
            w[shorts] = short_weight

        ed = next_trading_day(daily_index, t)
        if ed is None:
            continue

        rows.append(w)
        exec_dates.append(ed)
        prev_w = w

    weights_at_exec = pd.DataFrame(rows, index=pd.DatetimeIndex(exec_dates), columns=uni)
    turnover_at_exec = pd.Series(
        [float((weights_at_exec.iloc[i] - (weights_at_exec.iloc[i - 1] if i > 0 else pd.Series(0.0, index=uni))).abs().sum())
         for i in range(len(weights_at_exec))],
        index=weights_at_exec.index,
    )
    return weights_at_exec, turnover_at_exec
