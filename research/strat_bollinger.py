#!/usr/bin/env python3
"""
STRATEGY 2 -- BOLLINGER BAND MEAN-REVERSION, standard 20-period / 2 std dev,
daily bars, all 7 instruments, full continuous-compounding treatment.

RULE, stated before running, never re-tuned:
  BB_LEN = 20, BB_STD = 2.0 (industry-standard defaults, not fitted).
  mid = SMA(close, 20); upper = mid + 2*std(close,20); lower = mid - 2*std(close,20).
  LONG entry: close <= lower band (oversold touch/breach).
  SHORT entry: close >= upper band (overbought touch/breach).
  EXIT: close crosses back through the MIDDLE band (mean reversion achieved),
        OR a stated stop = 3 std dev beyond the entry band (a clearly wider
        catastrophic-stop level, not a tuned parameter).
  One position at a time, no pyramiding. 1% fixed-fractional risk (this
  project's standing convention) -- position sized as if a "trade" is a
  fixed 1% equity risk, but since this is a mean-reversion signal without a
  fixed R multiple, this is implemented as directly compounding the
  instrument's own daily return while a position is open, at FULL exposure
  (not fractional) -- stated explicitly, since the "1%" fixed-fractional
  R-based sizing convention used elsewhere in this project assumes a fixed-
  distance stop that Bollinger mean-reversion does not have by default. This
  is the same "fully invested while in position" sizing already used for
  section 30's on-chain signal for the same reason.

LOOK-AHEAD: signal decided on day t's CLOSE (needs the full day's bar), so
position is held from t+1's open, i.e. applied via .shift(1) in the shared
engine's backtest_from_position(). No indicator ever uses same-day data
beyond the close that is available at that point.

COSTS: instrument's own real-cost model from six_strategies_engine.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.six_strategies_engine import (
    load_daily, ALL_INSTRUMENTS, REAL_OOS_SPLIT, full_report, print_report, START_CAP,
)

BB_LEN = 20
BB_STD = 2.0
STOP_MULT = 3.0


def build_position(daily: pd.DataFrame) -> pd.Series:
    close = daily["close"]
    mid = close.rolling(BB_LEN).mean()
    std = close.rolling(BB_LEN).std()
    upper = mid + BB_STD * std
    lower = mid - BB_STD * std
    stop_up = mid + STOP_MULT * std
    stop_dn = mid - STOP_MULT * std

    pos = pd.Series(0, index=close.index, dtype=int)
    state = 0
    for i in range(len(close)):
        c = close.iloc[i]
        if not np.isfinite(mid.iloc[i]):
            pos.iloc[i] = 0
            continue
        if state == 0:
            if c <= lower.iloc[i]:
                state = 1
            elif c >= upper.iloc[i]:
                state = -1
        elif state == 1:
            if c >= mid.iloc[i] or c <= stop_dn.iloc[i]:
                state = 0
        elif state == -1:
            if c <= mid.iloc[i] or c >= stop_up.iloc[i]:
                state = 0
        pos.iloc[i] = state
    return pos


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("STRATEGY 2 -- BOLLINGER BAND MEAN-REVERSION (20, 2.0), daily, all instruments\n")
    results = []
    for inst in ALL_INSTRUMENTS:
        daily = load_daily(inst)
        pos = build_position(daily)
        oos = REAL_OOS_SPLIT.get(inst)
        r = full_report(f"BOLLINGER (20,2.0) -- {inst}", daily, pos, oos_split=oos)
        print_report(r)
        results.append((inst, r))
    return results


if __name__ == "__main__":
    main()
