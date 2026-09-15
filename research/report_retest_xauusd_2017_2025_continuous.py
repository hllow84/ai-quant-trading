#!/usr/bin/env python3
"""
RETEST OR30/1R, XAUUSD -- ONE CONTINUOUS compounding run across the full
available M1 history, 2017-01-02 -> 2025-12-31, treated as a single account
that lived through both eras back to back.

REPORTING ONLY. No new rule, no new parameter, no new trial. Entry logic is
byte-identical to sec 10.5/10.6/10.7/10.8/10.9: orb(retest=True,
retest_tol_frac=0.10, or_minutes=30, target="1R", stop_mode="or_range",
09:30 ET session), simulate_trades + de_overlap, 1% fixed-fractional risk,
XAUUSD legacy $/oz cost model (cost_bps=None) -- all reused unchanged from
research/report_retest_or30_1r_all4_compounded.py.

DATA CAVEAT, stated plainly up front: this project's XAUUSD M1 archive does
NOT reach back to 2013. The earliest clean XAUUSD M1 on disk is
2017-01-02 (data/XAUUSD_M1_2017_spot_dukascopy.csv, backfilled for sec 10.6).
2013-2016 XAUUSD M1 does not exist in this repo and was not pulled for this
task (reporting-only, no new data). So "full available history" here means
2017-01-02 -> 2025-12-31 (9 years), NOT 2013-2025 -- the two files
(2017-only and 2018-2025) are concatenated into ONE continuous frame with no
gap (2017 file ends 2017-12-29 21:58 UTC; 2018 file starts 2018-01-01 23:00
UTC -- the gap between them is one New Year weekend, not a data hole).

The two previously-reported numbers (sec 10.6: XAUUSD "out-of-regime"/2017
compounded in isolation from its own fresh $100k; sec 10.6/10.7: XAUUSD FULL
2018-2025 compounded from its own fresh $100k) are EACH-SEPARATELY-FUNDED
summaries. This script is different on purpose: ONE $100k account, one
trade stream in chronological order across the full 2017-2025 span, so the
equity curve carries whatever gain or loss 2017 produced into 2018 rather
than resetting capital at the year boundary.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.ftmo_engine import (
    simulate_trades, de_overlap, RISK_PER_TRADE,
    build_daily_returns, equity_from_returns, build_position_series,
)
from strategies.orb import orb, ET

D = _ROOT / "data"
START_CAP = 100_000.0
BARS_PER_YEAR = 252

ET_SESSION = dict(session_tz=ET, open_min=9 * 60 + 30, close_min=16 * 60, min_sess_bars=300)
PARAMS = dict(or_minutes=30, target="1R", stop_mode="or_range")

FILE_2017 = D / "XAUUSD_M1_2017_spot_dukascopy.csv"
FILE_2018_2025 = D / "XAUUSD_M1_2018_2025_spot_dukascopy.csv"


def mid_frame(path: Path):
    spot = load_m1_spot(path)
    m = pd.DataFrame(index=spot.index)
    for c in ("open", "high", "low", "close"):
        m[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
    m["spread"] = spot["spread"]
    m["volume"] = spot["volume"]
    return m, spot


def build_trades(m: pd.DataFrame) -> pd.DataFrame:
    cands = orb(m, PARAMS, retest=True, retest_tol_frac=0.10, **ET_SESSION)
    tr = de_overlap(simulate_trades(m, cands, strictly_after=False,
                                     cost_bps=None, slip_bps_fn=None))
    tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True)
    tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True)
    return tr.sort_values("exit_time").reset_index(drop=True)


def compound_path(net_R: pd.Series, start_cap: float) -> np.ndarray:
    """Running equity AFTER each trade, one continuous account."""
    eq = start_cap
    path = np.empty(len(net_R))
    for i, r in enumerate(net_R.to_numpy()):
        eq *= (1.0 + RISK_PER_TRADE * r)
        path[i] = eq
    return path


def bh(m: pd.DataFrame, a: str, b: str, start_cap: float):
    seg = m.loc[(m.index >= pd.Timestamp(a, tz="UTC")) & (m.index <= pd.Timestamp(b, tz="UTC") + pd.Timedelta(days=1))]
    if seg.empty:
        return None
    p0, p1 = float(seg["mid_close"].iloc[0]), float(seg["mid_close"].iloc[-1])
    return start_cap * p1 / p0, p0, p1


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # ---- load and concatenate into ONE continuous M1 frame ----
    m17, spot17 = mid_frame(FILE_2017)
    m18, spot18 = mid_frame(FILE_2018_2025)
    print(f"2017 file:      {FILE_2017.name}: {len(m17):,} bars, {m17.index[0]} -> {m17.index[-1]}")
    print(f"2018-2025 file: {FILE_2018_2025.name}: {len(m18):,} bars, {m18.index[0]} -> {m18.index[-1]}")
    gap = m18.index[0] - m17.index[-1]
    print(f"Gap between files: {gap} (New Year weekend / holiday close -- not a data hole)")
    assert m17.index[-1] < m18.index[0], "files overlap -- would double-count bars"

    m = pd.concat([m17, m18]).sort_index()
    spot = pd.concat([spot17, spot18]).sort_index()
    assert m.index.is_monotonic_increasing and not m.index.has_duplicates
    daily_index = aggregate_daily(spot).index
    print(f"Continuous frame: {len(m):,} bars, {m.index[0]} -> {m.index[-1]}\n")

    # ---- build trades on the CONTINUOUS frame, one pass, one trade stream ----
    tr = build_trades(m)
    print(f"RETEST OR30/1R trades over the full continuous span: {len(tr)}")
    print(f"First trade entry: {tr['entry_time'].min()}   Last trade exit: {tr['exit_time'].max()}\n")

    # ---- honesty gate ----
    pos = build_position_series(tr, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:60]}"
    daily_ret = build_daily_returns(tr, daily_index)
    daily_equity = equity_from_returns(daily_ret)
    full_sharpe = sharpe(daily_ret, BARS_PER_YEAR)
    full_gross_pf = profit_factor(tr["gross_R"])
    full_net_pf = profit_factor(tr["net_R"])
    full_maxdd = max_drawdown(daily_equity)

    # ---- ONE continuous compounding path across every trade in order ----
    path = compound_path(tr["net_R"], START_CAP)
    end_balance = path[-1] if len(path) else START_CAP
    # peak-to-trough drawdown on the actual TRADE-BY-TRADE equity path (not the
    # daily-resampled one) -- the true worst intra-run peak-to-trough on this
    # exact account, since a trade-level path can register a lower trough
    # between daily marks than the daily-resampled series would show.
    running_peak = np.maximum.accumulate(np.concatenate(([START_CAP], path)))
    dd_path = 1.0 - np.concatenate(([START_CAP], path)) / running_peak
    trade_level_maxdd = float(dd_path.max())
    maxdd_idx = int(dd_path.argmax())
    if maxdd_idx == 0:
        maxdd_date = None
    else:
        maxdd_date = tr["exit_time"].iloc[maxdd_idx - 1]
    peak_before_dd = float(running_peak[maxdd_idx])

    # ---- year-by-year breakdown of the SAME continuous run ----
    years = sorted(tr["exit_time"].dt.year.unique())
    print("=" * 110)
    print("  YEAR-BY-YEAR -- ONE CONTINUOUS $100,000 ACCOUNT, RETEST OR30/1R, XAUUSD, 2017-2025")
    print("=" * 110)
    print(f"  {'year':<6} {'trades':>7} {'start equity':>14} {'end equity':>14} {'year return %':>14} "
          f"{'gross PF':>9} {'net PF':>8} {'win %':>7}")
    print("  " + "-" * 106)

    eq_before = START_CAP
    yearly_rows = []
    running_eq = START_CAP
    running_path_all = []
    for i, r in enumerate(tr["net_R"].to_numpy()):
        running_eq *= (1.0 + RISK_PER_TRADE * r)
        running_path_all.append(running_eq)
    tr = tr.assign(_running_eq=running_path_all)

    for yr in years:
        yr_mask = tr["exit_time"].dt.year == yr
        yr_trades = tr[yr_mask]
        start_eq = eq_before
        end_eq = float(yr_trades["_running_eq"].iloc[-1])
        ret_pct = end_eq / start_eq - 1.0
        gpf = profit_factor(yr_trades["gross_R"]) if len(yr_trades) else float("nan")
        npf = profit_factor(yr_trades["net_R"]) if len(yr_trades) else float("nan")
        winr = (yr_trades["net_R"] > 0).mean() * 100 if len(yr_trades) else float("nan")
        yearly_rows.append((yr, len(yr_trades), start_eq, end_eq, ret_pct, gpf, npf, winr))
        print(f"  {yr:<6} {len(yr_trades):>7} {start_eq:>14,.0f} {end_eq:>14,.0f} {ret_pct:>+13.1%} "
              f"{gpf:>9.3f} {npf:>8.3f} {winr:>6.1f}%")
        eq_before = end_eq

    print("  " + "-" * 106)
    print(f"  {'TOTAL':<6} {len(tr):>7} {START_CAP:>14,.0f} {end_balance:>14,.0f} "
          f"{end_balance/START_CAP-1:>+13.1%}")
    print("=" * 110)

    era_2017 = tr[tr["exit_time"].dt.year == 2017]
    era_18_25 = tr[tr["exit_time"].dt.year >= 2018]
    era_2017_end = float(era_2017["_running_eq"].iloc[-1]) if len(era_2017) else START_CAP
    print(f"\nEra split within the SAME continuous run (no capital reset at the boundary):")
    print(f"  2017 alone:       {START_CAP:>12,.0f} -> {era_2017_end:>12,.0f}  ({era_2017_end/START_CAP-1:+.1%}), {len(era_2017)} trades")
    print(f"  2018-2025 alone:  {era_2017_end:>12,.0f} -> {end_balance:>12,.0f}  ({end_balance/era_2017_end-1:+.1%}), {len(era_18_25)} trades")

    # ---- headline full-period number ----
    print(f"\n{'='*110}")
    print("  FULL-PERIOD CONTINUOUS RESULT, 2017-01-02 -> 2025-12-31 (9 years, ONE account)")
    print(f"{'='*110}")
    print(f"  Starting balance:        ${START_CAP:,.0f}")
    print(f"  Ending balance:          ${end_balance:,.0f}")
    print(f"  Total return:            {end_balance/START_CAP-1:+.1%}")
    print(f"  Total trades:            {len(tr)}")
    print(f"  Look-ahead guard:        {guard}")
    print(f"  Gross PF (whole span):   {full_gross_pf:.3f}")
    print(f"  Net PF (whole span):     {full_net_pf:.3f}")
    print(f"  Sharpe (daily, ann.):    {full_sharpe:+.2f}")
    print(f"  Max drawdown (daily-resampled equity, sec-10-style metric): {full_maxdd*100:.1f}%")
    print(f"  Max drawdown (TRADE-BY-TRADE equity path, the real worst peak-to-trough this")
    print(f"    exact account would have hit before recovering): {trade_level_maxdd*100:.1f}%")
    if maxdd_date is not None:
        print(f"    -> peak equity ${peak_before_dd:,.0f} reached before the trough; trough reached at "
              f"trade exiting {maxdd_date.date()}")

    # ---- buy-and-hold comparison, same continuous span ----
    print(f"\n{'='*110}")
    print("  BUY-AND-HOLD XAUUSD COMPARISON, SAME 2017-01-02 -> 2025-12-31 SPAN, SAME $100,000")
    print(f"{'='*110}")
    bh_eq, p0, p1 = bh(m, "2017-01-01", "2025-12-31", START_CAP)
    bh_daily = m["mid_close"].resample("1D").last().dropna()
    bh_daily_ret = bh_daily.pct_change().dropna()
    bh_equity_curve = (1.0 + bh_daily_ret).cumprod() * START_CAP
    bh_maxdd = max_drawdown(bh_equity_curve / START_CAP)
    bh_sharpe = sharpe(bh_daily_ret, BARS_PER_YEAR)
    print(f"  XAUUSD price:            ${p0:,.2f} (2017-01-02)  ->  ${p1:,.2f} (2025-12-31)")
    print(f"  Buy-and-hold ending:     ${bh_eq:,.0f}")
    print(f"  Buy-and-hold return:     {bh_eq/START_CAP-1:+.1%}")
    print(f"  Buy-and-hold Sharpe:     {bh_sharpe:+.2f}")
    print(f"  Buy-and-hold max DD:     {bh_maxdd*100:.1f}%")
    print(f"\n  STRATEGY  {end_balance/START_CAP-1:+.1%}  vs  BUY-AND-HOLD  {bh_eq/START_CAP-1:+.1%}  "
          f"-> strategy {'BEATS' if end_balance > bh_eq else 'LOSES TO'} buy-and-hold on continuous dollars")

    # ---- save a CSV of the year-by-year table + summary for the record ----
    out = _ROOT / "results" / "retest_xauusd_2017_2025_continuous.csv"
    df = pd.DataFrame(yearly_rows, columns=["year", "n_trades", "start_equity", "end_equity",
                                              "year_return_pct", "gross_pf", "net_pf", "win_rate_pct"])
    df.to_csv(out, index=False)
    print(f"\nYear-by-year table saved: {out}")


if __name__ == "__main__":
    main()
