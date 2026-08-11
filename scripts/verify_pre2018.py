#!/usr/bin/env python3
"""Hard gate for the pre-2018 (2013_2017) H1 basket files.

Same role as verify_basket.py, retargeted at the out-of-regime window. The
failure this exists to catch is the one that already happened once in this repo:
a file NAMED for a span that actually holds a fraction of it, silently turning an
8-year backtest into a 2-year one.

Differences from verify_basket.py, all forced by what the archive really holds:
  * Span is 2013-09-30 -> 2017-12-29, not 8 full years. 2013 is a partial warmup
    quarter, so it is checked for presence but exempt from the per-year floor.
  * Price bands are the pre-2018 levels (indices were far lower), so the
    2018-2025 bands would wrongly pass everything.
  * Per-year bar counts are printed and floored, because a dropped year is the
    specific defect this gate is for.
  * Coverage gaps > 10 days are reported: JP225's archive is known to stop early
    and a silent tail gap shortens the test window without shortening the name.

Exit 0 = files good. Exit 1 = caller MUST NOT run the backtest.
"""
import os
import sys

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REQUIRED_COLS = ["timestamp", "datetime_utc",
                 "bid_open", "bid_high", "bid_low", "bid_close",
                 "ask_open", "ask_high", "ask_low", "ask_close",
                 "spread", "volume"]

# name -> (lo, hi) generous outer band at PRE-2018 index levels.
FILES = {
    "NAS100": (2500, 7000),
    "US30":   (14000, 26000),
    "SPX500": (1500, 3000),
    "UK100":  (5500, 8000),
    "JP225":  (12000, 25000),
}

FIRST_ON_OR_BEFORE = pd.Timestamp("2013-10-31", tz="UTC")
LAST_ON_OR_AFTER = pd.Timestamp("2017-11-01", tz="UTC")
FULL_YEARS = [2014, 2015, 2016, 2017]
MIN_BARS_PER_FULL_YEAR = 2000   # index H1 is market-hours-only, ~3-6k bars/yr
MIN_BARS = 12_000
MAX_GAP_DAYS = 10


def verify(name, lo_exp, hi_exp):
    fname = f"{name}_H1_2013_2017_cfd_dukascopy.csv"
    path = os.path.join(REPO, "data", fname)
    print(f"\n{'='*78}\nVERIFY {name}  ({fname})\n{'='*78}")
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        print("  FAIL: file missing or empty.")
        return False

    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        print(f"  FAIL: missing columns {missing}")
        return False

    dt = pd.to_datetime(df["datetime_utc"], utc=True)
    first, last = dt.min(), dt.max()
    per_year = dt.dt.year.value_counts().sort_index()
    lo, hi = float(df["bid_close"].min()), float(df["bid_close"].max())
    med_px, med_sp = float(df["bid_close"].median()), float(df["spread"].median())
    neg = int((df["spread"] < 0).sum())

    # Largest coverage hole, ignoring normal weekends/holidays via the threshold.
    gaps = dt.sort_values().diff().dropna()
    max_gap = gaps.max() if len(gaps) else pd.Timedelta(0)
    big = gaps[gaps > pd.Timedelta(days=MAX_GAP_DAYS)]

    print(f"  bars            : {len(df):,}")
    print(f"  first / last    : {first}  ->  {last}")
    print(f"  bars per year   : {per_year.to_dict()}")
    print(f"  bid_close range : {lo:,.2f} -> {hi:,.2f}  (median {med_px:,.2f})")
    print(f"  spread median   : {med_sp:.4f} pts = {1e4*med_sp/med_px:.3f} bps")
    print(f"  negative spreads: {neg} ({100*neg/len(df):.3f}%)")
    print(f"  largest gap     : {max_gap}  ({len(big)} gaps > {MAX_GAP_DAYS}d)")

    fails, warns = [], []
    if first > FIRST_ON_OR_BEFORE:
        fails.append(f"starts too late ({first.date()}, need <= 2013-10-31)")
    if last < LAST_ON_OR_AFTER:
        fails.append(f"ends too early ({last.date()}, need >= 2017-11-01)")
    for y in FULL_YEARS:
        n = int(per_year.get(y, 0))
        if n < MIN_BARS_PER_FULL_YEAR:
            fails.append(f"{y} has only {n} bars (< {MIN_BARS_PER_FULL_YEAR})")
    if len(df) < MIN_BARS:
        fails.append(f"only {len(df):,} bars (< {MIN_BARS:,}) - likely partial")
    if lo < lo_exp or hi > hi_exp:
        fails.append(f"price {lo:,.0f}-{hi:,.0f} outside band {lo_exp:,}-{hi_exp:,}")
    if not (med_sp > 0):
        fails.append(f"median spread not positive ({med_sp})")
    if neg / max(len(df), 1) > 0.01:
        fails.append(f"{100*neg/len(df):.2f}% negative spreads (>1%)")
    # A tail that stops early is not fatal for a basket member, but it silently
    # shortens that member's contribution, so it must be surfaced, not swallowed.
    if last < pd.Timestamp("2017-12-15", tz="UTC"):
        warns.append(f"tail stops {last.date()} — member is short of the 2017-12-29 window end")
    if len(big):
        warns.append(f"{len(big)} coverage gap(s) > {MAX_GAP_DAYS}d, largest {max_gap}")

    for w in warns:
        print(f"  WARN: {w}")
    if fails:
        print("  --> FAIL")
        for f in fails:
            print(f"      - {f}")
        return False
    print("  --> PASS")
    return True


def main():
    res = {n: verify(n, *b) for n, b in FILES.items()}
    print(f"\n{'='*78}")
    for n, ok in res.items():
        print(f"  {n:>7}: {'PASS' if ok else 'FAIL'}")
    if all(res.values()):
        print(f"  ALL {len(res)} VERIFIED — pre-2018 out-of-regime test may proceed.")
        print("  NOTE: GER40 is absent by design (no Dukascopy ask/spread before 2015).")
        print("=" * 78)
        return 0
    print(f"  {sum(res.values())}/{len(res)} passed — VERIFICATION FAILED.")
    print("=" * 78)
    return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
