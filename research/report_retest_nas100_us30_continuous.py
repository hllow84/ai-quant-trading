#!/usr/bin/env python3
"""
RETEST OR30/1R, NAS100 and US30 -- ONE CONTINUOUS compounding run each,
across the full available M1 history per instrument, same treatment as
research/report_retest_xauusd_2017_2025_continuous.py.

REPORTING ONLY. No new rule, no new parameter, no new trial. Entry logic is
byte-identical to sec 10.5/10.6/10.9: orb(retest=True, retest_tol_frac=0.10,
or_minutes=30, target="1R", stop_mode="or_range", 09:30 ET session),
simulate_trades + de_overlap, 1% fixed-fractional risk, index cost model
(run_orb.COST_BPS + run_orb.slip_bps) -- all reused unchanged.

DATA SPAN, checked not assumed: NAS100/US30 M1 on disk is split across two
files per instrument -- data/{NAS100,US30}_M1RTH_2013_2017_cfd_dukascopy.csv
(RTH-only, i.e. regular-trading-hours bars only) and
data/{NAS100,US30}_M1_2018_2025_cfd_dukascopy.csv (full 23h bars). Both
start 2013-09-30 and run to 2025-12-31, concatenated below into ONE
continuous frame per instrument with no gap of substance (a few New Year
days between files, a holiday close, not a data hole). The 2013-2017 file
being RTH-only does not affect this strategy: ORB only ever trades the
09:30-16:00 ET session, which RTH-only data fully covers.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

import run_orb as ro
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

INSTRUMENTS = {
    "NAS100": (D / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv", D / "NAS100_M1_2018_2025_cfd_dukascopy.csv"),
    "US30":   (D / "US30_M1RTH_2013_2017_cfd_dukascopy.csv",   D / "US30_M1_2018_2025_cfd_dukascopy.csv"),
}


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
                                     cost_bps=ro.COST_BPS, slip_bps_fn=ro.slip_bps))
    tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True)
    tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True)
    return tr.sort_values("exit_time").reset_index(drop=True)


def bh(m: pd.DataFrame, start_cap: float):
    p0, p1 = float(m["mid_close"].iloc[0]), float(m["mid_close"].iloc[-1])
    return start_cap * p1 / p0, p0, p1


def run_one(inst: str, f_early: Path, f_late: Path) -> None:
    m_e, spot_e = mid_frame(f_early)
    m_l, spot_l = mid_frame(f_late)
    print(f"\n{'#'*112}\n  {inst}\n{'#'*112}")
    print(f"  early file: {f_early.name}: {len(m_e):,} bars, {m_e.index[0]} -> {m_e.index[-1]}")
    print(f"  late  file: {f_late.name}: {len(m_l):,} bars, {m_l.index[0]} -> {m_l.index[-1]}")
    gap = m_l.index[0] - m_e.index[-1]
    print(f"  gap between files: {gap}")
    assert m_e.index[-1] < m_l.index[0], f"{inst}: files overlap"

    m = pd.concat([m_e, m_l]).sort_index()
    spot = pd.concat([spot_e, spot_l]).sort_index()
    assert m.index.is_monotonic_increasing and not m.index.has_duplicates
    daily_index = aggregate_daily(spot).index
    print(f"  continuous frame: {len(m):,} bars, {m.index[0]} -> {m.index[-1]}")

    tr = build_trades(m)
    print(f"  RETEST OR30/1R trades over the full continuous span: {len(tr)}")
    print(f"  First entry: {tr['entry_time'].min()}   Last exit: {tr['exit_time'].max()}")

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

    # ---- continuous trade-by-trade compounding path, indexed by exit_time ----
    net_R = tr["net_R"].to_numpy()
    eq = START_CAP
    path = np.empty(len(net_R))
    for i, r in enumerate(net_R):
        eq *= (1.0 + RISK_PER_TRADE * r)
        path[i] = eq
    end_balance = path[-1] if len(path) else START_CAP
    tr = tr.assign(_running_eq=path)

    equity_s = pd.Series(path, index=pd.DatetimeIndex(tr["exit_time"]))
    equity_s = pd.concat([pd.Series([START_CAP], index=[tr["entry_time"].iloc[0]]), equity_s])
    running_peak = equity_s.cummax()
    dd = 1.0 - equity_s / running_peak
    trade_level_maxdd = float(dd.max())
    trough_trade_date = dd.idxmax()
    peak_trade_date = equity_s.loc[:trough_trade_date].idxmax()
    peak_before_dd = float(equity_s.loc[peak_trade_date])

    after = equity_s.loc[equity_s.index > trough_trade_date]
    hit = after[after >= peak_before_dd]
    recovery_trade_date = hit.index[0] if len(hit) else None

    # ---- year-by-year ----
    years = sorted(tr["exit_time"].dt.year.unique())
    print(f"\n{'='*112}")
    print(f"  YEAR-BY-YEAR -- {inst}, ONE CONTINUOUS $100,000 ACCOUNT, RETEST OR30/1R")
    print(f"{'='*112}")
    print(f"  {'year':<6} {'trades':>7} {'start equity':>14} {'end equity':>14} {'year return %':>14} "
          f"{'gross PF':>9} {'net PF':>8} {'win %':>7}")
    print("  " + "-" * 106)
    eq_before = START_CAP
    yearly_rows = []
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
    print(f"{'='*112}")

    # ---- headline + drawdown ----
    print(f"\n  FULL-PERIOD CONTINUOUS RESULT, {tr['entry_time'].min().date()} -> {tr['exit_time'].max().date()} (ONE account)")
    print(f"    Starting balance: ${START_CAP:,.0f}    Ending balance: ${end_balance:,.0f}    "
          f"Total return: {end_balance/START_CAP-1:+.1%}")
    print(f"    Trades: {len(tr)}   Guard: {guard}   Gross PF: {full_gross_pf:.3f}   Net PF: {full_net_pf:.3f}   "
          f"Sharpe: {full_sharpe:+.2f}")
    print(f"\n  MAXIMUM DRAWDOWN (trade-by-trade equity path):")
    print(f"    Peak equity ${peak_before_dd:,.0f}" + (f" reached after trade exiting {peak_trade_date.date()}" if peak_trade_date is not None else ""))
    print(f"    Max drawdown: {trade_level_maxdd*100:.1f}%" + (f", trough at trade exiting {trough_trade_date.date()}" if trough_trade_date is not None else ""))
    if recovery_trade_date is not None:
        print(f"    Recovered: equity back to/above ${peak_before_dd:,.0f} by trade exiting {recovery_trade_date.date()}")
        if trough_trade_date is not None:
            print(f"    Recovery time from trough: {(recovery_trade_date - trough_trade_date).days} calendar days")
        if peak_trade_date is not None:
            print(f"    Recovery time from original peak: {(recovery_trade_date - peak_trade_date).days} calendar days")
    else:
        print(f"    NOT recovered by the end of available data ({tr['exit_time'].max().date()}); "
              f"ending equity ${end_balance:,.0f} vs peak ${peak_before_dd:,.0f}")

    # ---- buy and hold, same span ----
    bh_end, p0, p1 = bh(m, START_CAP)
    bh_daily = m["mid_close"].resample("1D").last().dropna()
    bh_daily_ret = bh_daily.pct_change().dropna()
    bh_equity_curve = (1.0 + bh_daily_ret).cumprod() * START_CAP
    bh_maxdd = max_drawdown(bh_equity_curve / START_CAP)
    bh_sharpe = sharpe(bh_daily_ret, BARS_PER_YEAR)
    print(f"\n  BUY-AND-HOLD {inst} COMPARISON, SAME {m.index[0].date()} -> {m.index[-1].date()} SPAN, SAME $100,000")
    print(f"    Price: {p0:,.1f} ({m.index[0].date()}) -> {p1:,.1f} ({m.index[-1].date()})")
    print(f"    Buy-and-hold ending: ${bh_end:,.0f}  ({bh_end/START_CAP-1:+.1%})   Sharpe: {bh_sharpe:+.2f}   "
          f"Max DD: {bh_maxdd*100:.1f}%")
    print(f"    STRATEGY {end_balance/START_CAP-1:+.1%} (maxDD {trade_level_maxdd*100:.1f}%)  vs  "
          f"BUY-AND-HOLD {bh_end/START_CAP-1:+.1%} (maxDD {bh_maxdd*100:.1f}%)  "
          f"-> strategy {'BEATS' if end_balance > bh_end else 'LOSES TO'} buy-and-hold")

    out = _ROOT / "results" / f"retest_{inst.lower()}_2013_2025_continuous.csv"
    pd.DataFrame(yearly_rows, columns=["year", "n_trades", "start_equity", "end_equity",
                                        "year_return_pct", "gross_pf", "net_pf", "win_rate_pct"]).to_csv(out, index=False)
    print(f"\n  Year-by-year table saved: {out}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for inst, (f_early, f_late) in INSTRUMENTS.items():
        run_one(inst, f_early, f_late)


if __name__ == "__main__":
    main()
