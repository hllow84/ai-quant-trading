"""
ftmo_gold_swing.py — SWING versions of the three gold archetypes on H4 / Daily.

The intraday (M15) kills were driven by cost-to-risk ratio: stops of ~2 $/oz vs
~0.6 $/oz round-trip cost meant costs were ~30% of every trade's risk. These
swing versions widen the stop (H4/Daily swings, R ~ 15-30 $/oz) so the SAME
$/oz cost becomes ~1-3% of risk. Multi-day holds are allowed.

Signals are generated on H4 and RESOLVED on H4 (simulate_trades(..., strictly_after=True)).
Daily/weekly context is mapped onto H4 causally: higher-timeframe frames are
resampled with label='right' (a bar is known only at its right edge) and then
reindexed onto the H4 index with forward-fill, so each H4 bar sees only the last
COMPLETED daily/weekly bar. No look-ahead by construction.

All timestamps UTC. Defaults are fixed and stated. NO optimization.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from strategies.ftmo_gold import ema, atr  # reuse indicator helpers

MAX_HOLD_DAYS = 30      # force-flat time-exit cap (calendar days) — bounds the hold


def _session_end(ts: pd.Timestamp) -> pd.Timestamp:
    """Time-exit cap: MAX_HOLD_DAYS calendar days after entry."""
    return ts + pd.Timedelta(days=MAX_HOLD_DAYS)


# ── Strategy A (swing): Daily trend, H4 pullback ────────────────────────────────
# Trend : Daily EMA50 vs EMA200. Long-bias if EMA50>EMA200 and close>EMA50.
# Entry : in-bias H4 bar dips to/through EMA20(H4) and closes back across it,
#         with a body in the trade direction.
# Stop  : beyond the H4 swing (min/max low/high of last 5 H4 bars) +/- 0.1*ATR14(H4).
# Target: 2R. Hold: up to 30 days.
A_D_FAST, A_D_SLOW, A_H4_EMA, A_SWING, A_ATR_BUF, A_TARGET_R = 50, 200, 20, 5, 0.10, 2.0


def build_swing_trend(h4: pd.DataFrame, daily: pd.DataFrame) -> list[dict]:
    d = daily.copy()
    d["ema_f"] = ema(d["mid_close"], A_D_FAST)
    d["ema_s"] = ema(d["mid_close"], A_D_SLOW)
    long_bias  = (d["ema_f"] > d["ema_s"]) & (d["mid_close"] > d["ema_f"])
    short_bias = (d["ema_f"] < d["ema_s"]) & (d["mid_close"] < d["ema_f"])

    h = h4.copy()
    h["ema20"] = ema(h["mid_close"], A_H4_EMA)
    h["atr"]   = atr(h, 14)
    h["long_bias"]  = long_bias.reindex(h.index, method="ffill").fillna(False)
    h["short_bias"] = short_bias.reindex(h.index, method="ffill").fillna(False)
    h["swing_low"]  = h["mid_low"].rolling(A_SWING, min_periods=A_SWING).min()
    h["swing_high"] = h["mid_high"].rolling(A_SWING, min_periods=A_SWING).max()

    trades = []
    for ts, row in h.iterrows():
        if np.isnan(row["ema20"]) or np.isnan(row["atr"]) or np.isnan(row["swing_low"]):
            continue
        entry = float(row["mid_close"])
        buf   = A_ATR_BUF * float(row["atr"])
        if (row["long_bias"] and row["mid_low"] <= row["ema20"]
                and row["mid_close"] > row["ema20"] and row["mid_close"] > row["mid_open"]):
            stop = float(row["swing_low"]) - buf
            if stop < entry:
                trades.append(dict(entry_time=ts, side="long", entry_mid=entry, stop=stop,
                                   target=entry + A_TARGET_R * (entry - stop),
                                   session_end=_session_end(ts)))
        elif (row["short_bias"] and row["mid_high"] >= row["ema20"]
                and row["mid_close"] < row["ema20"] and row["mid_close"] < row["mid_open"]):
            stop = float(row["swing_high"]) + buf
            if stop > entry:
                trades.append(dict(entry_time=ts, side="short", entry_mid=entry, stop=stop,
                                   target=entry - A_TARGET_R * (stop - entry),
                                   session_end=_session_end(ts)))
    return trades


# ── Strategy B (swing): prior-week range breakout, H4 retest ───────────────────
# Level : prior-week high (PWH) / low (PWL).
# Entry : after an H4 close beyond the level, enter on the retest (H4 pulls back to
#         the level and closes back on the breakout side). Stop 1*ATR14(H4) BEYOND
#         the level (a meaningful distance, not a hairline) -> R ~ one H4 ATR.
# Target: 2R. First retest per side per week. Hold: up to 30 days.
B_ATR_BUF, B_TARGET_R = 1.0, 2.0


def build_swing_breakout(h4: pd.DataFrame, weekly: pd.DataFrame) -> list[dict]:
    pwh = weekly["mid_high"].shift(1)
    pwl = weekly["mid_low"].shift(1)

    h = h4.copy()
    h["atr"] = atr(h, 14)
    h["pwh"] = pwh.reindex(h.index, method="ffill")
    h["pwl"] = pwl.reindex(h.index, method="ffill")
    h["week"] = h.index.tz_localize(None).to_period("W").astype(str)

    trades = []
    armed_long = armed_short = False
    done_long = done_short = False
    cur_week = None
    for ts, row in h.iterrows():
        if row["week"] != cur_week:                 # reset per week
            cur_week = row["week"]
            armed_long = armed_short = False
            done_long = done_short = False
        if np.isnan(row["atr"]) or pd.isna(row["pwh"]) or pd.isna(row["pwl"]):
            continue
        entry = float(row["mid_close"])
        buf = B_ATR_BUF * float(row["atr"])
        if row["mid_close"] > row["pwh"]:
            armed_long = True
        if row["mid_close"] < row["pwl"]:
            armed_short = True
        # long retest
        if (armed_long and not done_long and row["mid_low"] <= row["pwh"]
                and row["mid_close"] > row["pwh"]):
            stop = float(row["pwh"]) - buf
            if stop < entry:
                trades.append(dict(entry_time=ts, side="long", entry_mid=entry, stop=stop,
                                   target=entry + B_TARGET_R * (entry - stop),
                                   session_end=_session_end(ts)))
                done_long = True
        # short retest
        if (armed_short and not done_short and row["mid_high"] >= row["pwl"]
                and row["mid_close"] < row["pwl"]):
            stop = float(row["pwl"]) + buf
            if stop > entry:
                trades.append(dict(entry_time=ts, side="short", entry_mid=entry, stop=stop,
                                   target=entry - B_TARGET_R * (stop - entry),
                                   session_end=_session_end(ts)))
                done_short = True
    return trades


# ── Strategy C (swing): fade a 2-ATR Daily extension from the mean ─────────────
# Extreme: Daily close > SMA20 + 2*ATR20 (over-extended up) or < SMA20 - 2*ATR20.
# Entry  : in an over-extended state, fade on the first H4 rejection bar
#          (bearish body against an up-extension / bullish body against a down-one).
# Stop   : beyond the recent H4 swing extreme (last 3 H4 bars) +/- 0.2*ATR14(H4).
# Target : 1.5R. First fade per side per day. Hold: up to 30 days.
C_SMA, C_ATR_D, C_K, C_SWING, C_ATR_BUF, C_TARGET_R = 20, 20, 2.0, 3, 0.20, 1.5


def build_swing_meanrev(h4: pd.DataFrame, daily: pd.DataFrame) -> list[dict]:
    d = daily.copy()
    d["mean"] = d["mid_close"].rolling(C_SMA, min_periods=C_SMA).mean()
    d["atrd"] = atr(d, C_ATR_D)
    over_up   = d["mid_close"] > (d["mean"] + C_K * d["atrd"])
    over_down = d["mid_close"] < (d["mean"] - C_K * d["atrd"])

    h = h4.copy()
    h["atr"] = atr(h, 14)
    h["over_up"]   = over_up.reindex(h.index, method="ffill").fillna(False)
    h["over_down"] = over_down.reindex(h.index, method="ffill").fillna(False)
    h["hh3"] = h["mid_high"].rolling(C_SWING, min_periods=1).max()
    h["ll3"] = h["mid_low"].rolling(C_SWING, min_periods=1).min()
    h["day"] = h.index.normalize()

    trades = []
    done_short_day: dict = {}
    done_long_day: dict = {}
    for ts, row in h.iterrows():
        if np.isnan(row["atr"]):
            continue
        day = row["day"]
        entry = float(row["mid_close"])
        buf = C_ATR_BUF * float(row["atr"])
        # fade an up-extension -> short on a bearish H4 bar
        if (row["over_up"] and not done_short_day.get(day)
                and row["mid_close"] < row["mid_open"]):
            stop = float(row["hh3"]) + buf
            if stop > entry:
                trades.append(dict(entry_time=ts, side="short", entry_mid=entry, stop=stop,
                                   target=entry - C_TARGET_R * (stop - entry),
                                   session_end=_session_end(ts)))
                done_short_day[day] = True
        # fade a down-extension -> long on a bullish H4 bar
        if (row["over_down"] and not done_long_day.get(day)
                and row["mid_close"] > row["mid_open"]):
            stop = float(row["ll3"]) - buf
            if stop < entry:
                trades.append(dict(entry_time=ts, side="long", entry_mid=entry, stop=stop,
                                   target=entry + C_TARGET_R * (entry - stop),
                                   session_end=_session_end(ts)))
                done_long_day[day] = True
    return trades
