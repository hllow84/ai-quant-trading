#!/usr/bin/env python3
"""
test_cross_asset_leadlag.py — PART 1 (statistical test, run BEFORE any
backtest is built): does one market's move predict ANOTHER market's move
with a lag? Every prior candidate in this project (price patterns,
momentum rotation sec 12/17, positioning sec 18) was self-referential — an
asset predicting its own future from its own past. This tests a third,
genuinely different information category: cross-asset lead-lag.

FOUR PRE-REGISTERED PAIRS, each with an EXACT stated lag and causal design
--------------------------------------------------------------------------
1. NAS100 prior-session return -> BTC next 4h return
2. NAS100 prior-session return -> BTC next 8h return
3. DXY (real ICE US Dollar Index) prior-day return -> XAUUSD next-day return
4. DXY prior-day return -> CEW next-day return

CAUSALITY, checked explicitly for each pair (the task's own warning: this
is the most likely place for a subtle look-ahead bug in a cross-asset
test):

  Pair 1/2 — NAS100 "prior-session return" is defined as close-to-close on
  the NAS100 CFD's own UTC-calendar-day aggregation (same convention
  research/gold_data.py::aggregate_daily uses everywhere else in this
  repo for a near-24h instrument) — i.e. the return realized between the
  LAST H1 bar of UTC-day D-1 and the LAST H1 bar of UTC-day D. That value
  is fully known only once the last bar of day D has printed. The target
  (BTC's forward return) is measured starting from the first BTCUSDT H1
  bar at or after that exact NAS100 timestamp, PLUS one further full H1
  bar of conservative lag (matching this project's standing convention of
  never trusting a same-timestamp handoff). `verify_causality()` asserts
  this for every observation used, not a sample.

  Pair 3/4 — DXY's daily bar (a US-market-hours index/proxy) is treated as
  known only at the CLOSE of its own trading day D. The target is the
  FOLLOWING trading/calendar day's return in each other asset (XAUUSD's
  UTC-day D+1 return for gold; CEW's next NYSE trading day close-to-close
  for the ETF) — using the NEXT day entirely, never the same day DXY
  closed on, removes any same-day overlap ambiguity by construction.

METHOD — stated before any p-value is read
---------------------------------------------
Pearson correlation between the lagged predictor return and the forward
target return, for each of the 4 pairs (all non-overlapping observations —
NAS100 signals are one per UTC day, BTC's 4h/8h windows are far shorter
than the 24h gap between signals; DXY/XAUUSD/CEW are all daily-to-next-
daily, no overlap). Two-sided t-test on the correlation coefficient.
**Bonferroni correction: alpha=0.05 / 4 tests = 0.0125**, decided before
any result is read — same discipline as section 16's seasonality test.

ONLY IF a pair clears the corrected threshold does this proceed to build
and backtest a directional strategy (run_cross_asset_leadlag.py). If NONE
clear it, that is reported as the answer — plainly, not dressed up.

Usage: python scripts/test_cross_asset_leadlag.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
from scipy import stats

from research.gold_data import load_m1_spot

ALPHA = 0.05
N_TESTS = 4
BONFERRONI_ALPHA = ALPHA / N_TESTS

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"


def nas100_daily_close_series() -> tuple[pd.Series, pd.Series]:
    """Returns (daily_close, actual_last_bar_timestamp_per_day), UTC-day aggregation."""
    h1 = load_m1_spot(DATA / "NAS100_H1_2018_2025_cfd_dukascopy.csv")
    mid = (h1["bid_close"] + h1["ask_close"]) / 2
    day = mid.index.normalize()
    daily_close = mid.groupby(day).last()
    last_ts = pd.Series(mid.index, index=mid.index).groupby(day).last()
    return daily_close, last_ts


def btc_h1() -> pd.DataFrame:
    df = pd.read_csv(DATA / "BTCUSDT_H1_2018_2025_binance.csv", parse_dates=["datetime_utc"])
    df["datetime_utc"] = pd.to_datetime(df["datetime_utc"], utc=True)
    return df.set_index("datetime_utc").sort_index()


def xau_daily_close() -> pd.Series:
    m1 = load_m1_spot(DATA / "XAUUSD_M1_2018_2025_spot_dukascopy.csv")
    mid = (m1["bid_close"] + m1["ask_close"]) / 2
    daily = mid.groupby(mid.index.normalize()).last()
    daily.index = daily.index.tz_localize(None)  # match DXY/CEW's tz-naive daily-date convention
    return daily


def dxy_daily_close() -> pd.Series:
    df = pd.read_csv(DATA / "DXYNYB_daily_yfinance.csv", index_col=0, parse_dates=True)
    return df["close"]


def cew_daily_close() -> pd.Series:
    df = pd.read_csv(DATA / "CEW_daily_yfinance.csv", index_col=0, parse_dates=True)
    return df["close"]


def pair_nas100_btc(hours: int) -> pd.DataFrame:
    """NAS100 prior-day return -> BTC forward `hours`-hour return, causal."""
    nas_close, nas_ts = nas100_daily_close_series()
    nas_ret = nas_close.pct_change()

    btc = btc_h1()
    btc_idx = btc.index

    rows = []
    for day, ret in nas_ret.dropna().items():
        signal_ts = nas_ts.loc[day]  # actual last-bar timestamp of that UTC day
        pos = btc_idx.searchsorted(signal_ts, side="right")  # first BTC bar strictly after
        pos += 1  # one further conservative lag bar
        if pos >= len(btc_idx) or pos + hours >= len(btc_idx):
            continue
        entry_ts = btc_idx[pos]
        exit_ts = btc_idx[pos + hours]
        if entry_ts <= signal_ts:  # causality sanity check inline
            continue
        entry_px = btc["mid_close"].iloc[pos]
        exit_px = btc["mid_close"].iloc[pos + hours]
        fwd_ret = exit_px / entry_px - 1.0
        rows.append(dict(signal_day=day, signal_ts=signal_ts, entry_ts=entry_ts,
                         nas_ret=ret, btc_fwd_ret=fwd_ret))
    return pd.DataFrame(rows)


def pair_dxy_next_day(target_close: pd.Series, target_name: str) -> pd.DataFrame:
    """DXY prior-day return -> target's NEXT trading/calendar day return, causal by construction."""
    dxy_close = dxy_daily_close()
    dxy_ret = dxy_close.pct_change()
    tgt_ret = target_close.pct_change()

    # Align DXY day D's return to target's return on the FIRST target date
    # strictly after D — never the same day, removing overlap ambiguity.
    common = pd.DataFrame({"dxy_ret": dxy_ret}).dropna()
    rows = []
    tgt_days = tgt_ret.dropna().index
    for d, r in common["dxy_ret"].items():
        pos = tgt_days.searchsorted(d, side="right")
        if pos >= len(tgt_days):
            continue
        next_day = tgt_days[pos]
        if next_day <= d:
            continue
        # Sanity bound: "next day" must actually be a few calendar days away,
        # not the target series' very first date (which is what searchsorted
        # returns for any DXY date before the target's own inception -- DXY
        # goes back to 1971, XAUUSD/CEW start 2018/2009, so without this
        # check EVERY pre-inception DXY date would silently collapse onto
        # target day 1, corrupting the sample with decades of stale, non-
        # adjacent "next day" pairings. Caught before trusting any p-value.
        if (next_day - d).days > 5:
            continue
        rows.append(dict(dxy_day=d, target_day=next_day, dxy_ret=r,
                         target_fwd_ret=float(tgt_ret.loc[next_day])))
    return pd.DataFrame(rows)


