#!/usr/bin/env python3
"""
STRATEGY 6 -- ICHIMOKU CLOUD, standard 9/26/52, daily bars, all 7
instruments, full continuous-compounding treatment.

RULE, stated before running, never re-tuned:
  Tenkan-sen (9)  = (highest high(9) + lowest low(9)) / 2
  Kijun-sen (26)  = (highest high(26) + lowest low(26)) / 2
  Senkou Span A   = (Tenkan + Kijun) / 2, plotted 26 periods FORWARD
  Senkou Span B   = (highest high(52) + lowest low(52)) / 2, plotted 26 forward
  Cloud (Kumo) at day t = Span A/B values COMPUTED 26 days ago (i.e. the
  cloud visible at t was calculated from data available at t-26, so using
  it at t is NOT look-ahead -- it is a lagging plot by construction, the
  standard Ichimoku convention. Implemented here explicitly via .shift(26)
  rather than assumed.
  LONG entry: close > cloud (max(Span A, Span B) at t) AND Tenkan crosses
              above Kijun.
  SHORT entry: close < cloud (min(Span A, Span B) at t) AND Tenkan crosses
              below Kijun.
  EXIT: opposite cloud condition (price crosses back through the cloud) OR
  the Tenkan/Kijun reverse-crosses -- exit as soon as EITHER condition
  fires (stated: whichever the brief's "opposite cloud condition or stated
  stop" is read as -- here, cloud-cross is the exit trigger, checked every
  bar, no separate fixed stop).
  One position at a time, full exposure while open (trend-following
  system, not a fixed-R setup, same convention as MACD/Bollinger above).

LOOK-AHEAD: the whole point of the shift(26) is to guarantee the cloud used
at day t was fully computable using data through day t-26. Position itself
is further shifted by 1 day (engine convention) before being applied to
day t+1's return.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.six_strategies_engine import (
    load_daily, ALL_INSTRUMENTS, REAL_OOS_SPLIT, full_report, print_report,
)

TENKAN_LEN, KIJUN_LEN, SENKOU_B_LEN, DISPLACEMENT = 9, 26, 52, 26


def build_position(daily: pd.DataFrame) -> pd.Series:
    high, low, close = daily["high"], daily["low"], daily["close"]
    tenkan = (high.rolling(TENKAN_LEN).max() + low.rolling(TENKAN_LEN).min()) / 2
    kijun = (high.rolling(KIJUN_LEN).max() + low.rolling(KIJUN_LEN).min()) / 2
    span_a = ((tenkan + kijun) / 2).shift(DISPLACEMENT)
    span_b = ((high.rolling(SENKOU_B_LEN).max() + low.rolling(SENKOU_B_LEN).min()) / 2).shift(DISPLACEMENT)
    cloud_top = pd.concat([span_a, span_b], axis=1).max(axis=1)
    cloud_bot = pd.concat([span_a, span_b], axis=1).min(axis=1)

    tk_cross_up = (tenkan > kijun) & (tenkan.shift(1) <= kijun.shift(1))
    tk_cross_dn = (tenkan < kijun) & (tenkan.shift(1) >= kijun.shift(1))

    pos = pd.Series(0, index=close.index, dtype=int)
    state = 0
    for i in range(len(close)):
        if not (np.isfinite(cloud_top.iloc[i]) and np.isfinite(cloud_bot.iloc[i]) and np.isfinite(tenkan.iloc[i])):
            pos.iloc[i] = 0
            continue
        c = close.iloc[i]
        if state == 0:
            if c > cloud_top.iloc[i] and tk_cross_up.iloc[i]:
                state = 1
            elif c < cloud_bot.iloc[i] and tk_cross_dn.iloc[i]:
                state = -1
        elif state == 1:
            if c < cloud_bot.iloc[i] or tk_cross_dn.iloc[i]:
                state = 0
        elif state == -1:
            if c > cloud_top.iloc[i] or tk_cross_up.iloc[i]:
                state = 0
        pos.iloc[i] = state
    return pos


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("STRATEGY 6 -- ICHIMOKU CLOUD (9,26,52), daily, all instruments\n")
    results = []
    for inst in ALL_INSTRUMENTS:
        daily = load_daily(inst)
        pos = build_position(daily)
        oos = REAL_OOS_SPLIT.get(inst)
        r = full_report(f"ICHIMOKU (9,26,52) -- {inst}", daily, pos, oos_split=oos)
        print_report(r)
        results.append((inst, r))
    return results


if __name__ == "__main__":
    main()
