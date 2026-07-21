#!/usr/bin/env python3
"""Verify the six H1 basket files before the sweep is allowed to run.

Same hard-gate role as scripts/verify_indices.py, applied to the H1 base files.
A partial merge once produced a file NAMED 2018_2025 that held only two years;
the sweep must never silently run on that.

Exit 0 = all files good. Exit 1 = caller MUST NOT run the sweep.
"""
import os
import sys

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_COLS = ["timestamp", "datetime_utc",
                 "bid_open", "bid_high", "bid_low", "bid_close",
                 "ask_open", "ask_high", "ask_low", "ask_close",
                 "spread", "volume"]

# name -> (lo, hi) generous outer band; catches wrong instrument / decimal error
FILES = {
    "NAS100": (5500, 30000),
    "US30":   (18000, 50000),
    "GER40":  (8000, 30000),
    "UK100":  (4000, 12000),
    "JP225":  (14000, 60000),
    "SPX500": (1800, 9000),
}

FIRST_ON_OR_BEFORE = pd.Timestamp("2018-01-31", tz="UTC")
LAST_ON_OR_AFTER = pd.Timestamp("2025-12-01", tz="UTC")
YEARS = list(range(2018, 2026))
MIN_BARS = 25_000          # ~8y x ~5,500 H1 bars/yr, generous floor


def verify(name, lo_exp, hi_exp):
    fname = f"{name}_H1_2018_2025_cfd_dukascopy.csv"
    path = os.path.join(REPO, "data", fname)
    print(f"\n{'='*72}\nVERIFY {name}  ({fname})\n{'='*72}")
    if not os.path.exists(path):
        print("  FAIL: file does not exist.")
        return False
    if os.path.getsize(path) == 0:
        print("  FAIL: file is empty.")
        return False

    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        print(f"  FAIL: missing columns {missing}")
        return False

    dt = pd.to_datetime(df["datetime_utc"], utc=True)
    first, last = dt.min(), dt.max()
    years = sorted(dt.dt.year.unique().tolist())
    missing_years = [y for y in YEARS if y not in years]
    lo, hi = float(df["bid_close"].min()), float(df["bid_close"].max())
    med_px, med_sp = float(df["bid_close"].median()), float(df["spread"].median())
    neg = int((df["spread"] < 0).sum())

    print(f"  bars            : {len(df):,}")
    print(f"  first / last    : {first}  ->  {last}")
    print(f"  years present   : {years}")
    print(f"  bid_close range : {lo:,.2f} -> {hi:,.2f}  (median {med_px:,.2f})")
    print(f"  spread median   : {med_sp:.4f} pts = {1e4*med_sp/med_px:.3f} bps")
    print(f"  negative spreads: {neg} ({100*neg/len(df):.3f}%)")

    fails = []
    if first > FIRST_ON_OR_BEFORE:
        fails.append(f"starts too late ({first.date()}, need <= 2018-01-31)")
    if last < LAST_ON_OR_AFTER:
        fails.append(f"ends too early ({last.date()}, need >= 2025-12-01)")
    if missing_years:
        fails.append(f"years absent: {missing_years}")
    if len(df) < MIN_BARS:
        fails.append(f"only {len(df):,} bars (< {MIN_BARS:,}) - likely a partial merge")
    if lo < lo_exp or hi > hi_exp:
        fails.append(f"price {lo:,.0f}-{hi:,.0f} outside band {lo_exp:,}-{hi_exp:,}")
    if not (med_sp > 0):
        fails.append(f"median spread not positive ({med_sp})")
    if neg / max(len(df), 1) > 0.01:
        fails.append(f"{100*neg/len(df):.2f}% negative spreads (>1%)")

    if fails:
        print("  --> FAIL")
        for f in fails:
            print(f"      - {f}")
        return False
    print("  --> PASS")
    return True


def main():
    res = {n: verify(n, *b) for n, b in FILES.items()}
    print(f"\n{'='*72}")
    for n, ok in res.items():
        print(f"  {n:>7}: {'PASS' if ok else 'FAIL'}")
    n_ok = sum(res.values())
    if all(res.values()):
        print(f"  ALL {len(res)} VERIFIED — basket sweep may proceed.")
        print("=" * 72)
        return 0
    print(f"  {n_ok}/{len(res)} passed — VERIFICATION FAILED, sweep will NOT run.")
    print("=" * 72)
    return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
