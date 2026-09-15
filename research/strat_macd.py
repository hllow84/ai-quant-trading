#!/usr/bin/env python3
"""
STRATEGY 3 -- MACD CROSSOVER, standard 12/26/9, daily bars, all 7
instruments, full continuous-compounding treatment.

RULE, stated before running, never re-tuned:
  EMA_FAST = 12, EMA_SLOW = 26, SIGNAL = 9 (the universal textbook default).
  MACD line = EMA(close,12) - EMA(close,26); signal = EMA(MACD,9).
  LONG entry: MACD crosses ABOVE signal.
  SHORT entry: MACD crosses BELOW signal.
  EXIT: the reverse crossover (always in the market, long or short, once
  both EMAs have enough history) -- the standard always-in-market MACD
  crossover system, no separate stop/target (stated, per the brief's "or a
  stated stop/target" being satisfied by "the reverse crossover" as the
  exit rule, the classic form of this system).
  One position at a time. Full exposure while a position is open (this is
  a trend-following always-in-market system, not a fixed-R setup, so it is
  NOT fixed-fractional-R sized -- same convention/reasoning as Bollinger).

LOOK-AHEAD: signal decided on day t's close (EMAs need the full day's
bar), position applied from t+1 via the shared engine's shift(1).
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

EMA_FAST, EMA_SLOW, SIGNAL_LEN = 12, 26, 9


def build_position(daily: pd.DataFrame) -> pd.Series:
    close = daily["close"]
    macd = close.ewm(span=EMA_FAST, adjust=False).mean() - close.ewm(span=EMA_SLOW, adjust=False).mean()
    signal = macd.ewm(span=SIGNAL_LEN, adjust=False).mean()
    pos = pd.Series(np.where(macd > signal, 1, -1), index=close.index)
    warmup = EMA_SLOW + SIGNAL_LEN
    pos.iloc[:warmup] = 0
    return pos


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("STRATEGY 3 -- MACD CROSSOVER (12,26,9), daily, all instruments, always-in-market\n")
    results = []
    for inst in ALL_INSTRUMENTS:
        daily = load_daily(inst)
        pos = build_position(daily)
        oos = REAL_OOS_SPLIT.get(inst)
        r = full_report(f"MACD (12,26,9) -- {inst}", daily, pos, oos_split=oos)
        print_report(r)
        results.append((inst, r))
    return results


if __name__ == "__main__":
    main()
