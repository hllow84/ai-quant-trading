#!/usr/bin/env python3
"""
AUDITED ICT SMC FULL MODEL (strategies_pine/ICT_SMC_Full_FTMO_v2.pine), EURUSD
-- ONE CONTINUOUS compounding run across the full available M1 history,
same treatment as the ORB full-period continuous tests.

REPORTING ONLY. No new rule, no re-tuning, no new filter. Reuses
run_ict_smc.py's own run_state_machine() and run_one_window() UNCHANGED --
same Pine constants (pivot_len=5, disp_mult=1.5, ob_max_bars=50,
sweep_window=5, rr_ratio=2.0, London/NY kill zones), same MIN_STOP_TICKS/
MIN_STOP_BPS floor, same INDEX_COST_BPS cost model (commission 0.35bps,
slippage 0.15/1.00bps), same 1% fixed-fractional risk.

WHY THIS IS DIFFERENT FROM SEC 28's TWO EURUSD CELLS: sec 28 ran
"EURUSD in-regime 2018-2025" and "EURUSD out-of-regime 2013-2017" as TWO
SEPARATE backtests, each loading its own file and each starting its own
fresh $100,000 (and, more importantly, each running run_state_machine()
independently on its own file, so the daily-EMA-bias/structure state resets
at the 2018 boundary instead of carrying real history across it). This
script concatenates BOTH EURUSD files into ONE continuous M1 frame first,
runs the state machine ONCE on the full continuous history, then resolves
ONE trade stream across the whole span with run_one_window() -- an honest
single continuous account, matching how a live account would actually
experience it, not two independently-reset backtests reported side by side.

DATA SPAN, checked not assumed: EURUSD M1 is split across
data/EURUSD_M1_2013_2017_spot_dukascopy.csv and
data/EURUSD_M1_2018_2025_spot_dukascopy.csv. Concatenated below with a
data-integrity check (no overlap, monotonic, no duplicate timestamps).

PRIOR RESULT, restated plainly, since it does not match a "carried by one
lucky year" story: sec 28 found EURUSD in-regime 2018-2025 ending at $6,159
(-93.8%, max_dd 94.8%) and EURUSD out-of-regime 2013-2017 ending at $18,603
(-81.4%, max_dd 83.9%) -- BOTH windows are severe, independent near-total
losses, not a strong result carried by a single good year. This script
re-verifies that finding under a single continuous account rather than
assuming it.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

import run_ict_smc as ict
from research.metrics import sharpe, max_drawdown, profit_factor

D = _ROOT / "data"
START_CAP = ict.START_CAP
BARS_PER_YEAR = ict.BARS_PER_YEAR
RISK_PER_TRADE = ict.RISK_PER_TRADE if hasattr(ict, "RISK_PER_TRADE") else None

FILE_EARLY = D / "EURUSD_M1_2013_2017_spot_dukascopy.csv"
FILE_LATE = D / "EURUSD_M1_2018_2025_spot_dukascopy.csv"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    W = 116
    m_e = ict.load_dukas_mid(FILE_EARLY)
    m_l = ict.load_dukas_mid(FILE_LATE)
    print(f"early file: {FILE_EARLY.name}: {len(m_e):,} bars, {m_e.index[0]} -> {m_e.index[-1]}")
    print(f"late  file: {FILE_LATE.name}: {len(m_l):,} bars, {m_l.index[0]} -> {m_l.index[-1]}")
    gap = m_l.index[0] - m_e.index[-1]
    print(f"gap between files: {gap}")
    assert m_e.index[-1] < m_l.index[0], "files overlap -- would double-count bars"

    m1 = pd.concat([m_e, m_l]).sort_index()
    assert m1.index.is_monotonic_increasing and not m1.index.has_duplicates
    print(f"continuous frame: {len(m1):,} bars, {m1.index[0]} -> {m1.index[-1]}\n")

    print("computing ICT SMC state machine on the FULL continuous history (slow O(n) pass) ...", flush=True)
    sig = ict.run_state_machine(m1, ict.MINTICK["EURUSD"])

    print("resolving ONE continuous trade stream across the whole span ...", flush=True)
    tr = ict.run_one_window(m1, "2013-01-01", "2025-12-31", sig,
                             ict.INDEX_COST_BPS, ict.index_slip_bps,
                             "EURUSD continuous 2013-2025", ict.MINTICK["EURUSD"])
    tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True)
    tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True)
    tr = tr.sort_values("exit_time").reset_index(drop=True)
    print(f"\n{len(tr)} trades over the full continuous span")
    if tr.empty:
        print("NO TRADES -- cannot report further.")
        return
    print(f"First entry: {tr['entry_time'].min()}   Last exit: {tr['exit_time'].max()}\n")

    # ---- continuous trade-by-trade compounding path ----
    net_R = tr["net_R"].to_numpy()
    eq = START_CAP
    path = np.empty(len(net_R))
    ruin_trade = None
    for i, r in enumerate(net_R):
        eq *= (1.0 + ict.RISK_PER_TRADE * r)
        path[i] = eq
        if ruin_trade is None and eq <= START_CAP * 0.05:
            ruin_trade = i + 1
    end_balance = path[-1]
    tr = tr.assign(_running_eq=path)

    equity_s = pd.concat([pd.Series([START_CAP], index=[tr["entry_time"].iloc[0]]),
                          pd.Series(path, index=pd.DatetimeIndex(tr["exit_time"]))])
    running_peak = equity_s.cummax()
    dd = 1.0 - equity_s / running_peak
    max_dd = float(dd.max())
    trough_date = dd.idxmax()
    peak_date = equity_s.loc[:trough_date].idxmax()
    peak_val = float(equity_s.loc[peak_date])
    trough_val = float(equity_s.loc[trough_date])
    after = equity_s.loc[equity_s.index > trough_date]
    hit = after[after >= peak_val]
    recovery_date = hit.index[0] if len(hit) else None

    # ---- year-by-year ----
    years = sorted(tr["exit_time"].dt.year.unique())
    print("=" * W)
    print("  YEAR-BY-YEAR -- ONE CONTINUOUS $100,000 ACCOUNT, ICT SMC FULL MODEL, EURUSD, 2013-2025")
    print("=" * W)
    print(f"  {'year':<6} {'trades':>7} {'start equity':>14} {'end equity':>14} {'year return %':>14} "
          f"{'gross PF':>9} {'net PF':>8} {'win %':>7}")
    print("  " + "-" * (W - 4))
    eq_before = START_CAP
    yearly_rows = []
    for yr in years:
        m = tr["exit_time"].dt.year == yr
        yt = tr[m]
        start_eq = eq_before
        end_eq = float(yt["_running_eq"].iloc[-1])
        ret_pct = end_eq / start_eq - 1.0
        gpf = profit_factor(yt["gross_R"]) if len(yt) else float("nan")
        npf = profit_factor(yt["net_R"]) if len(yt) else float("nan")
        winr = (yt["net_R"] > 0).mean() * 100 if len(yt) else float("nan")
        yearly_rows.append((yr, len(yt), start_eq, end_eq, ret_pct, gpf, npf, winr))
        print(f"  {yr:<6} {len(yt):>7} {start_eq:>14,.0f} {end_eq:>14,.0f} {ret_pct:>+13.1%} "
              f"{gpf:>9.3f} {npf:>8.3f} {winr:>6.1f}%")
        eq_before = end_eq
    print("  " + "-" * (W - 4))
    print(f"  {'TOTAL':<6} {len(tr):>7} {START_CAP:>14,.0f} {end_balance:>14,.0f} "
          f"{end_balance/START_CAP-1:>+13.1%}")
    print("=" * W)

    # log-return contribution per year, for spotting concentration
    yr_log_ret = pd.Series({row[0]: np.log(row[3] / row[2]) if row[2] > 0 else float("nan") for row in yearly_rows})
    print(f"\nPer-year log-return contribution (for spotting concentration):")
    for yr, v in yr_log_ret.items():
        print(f"  {yr}: {v:+.3f}")
    total_log = yr_log_ret.sum()
    print(f"Sum of yearly log-returns: {total_log:+.3f} (log-space total return {(np.exp(total_log)-1)*100:+.1f}%, "
          f"should match TOTAL row above)")

    print(f"\n{'='*W}")
    print(f"  MAXIMUM DRAWDOWN OF THE FULL COMBINED EQUITY CURVE")
    print(f"{'='*W}")
    print(f"  Peak equity ${peak_val:,.0f} reached {peak_date.date()}")
    print(f"  Trough equity ${trough_val:,.0f} reached {trough_date.date()}")
    print(f"  Max drawdown: {max_dd*100:.1f}%")
    if recovery_date is not None:
        print(f"  Recovered (equity back to/above ${peak_val:,.0f}) on {recovery_date.date()}")
        print(f"  Time from trough to recovery: {(recovery_date - trough_date).days} calendar days")
        print(f"  Time from original peak to recovery: {(recovery_date - peak_date).days} calendar days")
    else:
        print(f"  NOT recovered by the end of available data ({equity_s.index[-1].date()}); "
              f"ending equity ${end_balance:,.0f} vs peak ${peak_val:,.0f}")

    print(f"\n{'='*W}")
    print(f"  HOW CLOSE TO RUIN, AND WHEN (bar: equity <= 5% of starting capital, i.e. a >=95% loss)")
    print(f"{'='*W}")
    min_eq = float(equity_s.min())
    min_eq_date = equity_s.idxmin()
    print(f"  Lowest equity point in the ENTIRE continuous run: ${min_eq:,.0f} ({min_eq/START_CAP*100:.1f}% of start) "
          f"on {min_eq_date.date()}")
    if ruin_trade is not None:
        print(f"  Equity FIRST dropped to <=5% of starting capital at trade #{ruin_trade} "
              f"(exiting {tr['exit_time'].iloc[ruin_trade-1].date()})")
        print(f"  Ending balance ${end_balance:,.0f} is "
              + ("ABOVE" if end_balance > START_CAP * 0.05 else "AT/BELOW")
              + " that 5%-of-start ruin threshold -- "
              + ("the account partially recovered from near-total loss" if end_balance > min_eq * 1.5 else
                 "the account stayed near ruin"))
    else:
        print(f"  Equity NEVER dropped to <=5% of starting capital anywhere in this run.")

    full_sharpe = sharpe(pd.Series(net_R * ict.RISK_PER_TRADE, index=tr["exit_time"]).groupby(level=0).sum(), BARS_PER_YEAR)
    full_gross_pf = profit_factor(tr["gross_R"])
    full_net_pf = profit_factor(tr["net_R"])
    print(f"\n{'='*W}")
    print(f"  FULL-PERIOD CONTINUOUS RESULT, {tr['entry_time'].min().date()} -> {tr['exit_time'].max().date()} (ONE account)")
    print(f"{'='*W}")
    print(f"  Starting balance: ${START_CAP:,.0f}    Ending balance: ${end_balance:,.0f}    "
          f"Total return: {end_balance/START_CAP-1:+.1%}")
    print(f"  Trades: {len(tr)}   Gross PF: {full_gross_pf:.3f}   Net PF: {full_net_pf:.3f}   Sharpe: {full_sharpe:+.2f}")

    p0, p1 = float(m1["mid_close"].iloc[0]), float(m1["mid_close"].iloc[-1])
    bh_end = START_CAP * p1 / p0
    bh_daily = m1["mid_close"].resample("1D").last().dropna()
    bh_daily_ret = bh_daily.pct_change().dropna()
    bh_equity_curve = (1.0 + bh_daily_ret).cumprod() * START_CAP
    bh_maxdd = max_drawdown(bh_equity_curve / START_CAP)
    bh_sharpe = sharpe(bh_daily_ret, BARS_PER_YEAR)
    print(f"\n{'='*W}")
    print(f"  BUY-AND-HOLD EURUSD COMPARISON, SAME {m1.index[0].date()} -> {m1.index[-1].date()} SPAN, SAME $100,000")
    print(f"{'='*W}")
    print(f"  Price: {p0:.5f} ({m1.index[0].date()}) -> {p1:.5f} ({m1.index[-1].date()})")
    print(f"  Buy-and-hold ending: ${bh_end:,.0f}  ({bh_end/START_CAP-1:+.1%})   Sharpe: {bh_sharpe:+.2f}   "
          f"Max DD: {bh_maxdd*100:.1f}%")
    print(f"  STRATEGY {end_balance/START_CAP-1:+.1%} (maxDD {max_dd*100:.1f}%)  vs  "
          f"BUY-AND-HOLD {bh_end/START_CAP-1:+.1%} (maxDD {bh_maxdd*100:.1f}%)  "
          f"-> strategy {'BEATS' if end_balance > bh_end else 'LOSES TO'} buy-and-hold")

    out = _ROOT / "results" / "ict_smc_eurusd_2013_2025_continuous.csv"
    pd.DataFrame(yearly_rows, columns=["year", "n_trades", "start_equity", "end_equity",
                                        "year_return_pct", "gross_pf", "net_pf", "win_rate_pct"]).to_csv(out, index=False)
    print(f"\nYear-by-year table saved: {out}")


if __name__ == "__main__":
    main()
