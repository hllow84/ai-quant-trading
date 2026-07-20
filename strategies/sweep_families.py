"""
sweep_families.py — Five simple, explainable, defined-risk strategy families,
fully VECTORIZED (no per-bar Python loops) so they run across M5..H4 quickly.

Uniform conventions for the sweep (stated once, applied everywhere):
  - Signals + resolution on the SAME execution timeframe (engine strictly_after=True).
  - Every entry is rising-edge (fires only on the first bar of a setup), defined-risk
    (hard stop), fixed R-multiple target, and a max-hold time cap of H bars.
  - Session-agnostic (no intraday session filter) so families are comparable across
    timeframes. This means multi-bar / overnight holds are allowed — FTMO overnight
    rules are reported as context, not as the edge test.
  - ATR period = 14 (execution TF). Risk (1R) = stop distance in price. 1% risk/trade
    is applied in the engine. NO per-config optimization — 2-3 STATED variants/family.

Each builder returns a list of candidate trade dicts for research.ftmo_engine.simulate_trades.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.ftmo_gold import ema, atr


def _emit(idx, mask, side, entry, stop, target, sess_end):
    """Build trade dicts from vectorized arrays at the rising-edge entry bars."""
    m = (mask & ~mask.shift(1, fill_value=False)).to_numpy()
    pos = np.flatnonzero(m)
    e, s, t = entry.to_numpy(), stop.to_numpy(), target.to_numpy()
    out = []
    for i in pos:
        st, tg, en = s[i], t[i], e[i]
        if np.isnan(st) or np.isnan(tg) or np.isnan(en):
            continue
        if (side == "long" and st >= en) or (side == "short" and st <= en):
            continue  # malformed stop
        out.append(dict(entry_time=idx[i], side=side, entry_mid=float(en),
                        stop=float(st), target=float(tg), session_end=sess_end[i]))
    return out


def _sess_end(idx, H, tf_delta):
    return (idx + H * tf_delta)


# ── Family 1: Trend-continuation (HTF-ish filter + pullback) ────────────────────
def trend_continuation(m, p, tf_delta):
    c, o = m["mid_close"], m["mid_open"]
    a = atr(m, 14)
    et = ema(c, p["ema_trend"]); ef = ema(c, p["ema_fast"]); ep = ema(c, p["ema_pull"])
    se = pd.Series(_sess_end(m.index, p["H"], tf_delta), index=m.index)
    swing_lo = m["mid_low"].rolling(p["swing"], min_periods=p["swing"]).min()
    swing_hi = m["mid_high"].rolling(p["swing"], min_periods=p["swing"]).max()

    long_bias  = (c > et) & (ef > et)
    short_bias = (c < et) & (ef < et)
    long_e  = long_bias  & (m["mid_low"] <= ep) & (c > ep) & (c > o)
    short_e = short_bias & (m["mid_high"] >= ep) & (c < ep) & (c < o)

    l_stop = swing_lo - p["k_atr"] * a
    s_stop = swing_hi + p["k_atr"] * a
    l_tgt = c + p["R"] * (c - l_stop)
    s_tgt = c - p["R"] * (s_stop - c)
    return (_emit(m.index, long_e, "long", c, l_stop, l_tgt, se.to_numpy())
            + _emit(m.index, short_e, "short", c, s_stop, s_tgt, se.to_numpy()))


# ── Family 2: Breakout-retest (prior N-bar level, one-bar retest proxy) ─────────
def breakout_retest(m, p, tf_delta):
    c = m["mid_close"]; a = atr(m, 14)
    se = _sess_end(m.index, p["H"], tf_delta)
    hi = m["mid_high"].rolling(p["N"], min_periods=p["N"]).max().shift(1)
    lo = m["mid_low"].rolling(p["N"], min_periods=p["N"]).min().shift(1)

    long_e  = (c > hi) & (m["mid_low"] <= hi)     # closed above prior high after wicking to it
    short_e = (c < lo) & (m["mid_high"] >= lo)
    l_stop = hi - p["k_atr"] * a
    s_stop = lo + p["k_atr"] * a
    l_tgt = c + p["R"] * (c - l_stop)
    s_tgt = c - p["R"] * (s_stop - c)
    return (_emit(m.index, long_e, "long", c, l_stop, l_tgt, se)
            + _emit(m.index, short_e, "short", c, s_stop, s_tgt, se))


# ── Family 3: Mean-reversion (fade k*ATR extension from an EMA) ─────────────────
def mean_reversion(m, p, tf_delta):
    c, o = m["mid_close"], m["mid_open"]; a = atr(m, 14)
    se = _sess_end(m.index, p["H"], tf_delta)
    mean = ema(c, p["N"])
    swing_hi = m["mid_high"].rolling(p["swing"], min_periods=1).max()
    swing_lo = m["mid_low"].rolling(p["swing"], min_periods=1).min()

    ext_up = c > (mean + p["k_ext"] * a)
    ext_dn = c < (mean - p["k_ext"] * a)
    short_e = ext_up & (c < o)     # fade up-extension on a bearish bar
    long_e  = ext_dn & (c > o)     # fade down-extension on a bullish bar
    s_stop = swing_hi + p["k_atr"] * a
    l_stop = swing_lo - p["k_atr"] * a
    s_tgt = c - p["R"] * (s_stop - c)
    l_tgt = c + p["R"] * (c - l_stop)
    return (_emit(m.index, long_e, "long", c, l_stop, l_tgt, se)
            + _emit(m.index, short_e, "short", c, s_stop, s_tgt, se))


# ── Family 4: Momentum (sign of close - close[N], ride direction) ───────────────
def momentum(m, p, tf_delta):
    c = m["mid_close"]; a = atr(m, 14)
    se = _sess_end(m.index, p["H"], tf_delta)
    mom = c - c.shift(p["N"])
    long_e  = (mom > 0) & (mom.shift(1) <= 0)
    short_e = (mom < 0) & (mom.shift(1) >= 0)
    risk = p["k_atr"] * a
    l_stop = c - risk; s_stop = c + risk
    l_tgt = c + p["R"] * risk; s_tgt = c - p["R"] * risk
    return (_emit(m.index, long_e, "long", c, l_stop, l_tgt, se)
            + _emit(m.index, short_e, "short", c, s_stop, s_tgt, se))


# ── Family 5: MA-cross with trend filter ───────────────────────────────────────
def ma_cross(m, p, tf_delta):
    c = m["mid_close"]; a = atr(m, 14)
    se = _sess_end(m.index, p["H"], tf_delta)
    ef = ema(c, p["fast"]); es = ema(c, p["slow"]); et = ema(c, p["ema_trend"])
    cross_up = (ef > es) & (ef.shift(1) <= es.shift(1))
    cross_dn = (ef < es) & (ef.shift(1) >= es.shift(1))
    long_e  = cross_up & (c > et)
    short_e = cross_dn & (c < et)
    risk = p["k_atr"] * a
    l_stop = c - risk; s_stop = c + risk
    l_tgt = c + p["R"] * risk; s_tgt = c - p["R"] * risk
    return (_emit(m.index, long_e, "long", c, l_stop, l_tgt, se)
            + _emit(m.index, short_e, "short", c, s_stop, s_tgt, se))


# ── Variant registry (family -> list of stated parameter sets) ──────────────────
FAMILIES = {
    "trend": (trend_continuation, [
        dict(ema_trend=200, ema_fast=50, ema_pull=20, swing=5,  k_atr=0.5, R=2.0, H=24),
        dict(ema_trend=200, ema_fast=50, ema_pull=20, swing=10, k_atr=0.5, R=1.5, H=48),
        dict(ema_trend=100, ema_fast=30, ema_pull=10, swing=5,  k_atr=1.0, R=3.0, H=48),
    ]),
    "breakout": (breakout_retest, [
        dict(N=20, k_atr=1.0, R=2.0, H=24),
        dict(N=50, k_atr=1.0, R=2.0, H=48),
        dict(N=20, k_atr=1.5, R=1.5, H=24),
    ]),
    "meanrev": (mean_reversion, [
        dict(N=20, k_ext=2.0, swing=3, k_atr=0.5, R=1.5, H=24),
        dict(N=20, k_ext=2.5, swing=3, k_atr=0.5, R=1.0, H=12),
        dict(N=50, k_ext=2.0, swing=5, k_atr=1.0, R=1.5, H=24),
    ]),
    "momentum": (momentum, [
        dict(N=24, k_atr=2.0, R=2.0, H=48),
        dict(N=48, k_atr=2.0, R=2.0, H=96),
        dict(N=12, k_atr=1.5, R=1.5, H=24),
    ]),
    "macross": (ma_cross, [
        dict(fast=10, slow=30, ema_trend=200, k_atr=2.0, R=2.0, H=48),
        dict(fast=20, slow=50, ema_trend=200, k_atr=2.0, R=2.0, H=96),
        dict(fast=10, slow=30, ema_trend=100, k_atr=1.5, R=3.0, H=48),
    ]),
}

TIMEFRAMES = {"M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h", "H4": "4h"}
TF_DELTA = {
    "M5": pd.Timedelta(minutes=5), "M15": pd.Timedelta(minutes=15),
    "M30": pd.Timedelta(minutes=30), "H1": pd.Timedelta(hours=1),
    "H4": pd.Timedelta(hours=4),
}
