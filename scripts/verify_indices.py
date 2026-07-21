#!/usr/bin/env python3
"""Verify the merged index CFD files before the sweep is allowed to run.

Exists because a partial merge silently produced a NAS100 file NAMED
2018_2025 that actually ended 2019-12-31 (386k rows). A backtest reading it
would have quietly tested two years instead of eight and reported the result
as if it covered the full period. This gate makes that failure loud.

Checks per file:
  1. exists and is non-empty
  2. required columns present, including a real `spread`
  3. coverage spans 2018-01 -> 2025-12 (first and last bar, not just row count)
  4. every year 2018..2025 is actually represented
  5. price band is sane for the instrument
  6. spread is positive on the median and not pathologically negative

Exit 0 = both files good, sweep may proceed.
Exit 1 = at least one file bad, caller MUST NOT run the sweep.
"""
import os
import sys

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_COLS = [
    "timestamp", "datetime_utc",
    "bid_open", "bid_high", "bid_low", "bid_close",
    "ask_open", "ask_high", "ask_low", "ask_close",
    "spread", "volume",
]

# name -> (outer price band lo, hi). Deliberately generous: the point of the
# band check is to catch a wrong instrument or a decimal error, NOT to fail on
# a legitimate new high. Actual observed min/max is always printed for eyeball.
#
# NAS100 ceiling raised 25,000 -> 30,000 on 2026-07-21. The 25,000 bound was
# simply set too low and rejected REAL data: NDX ran to 26,255 (2025-10-30) and
# closed 2025 near 25,800. Verified genuine before widening, not assumed —
# monthly maxima climb smoothly (Jul 23.7k, Aug 24.0k, Sep 24.8k, Oct 26.3k),
# 58,011 bars (2.6%) sit above 25,000 and 3,742 above 26,000. A one-bar bad
# print cannot do that. 30,000 still catches the failures this check is for:
# a 10x decimal error lands at ~260,000 and a wrong instrument is nowhere near.
FILES = {
    "NAS100": ("NAS100_M1_2018_2025_cfd_dukascopy.csv", 5500, 30000),
    "US30":   ("US30_M1_2018_2025_cfd_dukascopy.csv", 18000, 50000),
}

FIRST_MUST_BE_ON_OR_BEFORE = pd.Timestamp("2018-01-31", tz="UTC")
LAST_MUST_BE_ON_OR_AFTER = pd.Timestamp("2025-12-01", tz="UTC")
YEARS = list(range(2018, 2026))


def verify(name, fname, lo_exp, hi_exp):
    path = os.path.join(REPO, "data", fname)
    print(f"\n{'='*70}\nVERIFY {name}  ({fname})\n{'='*70}")
    fails = []

    if not os.path.exists(path):
        print("  FAIL: file does not exist.")
        return False
    if os.path.getsize(path) == 0:
        print("  FAIL: file is empty.")
        return False

    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        fails.append(f"missing columns: {missing}")
        print(f"  FAIL: missing columns {missing}")
        return False

    dt = pd.to_datetime(df["datetime_utc"], utc=True)
    first, last = dt.min(), dt.max()
    years_present = sorted(dt.dt.year.unique().tolist())
    missing_years = [y for y in YEARS if y not in years_present]

    lo, hi = float(df["bid_close"].min()), float(df["bid_close"].max())
    med_px = float(df["bid_close"].median())
    med_sp = float(df["spread"].median())
    neg = int((df["spread"] < 0).sum())

    print(f"  rows            : {len(df):,}")
    print(f"  first bar (UTC) : {first}")
    print(f"  last  bar (UTC) : {last}")
    print(f"  years present   : {years_present}")
    print(f"  bid_close range : {lo:,.2f} -> {hi:,.2f}   (median {med_px:,.2f})")
    print(f"  spread med      : {med_sp:.4f} pts = {1e4*med_sp/med_px:.3f} bps of price")
    print(f"  negative spreads: {neg} ({100*neg/len(df):.3f}%)")

    if first > FIRST_MUST_BE_ON_OR_BEFORE:
        fails.append(f"coverage starts too late ({first.date()}, need <= 2018-01-31)")
    if last < LAST_MUST_BE_ON_OR_AFTER:
        fails.append(f"coverage ends too early ({last.date()}, need >= 2025-12-01)")
    if missing_years:
        fails.append(f"years absent from data: {missing_years}")
    if lo < lo_exp or hi > hi_exp:
        fails.append(f"price {lo:,.0f}-{hi:,.0f} outside {name} band {lo_exp:,}-{hi_exp:,}")
    if not (med_sp > 0):
        fails.append(f"median spread not positive ({med_sp})")
    if neg / max(len(df), 1) > 0.01:
        fails.append(f"{100*neg/len(df):.2f}% negative spreads (>1%)")

    if fails:
        print("  --> FAIL")
        for f in fails:
            print(f"      - {f}")
        return False
    print("  --> PASS: full 2018-2025 coverage, spread present, price band sane.")
    return True


def main():
    results = {n: verify(n, *v) for n, v in FILES.items()}
    print(f"\n{'='*70}")
    for n, ok in results.items():
        print(f"  {n:>7}: {'PASS' if ok else 'FAIL'}")
    if all(results.values()):
        print("  ALL FILES VERIFIED — sweep may proceed.")
        print("=" * 70)
        return 0
    print("  VERIFICATION FAILED — sweep will NOT run. Fix the data first.")
    print("=" * 70)
    return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
