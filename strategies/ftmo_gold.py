"""
ftmo_gold.py — Three simple, explainable, FTMO-shaped XAUUSD strategies.

All timestamps UTC. All bars use label='right', closed='left' (a bar labeled T
is fully known at T), so entering at a signal bar's close uses no future data.

SHARED RULES (FTMO shaping):
  - Intraday only. No overnight holds: every trade is force-flat at a session end
    time the same day (time-exit). Defined risk (hard stop) on every trade.
  - Entries only inside an active session window (stated per strategy, UTC).
  - Fixed-R target; hard stop = invalidation. 1% risk per trade (in the engine).
  - NO parameter optimization. Defaults are stated once and tested once.

Each builder returns a list of candidate trade dicts consumable by
research.ftmo_engine.simulate_trades. Overlap (one-position-at-a-time) and cost
handling are applied downstream in the engine.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ── shared helpers ──────────────────────────────────────────────────────────────

def ema(s: pd.Series, span: int) -> pd.Series:
    return s.ewm(span=span, adjust=False).mean()


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """Average true range on mid OHLC."""
    prev_close = df["mid_close"].shift(1)
    tr = pd.concat([
        df["mid_high"] - df["mid_low"],
        (df["mid_high"] - prev_close).abs(),
        (df["mid_low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()


def _tod(ts: pd.Timestamp) -> int:
    """Minutes since UTC midnight."""
    return ts.hour * 60 + ts.minute


def _session_end(ts: pd.Timestamp, hour: int) -> pd.Timestamp:
    """Force-flat timestamp at `hour`:00 UTC on the same calendar day as ts."""
    return ts.normalize() + pd.Timedelta(hours=hour)


# ── Strategy A: TREND-CONTINUATION (H1 trend, M15 pullback) ─────────────────────
# Session (UTC): entries 07:00-20:00, force-flat 21:00.
# Trend filter : H1 EMA50 vs EMA200. Long-bias if EMA50>EMA200 and close>EMA50.
# Entry (long) : in long-bias, M15 bar dips to/through EMA20 (low<=EMA20) and
#                closes back above it with a bullish body (close>open, close>EMA20).
# Stop         : recent swing low (min low, last 5 M15 bars) minus 0.10*ATR14.
# Target       : 2R.
A_H1_FAST, A_H1_SLOW = 50, 200
A_M15_EMA            = 20
A_SWING_LOOKBACK     = 5
A_ATR_BUF            = 0.10
A_TARGET_R           = 2.0
A_SESS_START, A_SESS_LAST_ENTRY, A_SESS_END = 7, 20, 21


def build_trend_continuation(m15: pd.DataFrame, h1: pd.DataFrame) -> list[dict]:
    h1 = h1.copy()
    h1["ema_f"] = ema(h1["mid_close"], A_H1_FAST)
    h1["ema_s"] = ema(h1["mid_close"], A_H1_SLOW)
    long_bias  = (h1["ema_f"] > h1["ema_s"]) & (h1["mid_close"] > h1["ema_f"])
    short_bias = (h1["ema_f"] < h1["ema_s"]) & (h1["mid_close"] < h1["ema_f"])

    m = m15.copy()
    m["ema20"] = ema(m["mid_close"], A_M15_EMA)
    m["atr"]   = atr(m, 14)
    # last CLOSED H1 bias at each M15 bar (right-edge labels -> ffill is causal)
    m["long_bias"]  = long_bias.reindex(m.index, method="ffill").fillna(False)
    m["short_bias"] = short_bias.reindex(m.index, method="ffill").fillna(False)
    m["swing_low"]  = m["mid_low"].rolling(A_SWING_LOOKBACK, min_periods=A_SWING_LOOKBACK).min()
    m["swing_high"] = m["mid_high"].rolling(A_SWING_LOOKBACK, min_periods=A_SWING_LOOKBACK).max()

    trades = []
    for ts, row in m.iterrows():
        tod = _tod(ts)
        if not (A_SESS_START * 60 <= tod < A_SESS_LAST_ENTRY * 60):
            continue
        if np.isnan(row["ema20"]) or np.isnan(row["atr"]) or np.isnan(row["swing_low"]):
            continue
        entry = float(row["mid_close"])
        buf   = A_ATR_BUF * float(row["atr"])
        # LONG pullback
        if (row["long_bias"] and row["mid_low"] <= row["ema20"]
                and row["mid_close"] > row["ema20"] and row["mid_close"] > row["mid_open"]):
            stop = float(row["swing_low"]) - buf
            if stop < entry:
                trades.append(dict(entry_time=ts, side="long", entry_mid=entry,
                                   stop=stop, target=entry + A_TARGET_R * (entry - stop),
                                   session_end=_session_end(ts, A_SESS_END)))
        # SHORT pullback
        elif (row["short_bias"] and row["mid_high"] >= row["ema20"]
                and row["mid_close"] < row["ema20"] and row["mid_close"] < row["mid_open"]):
            stop = float(row["swing_high"]) + buf
            if stop > entry:
                trades.append(dict(entry_time=ts, side="short", entry_mid=entry,
                                   stop=stop, target=entry - A_TARGET_R * (stop - entry),
                                   session_end=_session_end(ts, A_SESS_END)))
    return trades


# ── Strategy B: BREAKOUT-RETEST (London opening range) ──────────────────────────
# Session (UTC): opening range 07:00-08:00; entries on retest 08:00-16:00;
#                force-flat 20:00.
# Setup (long) : after a M15 close ABOVE the OR high, wait for a pullback that
#                touches the OR high (low<=OR_high) and closes back above it -> enter.
# Stop         : OR_high - max(0.15*range, 0.5*ATR14)  (just beyond the broken level).
# Target       : 2R. First valid retest per side per day only.
B_OR_START, B_OR_END = 7, 8          # opening range window (UTC hours)
B_ENTRY_LAST         = 16            # last entry hour
B_SESS_END           = 20
B_RANGE_BUF          = 0.15
B_ATR_BUF            = 0.5
B_TARGET_R           = 2.0


def build_breakout_retest(m15: pd.DataFrame) -> list[dict]:
    m = m15.copy()
    m["atr"] = atr(m, 14)
    m["day"] = m.index.normalize()

    trades = []
    for day, g in m.groupby("day"):
        orb = g[(g.index.map(_tod) > B_OR_START * 60) & (g.index.map(_tod) <= B_OR_END * 60)]
        if len(orb) < 2:
            continue
        or_high = float(orb["mid_high"].max())
        or_low  = float(orb["mid_low"].min())
        rng = or_high - or_low
        if rng <= 0:
            continue

        post = g[(g.index.map(_tod) > B_OR_END * 60) & (g.index.map(_tod) < B_ENTRY_LAST * 60)]
        armed_long = armed_short = False
        done_long = done_short = False
        for ts, row in post.iterrows():
            if np.isnan(row["atr"]):
                continue
            buf = max(B_RANGE_BUF * rng, B_ATR_BUF * float(row["atr"]))
            # arm on breakout close beyond the level
            if row["mid_close"] > or_high:
                armed_long = True
            if row["mid_close"] < or_low:
                armed_short = True
            entry = float(row["mid_close"])
            # LONG retest: pull back to the level, close back above
            if (armed_long and not done_long and row["mid_low"] <= or_high
                    and row["mid_close"] > or_high):
                stop = or_high - buf
                if stop < entry:
                    trades.append(dict(entry_time=ts, side="long", entry_mid=entry,
                                       stop=stop, target=entry + B_TARGET_R * (entry - stop),
                                       session_end=_session_end(ts, B_SESS_END)))
                    done_long = True
            # SHORT retest
            if (armed_short and not done_short and row["mid_high"] >= or_low
                    and row["mid_close"] < or_low):
                stop = or_low + buf
                if stop > entry:
                    trades.append(dict(entry_time=ts, side="short", entry_mid=entry,
                                       stop=stop, target=entry - B_TARGET_R * (stop - entry),
                                       session_end=_session_end(ts, B_SESS_END)))
                    done_short = True
    return trades


# ── Strategy C: MEAN-REVERSION at prior-day high/low ────────────────────────────
# Session (UTC): entries 07:00-20:00; force-flat 21:00.
# Setup (short): M15 bar pokes ABOVE prior-day high (high>PDH) then closes back
#                below it (close<PDH) -> fade short. Stop above the poke; target 1.5R.
# Setup (long) : mirror at prior-day low. First fade per level per day.
C_TARGET_R           = 1.5
C_POKE_LOOKBACK      = 2
C_ATR_BUF            = 0.10
C_SESS_START, C_SESS_LAST_ENTRY, C_SESS_END = 7, 20, 21


def build_mean_reversion(m15: pd.DataFrame, daily: pd.DataFrame) -> list[dict]:
    # prior-day mid high/low (shift(1) -> strictly prior, causal)
    pdh = daily["mid_high"].shift(1)
    pdl = daily["mid_low"].shift(1)

    m = m15.copy()
    m["atr"] = atr(m, 14)
    m["day"] = m.index.normalize()
    m["pdh"] = m["day"].map(pdh.to_dict())
    m["pdl"] = m["day"].map(pdl.to_dict())
    m["hh2"] = m["mid_high"].rolling(C_POKE_LOOKBACK, min_periods=1).max()
    m["ll2"] = m["mid_low"].rolling(C_POKE_LOOKBACK, min_periods=1).min()

    trades = []
    done_short_day: dict = {}
    done_long_day: dict = {}
    for ts, row in m.iterrows():
        tod = _tod(ts)
        if not (C_SESS_START * 60 <= tod < C_SESS_LAST_ENTRY * 60):
            continue
        if np.isnan(row["atr"]) or pd.isna(row["pdh"]) or pd.isna(row["pdl"]):
            continue
        day = row["day"]
        entry = float(row["mid_close"])
        buf = C_ATR_BUF * float(row["atr"])
        # SHORT fade at PDH
        if (not done_short_day.get(day) and row["mid_high"] > row["pdh"]
                and row["mid_close"] < row["pdh"]):
            stop = float(row["hh2"]) + buf
            if stop > entry:
                trades.append(dict(entry_time=ts, side="short", entry_mid=entry,
                                   stop=stop, target=entry - C_TARGET_R * (stop - entry),
                                   session_end=_session_end(ts, C_SESS_END)))
                done_short_day[day] = True
        # LONG fade at PDL
        if (not done_long_day.get(day) and row["mid_low"] < row["pdl"]
                and row["mid_close"] > row["pdl"]):
            stop = float(row["ll2"]) - buf
            if stop < entry:
                trades.append(dict(entry_time=ts, side="long", entry_mid=entry,
                                   stop=stop, target=entry + C_TARGET_R * (entry - stop),
                                   session_end=_session_end(ts, C_SESS_END)))
                done_long_day[day] = True
    return trades
