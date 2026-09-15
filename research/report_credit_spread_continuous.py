#!/usr/bin/env python3
"""
DEFINED-RISK CREDIT SPREAD (delta-10 short + protective long leg), sec 27 --
year-by-year / drawdown-recovery / trade-outcome reporting on the SAME
continuous run the original script already produces.

REPORTING ONLY. No new rule, no new parameter. run_combined_book() is
imported and called UNCHANGED from research/credit_spread_iv_filter.py --
same data, same Black-Scholes/real-VIX pricing, same 2% risk-per-position
sizing, same shared put-book+call-book capital account, same 4 a priori
cells (1pct/2pct width x FILTERED/UNFILTERED). Sec 27 already ran each cell
CONTINUOUSLY across the whole data window (no split into two eras) -- this
script extracts the additional detail that wasn't printed the first time:
a year-by-year log-return table, max-drawdown-with-recovery-date on the
daily mark-to-market equity curve (not just the max_dd number), and a
3-way trade-outcome split (full max loss / partial loss / full profit)
instead of just the "hit full max loss" binary already reported.

All 4 cells are reported side by side, exactly as sec 27 did -- sec 27's
own verdict was "MIXED, not a clean yes" across all 4, and UNFILTERED beat
FILTERED on every metric in both widths, so there is no single cell this
project has already designated as "the" confirmed rule to the exclusion of
the others; picking one silently here would be a new, unstated choice.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.metrics import sharpe, max_drawdown, profit_factor
from research.delta10_iv_filter import load_data, IV_LOOKBACK, TOP_TERCILE, BARS_PER_YEAR
import research.credit_spread_iv_filter as cs

START_CAPITAL = cs.START_CAPITAL
WIDTH_PCTS = cs.WIDTH_PCTS


def year_table(daily_ret: pd.Series, equity: pd.Series) -> pd.DataFrame:
    idx = daily_ret.index
    eq = equity.reindex(idx)
    eq_prev = eq.shift(1)
    eq_prev.iloc[0] = START_CAPITAL
    years = sorted(idx.year.unique())
    out = []
    for yr in years:
        m = idx.year == yr
        start_eq = float(eq_prev[m].iloc[0])
        end_eq = float(eq[m].iloc[-1])
        n_obs = int((daily_ret[m] != 0.0).sum())
        out.append(dict(year=int(yr), n_active_days=n_obs, start_equity=start_eq, end_equity=end_eq,
                         year_return_pct=(end_eq / start_eq - 1.0) * 100))
    return pd.DataFrame(out)


def drawdown_with_recovery(equity: pd.Series) -> dict:
    running_peak = equity.cummax()
    dd = 1.0 - equity / running_peak
    max_dd = float(dd.max())
    trough_date = dd.idxmax()
    peak_date = equity.loc[:trough_date].idxmax()
    peak_value = float(equity.loc[peak_date])
    trough_value = float(equity.loc[trough_date])
    after = equity.loc[equity.index > trough_date]
    hit = after[after >= peak_value]
    recovery_date = hit.index[0] if len(hit) else None
    return dict(max_dd=max_dd, peak_date=peak_date, peak_value=peak_value,
                trough_date=trough_date, trough_value=trough_value, recovery_date=recovery_date)


def trade_outcome_split(tr: pd.DataFrame) -> dict:
    if tr.empty:
        return dict(n=0, full_profit=0, partial_loss=0, full_max_loss=0)
    wins = tr[tr["win"]]
    losses = tr[~tr["win"]]
    full_max_loss = int(losses["hit_full_max_loss"].sum())
    partial_loss = int(len(losses) - full_max_loss)
    return dict(n=len(tr), full_profit=int(len(wins)), partial_loss=partial_loss, full_max_loss=full_max_loss)


def bh_spy_full(df: pd.DataFrame) -> dict:
    ret = df["spy"].pct_change().dropna()
    eq = (1 + ret).cumprod() * START_CAPITAL
    dd = drawdown_with_recovery(eq)
    return dict(ending=float(eq.iloc[-1]), total_ret=float(eq.iloc[-1] / START_CAPITAL - 1),
                sharpe=sharpe(ret, BARS_PER_YEAR), **dd)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    W = 118
    df = load_data()
    print(f"Data span: {df.index.min().date()} -> {df.index.max().date()} ({len(df):,} trading days)\n")

    iv_rank = df["vix"].rolling(IV_LOOKBACK, min_periods=IV_LOOKBACK).rank(pct=True)
    eligible_filtered = (iv_rank >= TOP_TERCILE).fillna(False)
    eligible_unfiltered = iv_rank.notna()

    bh = bh_spy_full(df)

    for width_name, width_pct in WIDTH_PCTS.items():
        for group_name, elig in [("FILTERED", eligible_filtered), ("UNFILTERED", eligible_unfiltered)]:
            label = f"{width_name} / {group_name}"
            tr, daily_ret, equity, guard, rej = cs.run_combined_book(df, elig, group_name, width_pct)

            print("=" * W)
            print(f"  {label}  --  ONE CONTINUOUS ${START_CAPITAL:,.0f} ACCOUNT, {df.index.min().date()} -> {df.index.max().date()}")
            print("=" * W)

            # ---- 2. year-by-year, prominently ----
            yt = year_table(daily_ret, equity)
            print(f"  {'year':<6} {'active days':>11} {'start equity':>14} {'end equity':>14} {'year return %':>14}")
            print("  " + "-" * (W - 4))
            for _, r in yt.iterrows():
                print(f"  {int(r['year']):<6} {int(r['n_active_days']):>11} {r['start_equity']:>14,.0f} "
                      f"{r['end_equity']:>14,.0f} {r['year_return_pct']:>+13.1f}%")
            end_balance = float(equity.iloc[-1])
            print("  " + "-" * (W - 4))
            print(f"  {'TOTAL':<6} {int((daily_ret!=0).sum()):>11} {START_CAPITAL:>14,.0f} {end_balance:>14,.0f} "
                  f"{(end_balance/START_CAPITAL-1)*100:>+13.1f}%")

            # ---- 3. max drawdown + recovery, prominently ----
            dd = drawdown_with_recovery(equity)
            print(f"\n  MAX DRAWDOWN OF THE FULL COMBINED EQUITY CURVE:")
            print(f"    Peak equity ${dd['peak_value']:,.0f} on {dd['peak_date'].date()}")
            print(f"    Trough equity ${dd['trough_value']:,.0f} on {dd['trough_date'].date()}")
            print(f"    Max drawdown: {dd['max_dd']*100:.2f}%")
            if dd["recovery_date"] is not None:
                days_trough_to_rec = (dd["recovery_date"] - dd["trough_date"]).days
                days_peak_to_rec = (dd["recovery_date"] - dd["peak_date"]).days
                print(f"    Recovered on {dd['recovery_date'].date()}  "
                      f"({days_trough_to_rec} days trough->recovery, {days_peak_to_rec} days total peak->recovery)")
            else:
                print(f"    NOT recovered by end of data ({equity.index[-1].date()}); "
                      f"current equity ${end_balance:,.0f} vs peak ${dd['peak_value']:,.0f}")

            # ---- 1. headline ----
            print(f"\n  FULL-PERIOD RESULT: ${START_CAPITAL:,.0f} -> ${end_balance:,.0f}  "
                  f"({(end_balance/START_CAPITAL-1)*100:+.1f}%)   trades={len(tr)}   "
                  f"Sharpe={sharpe(daily_ret, BARS_PER_YEAR):+.2f}   net PF={profit_factor(daily_ret):.3f}")

            # ---- 5. trade-outcome split ----
            oc = trade_outcome_split(tr)
            print(f"\n  TRADE OUTCOME SPLIT ({oc['n']} total trades):")
            if oc["n"]:
                print(f"    Full profit (expired with short leg worthless / net win):  {oc['full_profit']:>5}  "
                      f"({oc['full_profit']/oc['n']*100:.1f}%)")
                print(f"    Partial loss (loss, but did NOT hit the full max-loss cap): {oc['partial_loss']:>5}  "
                      f"({oc['partial_loss']/oc['n']*100:.1f}%)")
                print(f"    Full max loss (loss hit within 1% of the computed cap):     {oc['full_max_loss']:>5}  "
                      f"({oc['full_max_loss']/oc['n']*100:.1f}%)")
            print()

    # ---- 4. buy-and-hold SPY, same full span, printed once (identical span for all 4 cells) ----
    print("=" * W)
    print(f"  BUY-AND-HOLD SPY, SAME FULL SPAN {df.index.min().date()} -> {df.index.max().date()}, SAME ${START_CAPITAL:,.0f}")
    print("=" * W)
    print(f"  Ending balance: ${bh['ending']:,.0f}   Total return: {bh['total_ret']*100:+.1f}%   Sharpe: {bh['sharpe']:+.2f}")
    print(f"  Max drawdown: {bh['max_dd']*100:.1f}%  (peak ${bh['peak_value']:,.0f} on {bh['peak_date'].date()}, "
          f"trough ${bh['trough_value']:,.0f} on {bh['trough_date'].date()}"
          + (f", recovered {bh['recovery_date'].date()})" if bh["recovery_date"] is not None else ", NOT recovered by end of data)"))


if __name__ == "__main__":
    main()
