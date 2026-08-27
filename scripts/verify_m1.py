#!/usr/bin/env python3
"""
verify_m1.py — HARD GATE for the M1 row of the timeframe sweep. Exits 1 on failure.

This exists for the reason scripts/verify_indices.py exists: a partial merge once
produced a file NAMED `2018_2025` that actually held only 386k rows ending
2019-12-31, and a backtest would have silently run on two years instead of eight.
At M1 there are two further ways to be quietly wrong, so both are checked here
rather than assumed in the runner:

  A. THE EXECUTION-FRAME IDENTITY. run_sweep_m1.py builds its execution frame
     with resample_mid(m1, "1min"), the same transform M5-H4 used. If that were
     NOT equivalent to relabelling each native bar to its close time, the M1 row
     would be running a different convention from every row above it. Checked
     exactly, on a real slice of every file.

  B. THE ANNUALISATION FACTOR. Sharpe at M1 is the single easiest number in this
     project to inflate by ~30x. The gate measures the real M1 bars/year (which
     is NOT metrics.py's 525,600 — that assumes a 24/7 year) and asserts the
     identity SR_perbar / SR_daily == sqrt(bars_per_year / 252) on a synthetic
     return series, so the relationship is demonstrated arithmetically before any
     strategy result is read.

Checks per file: first and last bar, per-year bar floors, real positive spread,
price in band, coverage gaps, and the RTH window for the pre-2018 files.

Usage:  py -3.14 scripts/verify_m1.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_mid, resample_mid
from research.metrics import sharpe

# name -> (path, price_lo, price_hi, first_date, last_date, min_bars_per_full_year, rth_only)
SPECS = {
    "XAUUSD": (_ROOT / "data" / "XAUUSD_M1_2018_2025_spot_dukascopy.csv",
               1_000, 5_000, "2018-01-01", "2025-12-31", 100_000, False),
    "NAS100": (_ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv",
               5_000, 30_000, "2018-01-03", "2025-12-31", 150_000, False),
    "US30":   (_ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",
               15_000, 55_000, "2018-01-02", "2025-12-31", 150_000, False),
    "NAS100_pre2018": (_ROOT / "data" / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv",
                       3_000, 7_000, "2013-09-30", "2017-12-29", 55_000, True),
    "US30_pre2018":   (_ROOT / "data" / "US30_M1RTH_2013_2017_cfd_dukascopy.csv",
                       14_000, 26_000, "2013-09-30", "2017-12-29", 55_000, True),
}

RTH_UTC_MIN = (13 * 60, 21 * 60)     # [13:00, 21:00) UTC — the pre-2018 archive window
ANN_FACTOR_DAILY = 252
COLS = ["mid_open", "mid_high", "mid_low", "mid_close", "spread"]

# A NEGATIVE spread is impossible and always fails. A spread of exactly zero is a
# real, rare Dukascopy archive artifact (bid == ask at the close of one minute).
# It hands that single trade a free round-turn, so it flatters the strategy --
# the safe direction for a kill verdict, but it is still capped rather than
# ignored. Measured: 1 bar in 467,543 (0.0002%) in US30 2013-2017, 0 elsewhere.
ZERO_SPREAD_TOLERANCE = 0.0001      # 0.01% of bars

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)
    print(f"    FAIL  {msg}")


def ok(msg: str) -> None:
    print(f"    ok    {msg}")


def check_file(name: str, spec: tuple) -> None:
    path, lo, hi, first, last, min_year_bars, rth_only = spec
    print(f"\n[{name}] {path.name}")
    if not path.exists():
        fail(f"{name}: file missing at {path}")
        return

    m = load_m1_mid(path)
    if m.empty:
        fail(f"{name}: file loaded empty")
        return

    # ── span ──────────────────────────────────────────────────────────────────
    f_act, l_act = m.index[0], m.index[-1]
    if f_act.date() > pd.Timestamp(first).date():
        fail(f"{name}: first bar {f_act.date()} is AFTER the expected {first}")
    else:
        ok(f"first bar {f_act}")
    if l_act.date() < pd.Timestamp(last).date():
        fail(f"{name}: last bar {l_act.date()} is BEFORE the expected {last} "
             f"— this is the partial-merge failure mode")
    else:
        ok(f"last bar  {l_act}   ({len(m):,} M1 bars)")

    # ── per-year bar floor ────────────────────────────────────────────────────
    by_year = m.groupby(m.index.year).size()
    full_years = [y for y in by_year.index
                  if y not in (by_year.index.min(), by_year.index.max())] or list(by_year.index)
    thin = {int(y): int(by_year[y]) for y in full_years if by_year[y] < min_year_bars}
    if thin:
        fail(f"{name}: years below the {min_year_bars:,} bar floor: {thin}")
    else:
        ok(f"per-year bars clear the {min_year_bars:,} floor "
           f"(min {by_year[full_years].min():,}, max {by_year.max():,})")
    print(f"          {dict((int(k), int(v)) for k, v in by_year.items())}")

    # ── spread is real and positive ───────────────────────────────────────────
    sp = m["spread"]
    n_neg = int((sp < 0).sum())
    n_zero = int((sp == 0).sum())
    zero_share = n_zero / len(sp)
    if n_neg:
        # A negative spread is arithmetically impossible for a real book and
        # means the bid/ask merge is broken. Any count is a hard fail.
        fail(f"{name}: {n_neg:,} bars with NEGATIVE spread — the bid/ask merge is broken")
    elif zero_share > ZERO_SPREAD_TOLERANCE:
        fail(f"{name}: {n_zero:,} bars ({zero_share:.4%}) with spread exactly 0, above the "
             f"{ZERO_SPREAD_TOLERANCE:.2%} tolerance — a free round-turn flatters every trade "
             f"that enters on one")
    elif sp.nunique() < 50:
        fail(f"{name}: spread takes only {sp.nunique()} distinct values — looks synthetic")
    else:
        med_px = float(m["mid_close"].median())
        ok(f"spread real & positive: median {sp.median():.4f} px "
           f"= {1e4 * sp.median() / med_px:.2f} bps round-turn, {sp.nunique():,} distinct values, "
           f"{n_neg} negative / {n_zero} zero ({zero_share:.5%}, tolerance "
           f"{ZERO_SPREAD_TOLERANCE:.2%})")

    # ── price band ────────────────────────────────────────────────────────────
    pmin, pmax = float(m["mid_close"].min()), float(m["mid_close"].max())
    if pmin < lo or pmax > hi:
        fail(f"{name}: mid_close range {pmin:,.1f}-{pmax:,.1f} outside the sanity band {lo:,}-{hi:,}")
    else:
        ok(f"price band {pmin:,.1f} - {pmax:,.1f} (expected {lo:,} - {hi:,})")

    # ── coverage gaps ─────────────────────────────────────────────────────────
    days = pd.Series(m.index.normalize().unique()).sort_values()
    gaps = days.diff().dt.days.dropna()
    big = int((gaps > 10).sum())
    print(f"          {len(days):,} distinct UTC days; gaps > 10 days: {big} "
          f"(max {int(gaps.max()) if len(gaps) else 0} days)")

    # ── RTH window (pre-2018 files only) ──────────────────────────────────────
    mod = m.index.hour * 60 + m.index.minute
    inside = float(((mod >= RTH_UTC_MIN[0]) & (mod < RTH_UTC_MIN[1])).mean())
    if rth_only:
        if inside < 0.999:
            fail(f"{name}: only {inside:.4%} of bars inside [13:00,21:00) UTC — the matched "
                 f"in-regime control filters on exactly this window, so a mismatch invalidates "
                 f"the out-of-regime comparison")
        else:
            ok(f"RTH-only confirmed: {inside:.4%} of bars in [13:00,21:00) UTC "
               f"(min {int(mod.min())}, max {int(mod.max())} min-of-day)")
    else:
        ok(f"23-hour file: {inside:.1%} of bars fall inside [13:00,21:00) UTC "
           f"(the matched control keeps this subset)")

    # ── CHECK A: the execution-frame identity ─────────────────────────────────
    sl = m.iloc[:200_000] if len(m) > 200_000 else m
    rs = resample_mid(sl, "1min")
    shifted = sl.copy()
    shifted.index = shifted.index + pd.Timedelta(minutes=1)
    if len(rs) != len(shifted):
        fail(f"{name}: resample_mid('1min') produced {len(rs):,} bars vs {len(shifted):,} "
             f"for a +1min relabel — the M1 execution frame is NOT the M5-H4 convention")
    else:
        common = rs.index.intersection(shifted.index)
        same = np.allclose(rs.loc[common, COLS].to_numpy(),
                           shifted.loc[common, COLS].to_numpy(), equal_nan=True)
        if not same or len(common) != len(rs):
            fail(f"{name}: resample_mid('1min') != +1min relabel on values")
        else:
            ok(f"execution frame: resample_mid('1min') == native bar relabelled to its "
               f"close time, exactly ({len(rs):,} bars checked). Same convention as M5-H4.")

    # ── CHECK B: annualisation arithmetic, on this file's real bar count ──────
    span_years = max((m.index[-1] - m.index[0]).days / 365.25, 1e-9)
    bars_per_year = len(m) / span_years
    rng = np.random.default_rng(0)
    r_bar = pd.Series(rng.normal(0, 1e-4, 50_000))
    factor = int(round(bars_per_year))       # sharpe() takes an int factor
    sr_bar = sharpe(r_bar, factor)
    sr_day = sharpe(r_bar, ANN_FACTOR_DAILY)
    expect = float(np.sqrt(factor / ANN_FACTOR_DAILY))   # compare like with like
    got = sr_bar / sr_day if sr_day else float("nan")
    if not np.isclose(got, expect, rtol=1e-6):
        fail(f"{name}: annualisation identity broken ({got:.6f} vs {expect:.6f})")
    else:
        ok(f"annualisation: measured {bars_per_year:,.0f} M1 bars/year "
           f"(metrics.py assumes 525,600 for '1m' — {525_600 / bars_per_year:.1f}x too high). "
           f"Using it on per-bar returns instead of 252 on daily returns would inflate "
           f"Sharpe {expect:.1f}x.")


def main() -> int:
    print("=" * 100)
    print("  M1 DATA + METHOD GATE — run before run_sweep_m1.py. Exits 1 on any failure.")
    print("=" * 100)
    for name, spec in SPECS.items():
        check_file(name, spec)

    print("\n" + "=" * 100)
    if failures:
        print(f"  GATE FAILED — {len(failures)} problem(s). The sweep is BLOCKED:")
        for f in failures:
            print(f"    - {f}")
        print("=" * 100)
        return 1
    print("  GATE PASSED — all files and both method identities check out.")
    print("=" * 100)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
