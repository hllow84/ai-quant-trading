#!/usr/bin/env python3
"""
run_ftmo_swing.py — Swing (H4/Daily) versions of the three gold archetypes.

Structural follow-up to the M15 intraday kills: widen stops so real costs fall
from ~30% of risk to ~1-3%. Signals + resolution on H4; Daily/weekly context
mapped causally. Multi-day holds. Same cost model (real spread + $0.07/oz
commission + news-hour slippage). 1% risk/trade. NO tuning.

Reports gross-vs-net R, cost_R as % of risk, look-ahead guard, Sharpe(252),
DSR (n_configs=3), PF, win, trades, max DD, and a buy-and-hold gold comparison.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_mid, resample_mid, load_daily_spot
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import (
    sharpe, sortino, max_drawdown, profit_factor, hit_rate, deflated_sharpe_ratio,
)
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns,
    build_position_series,
)
from research.ftmo_rules import rolling_pass_rate
from strategies.ftmo_gold_swing import (
    build_swing_trend, build_swing_breakout, build_swing_meanrev,
)

BARS_PER_YEAR = 252


def score(name, candidates, h4, daily_index):
    raw = simulate_trades(h4, candidates, strictly_after=True)   # resolve on H4
    trades = de_overlap(raw)
    if trades.empty:
        return dict(name=name, n=0, trades=trades, guard="N/A", sharpe=float("nan"))

    pos = build_position_series(trades, h4.index)
    h4_ret = h4["mid_close"].pct_change()
    try:
        guard_look_ahead(pos, h4_ret, threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{exc}"

    daily_ret = build_daily_returns(trades, daily_index)
    equity    = equity_from_returns(daily_ret)
    return dict(
        name=name, n=len(trades), trades=trades, daily_ret=daily_ret, equity=equity,
        guard=guard,
        sharpe=sharpe(daily_ret, BARS_PER_YEAR),
        sortino=sortino(daily_ret, BARS_PER_YEAR),
        pf=profit_factor(trades["net_R"]),
        gross_pf=profit_factor(trades["gross_R"]),
        win=hit_rate(trades["net_R"]),
        mdd=max_drawdown(equity),
        gross_R_mean=float(trades["gross_R"].mean()),
        cost_R_mean=float(trades["cost_R"].mean()),
        net_R_mean=float(trades["net_R"].mean()),
        risk_med=float(trades["risk_price"].median()),
        skew=float(daily_ret.skew()), ekurt=float(daily_ret.kurtosis()),
        n_targets=int((trades["reason"] == "target").sum()),
        n_stops=int((trades["reason"] == "stop").sum()),
        n_time=int((trades["reason"] == "time").sum()),
    )


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("Loading M1 mid ...", flush=True)
    m1 = load_m1_mid()
    print("Resampling H4 / Daily / Weekly ...", flush=True)
    h4     = resample_mid(m1, "4h")
    daily  = resample_mid(m1, "1D")     # causal (right-labeled) for indicators
    weekly = resample_mid(m1, "1W")
    daily_bench = load_daily_spot()      # for the calendar-daily benchmark
    daily_index = daily_bench.index

    print("Building candidates ...", flush=True)
    ca = build_swing_trend(h4, daily)
    cb = build_swing_breakout(h4, weekly)
    cc = build_swing_meanrev(h4, daily)
    print(f"  A {len(ca):,}  B {len(cb):,}  C {len(cc):,} candidates")

    print("Scoring ...", flush=True)
    ra = score("A swing-trend",     ca, h4, daily_index)
    rb = score("B swing-breakout",  cb, h4, daily_index)
    rc = score("C swing-meanrev",   cc, h4, daily_index)
    results = [ra, rb, rc]

    # DSR, n_configs = 3
    sr_trials = [(r["sharpe"] if not np.isnan(r["sharpe"]) else 0.0) for r in results]
    for r in results:
        if r["n"] == 0 or np.isnan(r["sharpe"]):
            r["dsr"] = float("nan"); continue
        r["dsr"], _ = deflated_sharpe_ratio(
            sr_best=r["sharpe"], sr_trials=sr_trials, n_obs=len(r["daily_ret"]),
            skewness=r["skew"], excess_kurtosis=r["ekurt"])

    # Buy-and-hold gold benchmark (full period, daily)
    bh_ret = daily_bench["mid_close"].pct_change().dropna()
    bh_sharpe = sharpe(bh_ret, BARS_PER_YEAR)
    bh_pf     = profit_factor(bh_ret)
    bh_mdd    = max_drawdown(equity_from_returns(bh_ret))

    # FTMO Phase-1 (context only — swing trades hold overnight; FTMO rules may not suit)
    d0, d1 = daily_index[0], daily_index[-1]
    for r in results:
        r["ftmo"] = (rolling_pass_rate(r["trades"], d0, d1, phase=1, max_days=60)
                     if r["n"] else dict(pass_rate=float("nan")))

    # ── Report ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 100)
    print("  THREE SWING GOLD STRATEGIES  |  XAUUSD spot M1 -> H4/Daily/Weekly  |  2018-2025 UTC")
    print("  Costs: REAL spread + $0.07/oz commission + news slippage. 1% risk/trade. Multi-day holds.")
    print(f"  Buy&Hold gold benchmark (daily, full period): Sharpe {bh_sharpe:.2f}  PF {bh_pf:.2f}  MaxDD {bh_mdd*100:.1f}%")
    print("=" * 100)
    print(f"  {'Strategy':<18} {'Trades':>6} {'grPF':>5} {'netPF':>6} {'Sharpe':>7} {'DSR':>5} "
          f"{'MaxDD':>7} {'medR$':>6} {'costR%':>7} {'vsB&H':>6}")
    print("  " + "-" * 96)
    for r in results:
        if r["n"] == 0:
            print(f"  {r['name']:<18} {0:>6}  (no trades)")
            continue
        beats = "Y" if r["sharpe"] > bh_sharpe else "N"
        print(f"  {r['name']:<18} {r['n']:>6} {r['gross_pf']:>5.2f} {r['pf']:>6.2f} "
              f"{r['sharpe']:>7.2f} {r['dsr']:>5.2f} {r['mdd']*100:>6.1f} "
              f"{r['risk_med']:>6.1f} {r['cost_R_mean']*100:>6.2f} {beats:>6}")
    print("=" * 100)
    print("  medR$ = median stop distance ($/oz) = 1R.  costR% = mean cost as % of risk.")
    print("  vsB&H = does net Sharpe beat buy-and-hold gold?  (Y/N)")

    for r in results:
        print(f"\n[{r['name']}]")
        if r["n"] == 0:
            print("  No trades — setup never triggered under stated rules."); continue
        print(f"  Trades {r['n']} (target {r['n_targets']}/stop {r['n_stops']}/time {r['n_time']}) "
              f"| median 1R = {r['risk_med']:.1f} $/oz | Sortino {r['sortino']:.2f} | guard {r['guard'][:4]}")
        print(f"  Per-trade R: gross {r['gross_R_mean']:+.3f} - cost {r['cost_R_mean']:.3f} "
              f"({r['cost_R_mean']*100:.1f}% of risk) = net {r['net_R_mean']:+.3f}  "
              f"(gross PF {r['gross_pf']:.2f} -> net PF {r['pf']:.2f})")
        print(f"  vs Buy&Hold: strat Sharpe {r['sharpe']:.2f} / PF {r['pf']:.2f}  "
              f"vs  B&H Sharpe {bh_sharpe:.2f} / PF {bh_pf:.2f}  -> "
              f"{'BEATS' if r['sharpe'] > bh_sharpe else 'LOSES TO'} buy-and-hold")
        print(f"  (context) FTMO P1 pass rate: {r['ftmo']['pass_rate']*100:.1f}% "
              f"— swing holds overnight, so FTMO overnight rules may not suit.")

        survives = r["net_R_mean"] > 0 and r["pf"] > 1.0
        cost_small = r["cost_R_mean"] < 0.05
        cost_note = ("cost is now SMALL vs risk" if cost_small
                     else "cost still material vs risk")
        if survives:
            v = f"HAS an edge that survives costs ({cost_note})"
        elif r["gross_R_mean"] > 0:
            v = f"gross edge exists but net<=0 ({cost_note}) — kill"
        else:
            v = f"NO edge even gross ({cost_note}) — kill"
        print(f"  VERDICT: {v}.")

    # research_log rows
    print("\n--- research_log.md rows ---")
    for r in results:
        if r["n"] == 0:
            print(f"| 2026-07-18 | {r['name']} (swing) | XAUUSD | H4/D | 1% risk, no tuning | 0 trades | never triggered |")
            continue
        print(f"| 2026-07-18 | {r['name']} (swing) | XAUUSD | H4/D | 1% risk, fixed R, no tuning | "
              f"grPF {r['gross_pf']:.2f}, netPF {r['pf']:.2f}, Sharpe {r['sharpe']:.2f}, DSR {r['dsr']:.2f}, "
              f"MaxDD {r['mdd']*100:.1f}%, {r['n']} trades | medR {r['risk_med']:.0f}$/oz, costR {r['cost_R_mean']*100:.1f}%, "
              f"{'beats' if r['sharpe']>bh_sharpe else 'loses to'} B&H(SR {bh_sharpe:.2f}); guard {r['guard'][:4]} |")

    return results


if __name__ == "__main__":
    main()
