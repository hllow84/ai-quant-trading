#!/usr/bin/env python3
"""
test_vol_risk_premium.py — PART 1 (base-rate confirmation, run BEFORE any
strategy is built): does the "volatility risk premium" actually hold on
this data?

DOCUMENTED HYPOTHESIS BEING TESTED, stated explicitly before any number is
read: implied volatility (VIX) has historically run persistently ABOVE the
volatility that subsequently actually occurs — meaning option/vol sellers
have, on average and over long periods, collected more premium than the
turbulence that showed up cost them. This is a well-documented empirical
regularity (the "variance risk premium" literature), not a discovered
pattern being fit to this data; this script CONFIRMS it holds here, on the
specific data this study will use, before any strategy is built on it.

METHOD: for every trading day t (full VIX history, 1990-2026), compute the
REALIZED volatility of SPY over the FOLLOWING 20 trading days (annualized,
sqrt(252) x std of daily log returns, expressed in VIX-comparable "vol
points" i.e. x100). Compare VIX(t) (implied, known AT close of day t) to
that FORWARD realized vol. This forward comparison is DESCRIPTIVE ONLY —
it uses future data by construction (that is the whole point: "was the
implied estimate right") and is NEVER used as a trading signal. The
strategy in run_vol_risk_premium.py uses TRAILING realized vol only, which
IS causal — kept structurally separate from this descriptive check.

Usage: python scripts/test_vol_risk_premium.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
RV_WINDOW = 20  # trading days


def load_spy_close() -> pd.Series:
    df = pd.read_csv(DATA / "SPY_daily_yfinance.csv", index_col=0, parse_dates=True)
    return df["close"].dropna()


def load_vix_close() -> pd.Series:
    df = pd.read_csv(DATA / "vix_daily_yfinance.csv", index_col=0, parse_dates=True)
    return df["close"].dropna()


def realized_vol_forward(spy_close: pd.Series, window: int) -> pd.Series:
    """
    RV(t) = annualized std of daily log returns over [t+1, t+window] --
    DESCRIPTIVE ONLY, not causal. `rolling(window).std()` labeled at day
    d reflects [d-window+1, d]; shifting that series BACK by `window` days
    re-labels it at day t = d-window, so the value at t correctly reflects
    the window immediately AFTER t.
    """
    log_ret = np.log(spy_close / spy_close.shift(1)).dropna()
    return log_ret.rolling(window).std().shift(-window) * np.sqrt(252) * 100


def main() -> None:
    spy = load_spy_close()
    vix = load_vix_close()

    fwd_rv = realized_vol_forward(spy, RV_WINDOW)
    common = pd.DataFrame({"vix": vix, "fwd_rv": fwd_rv}).dropna()

    print("=" * 90)
    print("  VOLATILITY RISK PREMIUM — BASE RATE CONFIRMATION (run before any strategy)")
    print(f"  Hypothesis: VIX(t) > realized vol over the FOLLOWING {RV_WINDOW} trading days, on average.")
    print(f"  Sample: {len(common):,} trading days, {common.index.min().date()} -> {common.index.max().date()}")
    print("=" * 90)

    spread = common["vix"] - common["fwd_rv"]
    pct_positive = float((spread > 0).mean())
    mean_spread = float(spread.mean())
    median_spread = float(spread.median())
    mean_vix = float(common["vix"].mean())
    mean_fwd_rv = float(common["fwd_rv"].mean())

    print(f"\n  Mean VIX (implied):                 {mean_vix:.2f} vol points")
    print(f"  Mean forward-realized vol (SPY):    {mean_fwd_rv:.2f} vol points")
    print(f"  Mean spread (VIX - forward RV):     {mean_spread:+.2f} vol points")
    print(f"  Median spread:                      {median_spread:+.2f} vol points")
    print(f"  % of days VIX > forward realized vol: {pct_positive:.1%}")

    t_stat = mean_spread / (spread.std(ddof=1) / np.sqrt(len(spread)))
    print(f"  t-stat on mean spread != 0: {t_stat:.2f} (n={len(spread):,})")

    # By decade, so a single regime isn't silently carrying the whole result
    decade = (common.index.year // 10) * 10
    by_decade = spread.groupby(decade).agg(["mean", "count"])
    print("\n  By decade:")
    for d, row in by_decade.iterrows():
        print(f"    {int(d)}s: mean spread {row['mean']:+.2f} vol points, n={int(row['count']):,}")

    holds = mean_spread > 0 and pct_positive > 0.5
    print(f"\n  CONFIRMED on this data: {'YES' if holds else 'NO'} "
          f"(mean spread {'positive' if mean_spread > 0 else 'negative'}, "
          f"{pct_positive:.0%} of days {'above' if pct_positive > 0.5 else 'below'} 50%)")

    common.to_csv(RESULTS / "vol_risk_premium_base_rate.csv")
    print(f"\n  Saved: {RESULTS / 'vol_risk_premium_base_rate.csv'}")

    if not holds:
        print("\n  *** BASE RATE DOES NOT HOLD ON THIS DATA. Reconsider before building a strategy on it. ***")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
