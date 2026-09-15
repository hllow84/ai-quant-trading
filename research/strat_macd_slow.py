#!/usr/bin/env python3
"""
SLOWER, TREND-HOLDING MACD VARIANT -- BTCUSDT/ETHUSDT, daily, follow-up to
the standard 12/26/9 always-in-market crossover already tested
(research/strat_macd.py, results/strat_macd_run.log: BTCUSDT +3.1%,
ETHUSDT +3.2%, both losing decisively to their own buy-and-hold). This is a
GENUINELY DIFFERENT rule, not a re-label: long-only, holds THROUGH minor
whipsaws inside a positive-histogram regime, and only exits after a stated
run of consecutive negative-histogram bars, rather than reversing on every
single crossover.

RULE, stated before running, no re-tuning after seeing results:
  EMA_FAST=12, EMA_SLOW=26, SIGNAL=9 -- UNCHANGED from the fast-crossover
  test (no re-optimization of the MACD parameters themselves; only the
  entry/exit LOGIC around the same indicator changes).
  histogram = MACD line - signal line (same definition as before).
  ENTRY (long only, no short leg -- stated, the brief's "stay LONG" framing):
      histogram > 0 today (after being <= 0 the prior day) -> go long,
      applied from the NEXT bar via the shared engine's shift(1) convention.
  HOLD: stay long through ANY number of individual negative-histogram bars,
      as long as they do not reach the exit threshold below -- this is the
      entire point of the variant (do not exit on the first whipsaw).
  EXIT: histogram has been <= 0 for >= MIN_CONSEC_NEG_BARS consecutive bars
      -> flat (cash), no short position taken.
  MIN_CONSEC_NEG_BARS tested: {1, 3, 5} -- 1 is the degenerate case (exits
      on the very first negative bar, i.e. as fast as the original
      crossover's exit side, but STILL long-only/no-short, so even this is
      not identical to the original always-in-market test); 3 and 5 are the
      genuinely slower, noise-filtered versions the task asks for.
  SIZING: full exposure while in a long position, 100% cash (no cost, no
      return) otherwise -- same convention as every other non-fixed-R
      system in this batch (Bollinger/MACD/Ichimoku), stated in
      six_strategies_engine.py's module docstring.

LOOK-AHEAD: histogram value used for day t's decision is computed from data
through day t's own close (needs the full day's bar, same as the original
MACD test); the resulting position is applied to day t+1's return via the
shared engine's position.shift(1), so no future information ever enters a
decision.

COSTS: crypto cost model (20 bps commission), same as every other crypto
cell in this project.

OUT-OF-REGIME: NOT available for BTCUSDT/ETHUSDT -- no real pre-2018
real-cost window exists in this project (Binance data starts 2017-08-17,
already stated as a standing constraint in sections 28/30). Stated here
again rather than silently worked around.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.six_strategies_engine import load_daily, full_report, print_report

EMA_FAST, EMA_SLOW, SIGNAL_LEN = 12, 26, 9
MIN_CONSEC_NEG_BARS_OPTIONS = [1, 3, 5]
INSTRUMENTS = ["BTCUSDT", "ETHUSDT"]


def build_position(daily: pd.DataFrame, min_consec_neg: int) -> pd.Series:
    close = daily["close"]
    macd = close.ewm(span=EMA_FAST, adjust=False).mean() - close.ewm(span=EMA_SLOW, adjust=False).mean()
    signal = macd.ewm(span=SIGNAL_LEN, adjust=False).mean()
    hist = macd - signal
    warmup = EMA_SLOW + SIGNAL_LEN

    pos = pd.Series(0, index=close.index, dtype=int)
    state = 0          # 0 = flat, 1 = long
    neg_run = 0
    for i in range(len(close)):
        if i < warmup:
            pos.iloc[i] = 0
            continue
        h = hist.iloc[i]
        if h > 0:
            neg_run = 0
            if state == 0:
                state = 1
        else:
            neg_run += 1
            if state == 1 and neg_run >= min_consec_neg:
                state = 0
        pos.iloc[i] = state
    return pos


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("SLOWER MACD (12,26,9), long-only, holds through whipsaws, exits after "
          "N consecutive negative-histogram bars (N in {1,3,5}) -- BTCUSDT/ETHUSDT\n")
    results = []
    for inst in INSTRUMENTS:
        daily = load_daily(inst)
        for n in MIN_CONSEC_NEG_BARS_OPTIONS:
            pos = build_position(daily, n)
            r = full_report(f"SLOW MACD (exit after {n} consec neg-hist bar(s)) -- {inst}", daily, pos)
            print_report(r)
            results.append((inst, n, r))
    return results


if __name__ == "__main__":
    main()