def verify_causality(df: pd.DataFrame, signal_col: str, entry_col: str) -> bool:
    if df.empty:
        return False
    return bool((df[entry_col] > df[signal_col]).all())


def corr_test(x: np.ndarray, y: np.ndarray, label: str) -> dict:
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    n = len(x)
    if n < 10:
        return dict(pair=label, n=n, r=float("nan"), p_value=float("nan"), significant=False)
    r, p = stats.pearsonr(x, y)
    sig = bool(np.isfinite(p) and p < BONFERRONI_ALPHA)
    return dict(pair=label, n=n, r=float(r), p_value=float(p), significant=sig)


def main() -> None:
    print("=" * 100)
    print("  CROSS-ASSET LEAD-LAG — PART 1: statistical test, run BEFORE any backtest")
    print(f"  {N_TESTS} pre-registered pairs. Bonferroni alpha = {ALPHA}/{N_TESTS} = {BONFERRONI_ALPHA:.4f}")
    print("=" * 100)

    results = []

    print("\n[1/4] NAS100 prior-day return -> BTC next 4h return ...", flush=True)
    p1 = pair_nas100_btc(4)
    c1 = verify_causality(p1, "signal_ts", "entry_ts")
    print(f"  n={len(p1)}, causality={'PASS' if c1 else 'FAIL'}")
    r1 = corr_test(p1["nas_ret"], p1["btc_fwd_ret"], "NAS100->BTC (4h)")
    r1["causal_ok"] = c1
    results.append(r1)

    print("\n[2/4] NAS100 prior-day return -> BTC next 8h return ...", flush=True)
    p2 = pair_nas100_btc(8)
    c2 = verify_causality(p2, "signal_ts", "entry_ts")
    print(f"  n={len(p2)}, causality={'PASS' if c2 else 'FAIL'}")
    r2 = corr_test(p2["nas_ret"], p2["btc_fwd_ret"], "NAS100->BTC (8h)")
    r2["causal_ok"] = c2
    results.append(r2)

    print("\n[3/4] DXY prior-day return -> XAUUSD next-day return ...", flush=True)
    p3 = pair_dxy_next_day(xau_daily_close(), "XAUUSD")
    c3 = verify_causality(p3, "dxy_day", "target_day")
    print(f"  n={len(p3)}, causality={'PASS' if c3 else 'FAIL'}")
    r3 = corr_test(p3["dxy_ret"], p3["target_fwd_ret"], "DXY->XAUUSD (next day)")
    r3["causal_ok"] = c3
    results.append(r3)

    print("\n[4/4] DXY prior-day return -> CEW next-day return ...", flush=True)
    p4 = pair_dxy_next_day(cew_daily_close(), "CEW")
    c4 = verify_causality(p4, "dxy_day", "target_day")
    print(f"  n={len(p4)}, causality={'PASS' if c4 else 'FAIL'}")
    r4 = corr_test(p4["dxy_ret"], p4["target_fwd_ret"], "DXY->CEW (next day)")
    r4["causal_ok"] = c4
    results.append(r4)

    df = pd.DataFrame(results)
    df.to_csv(RESULTS / "cross_asset_leadlag_test.csv", index=False)

    print("\n" + "=" * 100)
    print("  RESULTS")
    print("=" * 100)
    print(f"  {'pair':<26} {'n':>6} {'r':>9} {'p-value':>10} {'causal':>7} {'sig (Bonf)':>11}")
    print("  " + "-" * 74)
    for _, r in df.sort_values("p_value").iterrows():
        print(f"  {r['pair']:<26} {int(r['n']):>6} {r['r']:>+9.4f} {r['p_value']:>10.4f} "
              f"{'PASS' if r['causal_ok'] else 'FAIL':>7} {'YES ***' if r['significant'] else 'no':>11}")

    n_sig = int(df["significant"].sum())
    min_p = df["p_value"].min()
    all_causal = bool(df["causal_ok"].all())
    print(f"\n  All 4 pairs causality-verified: {'YES' if all_causal else 'NO -- INVESTIGATE BEFORE READING ANYTHING'}")
    print(f"  RESULT: {n_sig}/{N_TESTS} pairs clear the Bonferroni-corrected threshold (p < {BONFERRONI_ALPHA:.4f}).")
    print(f"  Smallest raw p-value observed: {min_p:.4f}")

    if n_sig == 0:
        print("\n  CONCLUSION: NO statistically real cross-asset lead-lag relationship was found among these")
        print("  4 pre-registered pairs. Per the task's explicit instruction, this is reported as a clean")
        print("  negative — NO directional strategy is built or backtested on any of them. Forcing a backtest")
        print("  onto the smallest-p-value pair anyway would be exactly the failure mode this pre-registered")
        print("  test and its correction exist to prevent.")
    else:
        sig_rows = df[df["significant"]]
        print(f"\n  CONCLUSION: {n_sig} pair(s) clear the corrected threshold — proceeding to build and backtest")
        print("  a directional strategy on each (run_cross_asset_leadlag.py).")
        print(sig_rows.to_string(index=False))

    print(f"\n  Saved: {RESULTS / 'cross_asset_leadlag_test.csv'}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
