"""
positioning_reversal.py — contrarian positioning-extreme reversal.

MECHANISM (documented phenomenon, not an arbitrary rule, stated in one
sentence as required): when funding rate sits at an extreme percentile of
its own trailing distribution AND open interest is elevated (many traders
crowded onto the side paying/receiving that extreme funding), the crowd is
prone to a forced unwind/squeeze as the extreme resolves — this trades
documented crowded-positioning-squeeze / funding-rate mean-reversion, a bet
on OTHER TRADERS' POSITIONING, not on price shape.

Vectorized, same conventions as strategies/sweep_families.py (rising-edge
entry, defined-risk hard stop, fixed R-multiple target, max-hold cap H) —
reuses that module's `_emit()` trade-dict builder directly so trade
construction is identical to every other family in this repo.

Direction is CONTRARIAN by construction:
  funding at the extreme HIGH end (crowded LONGS paying shorts) -> go SHORT
  funding at the extreme LOW end (crowded SHORTS paying longs)  -> go LONG
"""
from __future__ import annotations

import pandas as pd

from strategies.ftmo_gold import atr
from strategies.sweep_families import _emit


def positioning_reversal(m: pd.DataFrame, funding_pctl: pd.Series, oi_pctl: pd.Series,
                         p: dict, tf_delta: pd.Timedelta) -> list[dict]:
    """
    m            : H1 mid-OHLC frame (mid_open/high/low/close, spread, volume)
    funding_pctl : pre-aligned, ALREADY LAGGED rolling percentile rank (0-100)
                   of the funding rate within its own trailing distribution,
                   reindexed onto m.index (see run_positioning_reversal.py's
                   align_feature() for the causal alignment + lag).
    oi_pctl      : same, for open interest.
    p            : dict(funding_bar, oi_bar, k_atr, R, H) — see driver for
                   the stated grid. funding_bar in {5, 10} (percent, each
                   tail); oi_bar is the elevated-OI threshold (fixed, stated
                   in the driver, not swept).
    """
    c = m["mid_close"]
    a = atr(m, 14)
    se = pd.Series(m.index + p["H"] * tf_delta, index=m.index)

    crowded_long = (funding_pctl >= (100 - p["funding_bar"])) & (oi_pctl >= p["oi_bar"])
    crowded_short = (funding_pctl <= p["funding_bar"]) & (oi_pctl >= p["oi_bar"])

    # rising edge only — fire once per new extreme episode, not on every bar
    # the condition happens to still be true
    short_e = crowded_long & ~crowded_long.shift(1, fill_value=False)   # fade crowded longs
    long_e = crowded_short & ~crowded_short.shift(1, fill_value=False)  # fade crowded shorts

    risk = p["k_atr"] * a
    l_stop = c - risk
    s_stop = c + risk
    l_tgt = c + p["R"] * risk
    s_tgt = c - p["R"] * risk

    return (_emit(m.index, long_e, "long", c, l_stop, l_tgt, se.to_numpy())
            + _emit(m.index, short_e, "short", c, s_stop, s_tgt, se.to_numpy()))


# ── stated grid, a priori, not tuned ────────────────────────────────────────
# funding_bar: test BOTH tails at 5% and 10% (task explicit).
# oi_bar: fixed elevated-OI threshold — 70th percentile of OI's own trailing
#         90-day distribution ("elevated" = OI meaningfully above its recent
#         normal range; not swept, to keep the grid small as the task's
#         primary axis is the funding percentile).
# k_atr=1.0 stop (1x ATR(14), H1) — a squeeze/unwind thesis expects a fast
# move, so a tighter-than-trend-family stop is the stated, non-tuned choice.
# H=48 bars (H1) = 2 days — funding resets every 8h; an extreme-positioning
# unwind is expected to resolve within a couple of days if it's going to.
GRID = [
    dict(funding_bar=5, oi_bar=70, k_atr=1.0, R=1.5, H=48),
    dict(funding_bar=5, oi_bar=70, k_atr=1.0, R=2.0, H=48),
    dict(funding_bar=10, oi_bar=70, k_atr=1.0, R=1.5, H=48),
    dict(funding_bar=10, oi_bar=70, k_atr=1.0, R=2.0, H=48),
]
