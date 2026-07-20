"""
htf_swing_breakout.py — HTF-trend-gated swing-level breakout (CONTINUATION).

Alpha story
-----------
Gold trends. When the higher timeframe (H1) is making higher highs AND higher
lows, a close ABOVE the most recent confirmed swing high on the trading
timeframe is a continuation trigger: the market has refused to make a lower
high and has expanded the range in the direction of the established structure.
Mirror for downtrends. This is the "break of structure in the direction of the
trend" idea, tested with hard defined risk and a fixed R target.

EVERY DEFAULT IS STATED HERE. Nothing below is tuned; the only things that vary
across the grid are (trading timeframe, R target, trading-TF pivot N).

Fixed defaults (identical in every config)
------------------------------------------
  H1 pivot N                : 3   (pivot = extreme of a centred 2N+1 = 7-bar window)
  HTF trend definition      : uptrend  = last confirmed pivot high > previous
                              confirmed pivot high AND last confirmed pivot low >
                              previous confirmed pivot low (HH & HL).
                              downtrend = LH & LL. Anything else = NO TRADE.
  HTF -> trading TF mapping : reindex(method="ffill"). Both frames use
                              label="right", closed="left", so an H1 bar labelled
                              T is fully closed AT T and a trading bar labelled T
                              is also fully closed AT T. The trend state used on
                              trading bar T therefore derives only from H1 bars
                              closed at or before T. Pivot confirmation adds a
                              further N-bar lag (a pivot at i is only visible from
                              i+N). No future H1 bar is ever read.
  Entry                     : CONFIRMED BAR CLOSE only, at that bar's mid close.
                              long  : uptrend   AND close > marked swing high
                              short : downtrend AND close < marked swing low
                              Rising-edge only (first bar of the condition).
  Stop                      : BEYOND THE OPPOSITE SIDE OF THE BREAKOUT BAR.
                              long  : breakout bar mid_low  - 0.1 * ATR(14)
                              short : breakout bar mid_high + 0.1 * ATR(14)
                              The 0.1*ATR buffer is a fixed realism allowance so
                              the stop does not sit exactly on the bar extreme.
                              This distance IS 1R.
  Minimum R                 : 0.25 * ATR(14). A breakout bar with a smaller range
                              than this produces a degenerate (near-zero) stop
                              whose cost_R explodes; such signals are DISCARDED
                              rather than silently traded. Stated, not tuned.
  Target                    : fixed R multiple (grid: 1.5R and 2.0R).
  Max hold                  : H = 48 trading-TF bars, then time-exit at mid close.
  Positions                 : one at a time (enforced by ftmo_engine.de_overlap).
  Risk                      : 1% of equity per trade (ftmo_engine.RISK_PER_TRADE).

Returns candidate trade dicts for research.ftmo_engine.simulate_trades.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.ftmo_gold import atr

# ── fixed, stated constants ────────────────────────────────────────────────────
H1_PIVOT_N   = 3      # N-bar pivots on the H1 trend frame
STOP_BUFFER  = 0.1    # x ATR(14) beyond the breakout bar's opposite extreme
MIN_R_ATR    = 0.25   # x ATR(14) minimum allowed stop distance
MAX_HOLD     = 48     # trading-TF bars
ATR_PERIOD   = 14


# ── pivot machinery ────────────────────────────────────────────────────────────

def _pivot_mask(s: pd.Series, n: int, high: bool) -> pd.Series:
    """
    True where bar i is the extreme of the centred window [i-n, i+n].
    NOTE: this is a *centred* (non-causal) mask by construction — it is only ever
    consumed through _confirmed(), which shifts it forward by n bars so a pivot is
    not visible until n bars after it printed.
    """
    w = 2 * n + 1
    roll = s.rolling(w, center=True, min_periods=w).max() if high else \
           s.rolling(w, center=True, min_periods=w).min()
    return (s == roll) & roll.notna()


def _confirmed(price: pd.Series, mask: pd.Series, n: int):
    """
    Causal view of pivots.

    Returns (last, prev): at bar t, `last` is the price of the most recent pivot
    CONFIRMED at or before t (i.e. a pivot that printed at or before t-n), and
    `prev` is the one before that. Both are forward-filled step functions.
    """
    at_conf = price.where(mask).shift(n)      # pivot price appears at its confirmation bar
    sparse = at_conf.dropna()
    last = at_conf.ffill()
    prev = sparse.shift(1).reindex(price.index).ffill()
    return last, prev


def h1_trend(h1: pd.DataFrame, n: int = H1_PIVOT_N) -> pd.Series:
    """+1 uptrend (HH & HL), -1 downtrend (LH & LL), 0 otherwise. Causal."""
    ph_last, ph_prev = _confirmed(h1["mid_high"], _pivot_mask(h1["mid_high"], n, True), n)
    pl_last, pl_prev = _confirmed(h1["mid_low"], _pivot_mask(h1["mid_low"], n, False), n)
    up = (ph_last > ph_prev) & (pl_last > pl_prev)
    dn = (ph_last < ph_prev) & (pl_last < pl_prev)
    return pd.Series(np.where(up, 1, np.where(dn, -1, 0)), index=h1.index, dtype=float)


# ── strategy builder ───────────────────────────────────────────────────────────

def htf_swing_breakout(m: pd.DataFrame, p: dict, tf_delta: pd.Timedelta,
                       trend_h1: pd.Series) -> list[dict]:
    """
    m         : trading-timeframe mid OHLC frame (mid_open/high/low/close, spread)
    p         : dict(N=<trading-TF pivot N>, R=<target R multiple>)
    trend_h1  : H1 trend series from h1_trend(), mapped in here causally
    """
    n = p["N"]
    c, hi, lo = m["mid_close"], m["mid_high"], m["mid_low"]
    a = atr(m, ATR_PERIOD)

    # causal HTF trend on the trading index (see module docstring for why ffill is safe)
    trend = trend_h1.reindex(m.index, method="ffill").fillna(0.0)

    # marked zone: most recent CONFIRMED swing high / low on the trading TF
    sw_hi, _ = _confirmed(hi, _pivot_mask(hi, n, True), n)
    sw_lo, _ = _confirmed(lo, _pivot_mask(lo, n, False), n)

    long_e  = (trend > 0) & (c > sw_hi)
    short_e = (trend < 0) & (c < sw_lo)

    # stop beyond the opposite side of the breakout bar
    l_stop = lo - STOP_BUFFER * a
    s_stop = hi + STOP_BUFFER * a

    min_r = MIN_R_ATR * a
    long_e = long_e & ((c - l_stop) >= min_r)
    short_e = short_e & ((s_stop - c) >= min_r)

    l_tgt = c + p["R"] * (c - l_stop)
    s_tgt = c - p["R"] * (s_stop - c)
    sess_end = (m.index + MAX_HOLD * tf_delta).to_numpy()

    return (_emit(m.index, long_e, "long", c, l_stop, l_tgt, sess_end)
            + _emit(m.index, short_e, "short", c, s_stop, s_tgt, sess_end))


def _emit(idx, mask, side, entry, stop, target, sess_end) -> list[dict]:
    """Rising-edge trade dicts (first bar of the condition only)."""
    m = (mask & ~mask.shift(1, fill_value=False)).to_numpy()
    e, s, t = entry.to_numpy(), stop.to_numpy(), target.to_numpy()
    out = []
    for i in np.flatnonzero(m):
        st, tg, en = s[i], t[i], e[i]
        if np.isnan(st) or np.isnan(tg) or np.isnan(en):
            continue
        if (side == "long" and st >= en) or (side == "short" and st <= en):
            continue
        out.append(dict(entry_time=idx[i], side=side, entry_mid=float(en),
                        stop=float(st), target=float(tg), session_end=sess_end[i]))
    return out


# ── stated grid ────────────────────────────────────────────────────────────────
# 3 timeframes x 2 R targets x 2 pivot settings = 12 configs.
TIMEFRAMES = {"M5": "5min", "M15": "15min", "M30": "30min"}
TF_DELTA = {"M5": pd.Timedelta(minutes=5),
            "M15": pd.Timedelta(minutes=15),
            "M30": pd.Timedelta(minutes=30)}
PIVOT_N = [3, 5]
R_TARGETS = [1.5, 2.0]
