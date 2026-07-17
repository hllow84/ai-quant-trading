#!/usr/bin/env python3
"""
run_ftmo.py — Build, cost, score, and FTMO-test three gold strategies.

Pipeline per strategy:
  signals -> simulate_trades (real spread + commission + news slippage)
          -> de_overlap (one position at a time)
          -> look-ahead guard on the held position (must pass)
          -> daily returns -> Sharpe (252), Sortino, PF, win rate, max DD
          -> Deflated Sharpe with n_configs = 3 (haircut for testing three)
          -> rolling FTMO Phase-1 pass rate (monthly starts, 60-day window)

No parameter tuning: defaults are fixed in strategies/ftmo_gold.py, tested once.
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
from strategies.ftmo_gold import (
    build_trend_continuation, build_breakout_retest, build_mean_reversion,
)

BARS_PER_YEAR = 252


def score_strategy(name, candidates, m1_mid, m15, daily_index):
    """Simulate + cost + guard + metrics for one strategy. Returns a result dict."""
    raw = simulate_trades(m1_mid, candidates)
    trades = de_overlap(raw)

    if trades.empty:
        return dict(name=name, trades=trades, n=0, daily_ret=pd.Series(dtype=float),
                    guard="N/A (no trades)", sharpe=float("nan"), sortino=float("nan"),
                    pf=float("nan"), win=float("nan"), mdd=float("nan"),
                    net_R_sum=0.0, skew=0.0, ekurt=0.0)

    # Look-ahead guard on the HELD position vs M15 returns
    pos = build_position_series(trades, m15.index)
    m15_ret = m15["mid_close"].pct_change()
    try:
        guard_look_ahead(pos, m15_ret, threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL: {exc}"

    daily_ret = build_daily_returns(trades, daily_index)
    equity    = equity_from_returns(daily_ret)

    return dict(
        name=name, trades=trades, n=len(trades), daily_ret=daily_ret, equity=equity,
        guard=guard,
        sharpe=sharpe(daily_ret, BARS_PER_YEAR),
        sortino=sortino(daily_ret, BARS_PER_YEAR),
        pf=profit_factor(trades["net_R"]),          # PF on per-trade R (cost-inclusive)
        gross_pf=profit_factor(trades["gross_R"]),  # PF BEFORE costs — is there a raw edge?
        gross_R_mean=float(trades["gross_R"].mean()),
        cost_R_mean=float(trades["cost_R"].mean()),
        net_R_mean=float(trades["net_R"].mean()),
        win=hit_rate(trades["net_R"]),
        mdd=max_drawdown(equity),
        net_R_sum=float(trades["net_R"].sum()),
        skew=float(daily_ret.skew()),
        ekurt=float(daily_ret.kurtosis()),
        n_targets=int((trades["reason"] == "target").sum()),
        n_stops=int((trades["reason"] == "stop").sum()),
        n_time=int((trades["reason"] == "time").sum()),
    )


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("Loading M1 mid data ...", flush=True)
    m1_mid = load_m1_mid()
    print(f"  M1 bars: {len(m1_mid):,}  ({m1_mid.index[0].date()} -> {m1_mid.index[-1].date()})",
          flush=True)

    print("Resampling M15 / H1 / daily ...", flush=True)
    m15   = resample_mid(m1_mid, "15min")
    h1    = resample_mid(m1_mid, "1h")
    daily = load_daily_spot()
    daily_index = daily.index

    print("Building candidate trades ...", flush=True)
    cand_a = build_trend_continuation(m15, h1)
    cand_b = build_breakout_retest(m15)
    cand_c = build_mean_reversion(m15, daily)
    print(f"  A trend-continuation : {len(cand_a):,} candidates")
    print(f"  B breakout-retest    : {len(cand_b):,} candidates")
    print(f"  C mean-reversion     : {len(cand_c):,} candidates")

    print("Simulating + scoring ...", flush=True)
    res_a = score_strategy("A trend-continuation", cand_a, m1_mid, m15, daily_index)
    res_b = score_strategy("B breakout-retest",    cand_b, m1_mid, m15, daily_index)
    res_c = score_strategy("C mean-reversion",     cand_c, m1_mid, m15, daily_index)
    results = [res_a, res_b, res_c]

    # Deflated Sharpe with n_configs = 3 (haircut for testing three strategies)
    sr_trials = [r["sharpe"] for r in results]
    sr_trials = [s if not np.isnan(s) else 0.0 for s in sr_trials]
    for r in results:
        if r["n"] == 0 or np.isnan(r["sharpe"]):
            r["dsr"] = float("nan")
            continue
        dsr, _ = deflated_sharpe_ratio(
            sr_best=r["sharpe"], sr_trials=sr_trials, n_obs=len(r["daily_ret"]),
            skewness=r["skew"], excess_kurtosis=r["ekurt"],
        )
        r["dsr"] = dsr

    # FTMO rolling pass rate (Phase 1, +10%, 60-day window, monthly starts)
    d_start, d_end = daily_index[0], daily_index[-1]
    print("Simulating rolling FTMO challenges ...", flush=True)
    for r in results:
        if r["n"] == 0:
            r["ftmo"] = dict(n_challenges=0, n_pass=0, pass_rate=float("nan"),
                             reasons={}, median_days_to_pass=float("nan"), phase=1)
        else:
            r["ftmo"] = rolling_pass_rate(r["trades"], d_start, d_end, phase=1, max_days=60)

    # ── Report ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 96)
    print("  THREE FTMO-SHAPED GOLD STRATEGIES  |  XAUUSD spot M1 -> M15/H1  |  2018-2025 UTC")
    print("  Costs: REAL spread + $7/lot ($0.07/oz) commission + news-hour slippage. 1% risk/trade.")
    print("=" * 96)
    hdr = (f"  {'Strategy':<22} {'Trades':>7} {'grPF':>6} {'netPF':>6} {'Win%':>6} {'Sharpe':>7} "
           f"{'DSR':>6} {'MaxDD':>7} {'FTMO%':>7} {'Guard':>6}")
    print(hdr)
    print("  " + "-" * 100)
    for r in results:
        if r["n"] == 0:
            print(f"  {r['name']:<22} {0:>7} {'--':>6} {'--':>6} {'--':>6} {'--':>7} {'--':>6} "
                  f"{'--':>7} {'--':>7} {r['guard'][:6]:>6}")
            continue
        print(f"  {r['name']:<22} {r['n']:>7} {r['gross_pf']:>6.2f} {r['pf']:>6.2f} "
              f"{r['win']*100:>5.1f} {r['sharpe']:>7.2f} {r['dsr']:>6.2f} {r['mdd']*100:>6.1f} "
              f"{r['ftmo']['pass_rate']*100:>6.1f} {r['guard'][:6]:>6}")
    print("=" * 96)
    print("  grPF = gross profit factor (before costs); netPF = after real costs.")
    print("  NOTE: all three net Sharpes are negative, so DSR is moot here — it merely")
    print("        ranks the least-bad of three losers, NOT statistical significance.")

    # Per-strategy detail + honest verdict
    for r in results:
        print(f"\n[{r['name']}]")
        if r["n"] == 0:
            print("  No trades generated — setup never triggered under stated rules.")
            continue
        print(f"  Trades {r['n']}  (target {r['n_targets']} / stop {r['n_stops']} / time {r['n_time']})  "
              f"| Sortino {r['sortino']:.2f}")
        print(f"  Per-trade R: gross {r['gross_R_mean']:+.3f}  - cost {r['cost_R_mean']:.3f}  "
              f"= net {r['net_R_mean']:+.3f}   (gross PF {r['gross_pf']:.3f} -> net PF {r['pf']:.3f})")
        f = r["ftmo"]
        print(f"  FTMO Phase-1: {f['n_pass']}/{f['n_challenges']} passed "
              f"({f['pass_rate']*100:.1f}%)  reasons={f['reasons']}")

        has_gross_edge = r["gross_R_mean"] > 0
        survives_costs = r["net_R_mean"] > 0
        if survives_costs:
            edge_txt = "HAS an edge that survives costs"
        elif has_gross_edge:
            edge_txt = ("has a TINY gross edge but costs destroy it "
                        f"(cost {r['cost_R_mean']:.2f}R/trade > gross {r['gross_R_mean']:.2f}R) — kill")
        else:
            edge_txt = "NO edge even before costs — kill"
        ftmo_txt = (f"clears FTMO ~{f['pass_rate']*100:.0f}% of starts"
                    if f["pass_rate"] >= 0.30 else
                    f"fails FTMO almost always ({f['pass_rate']*100:.0f}% pass)")
        print(f"  VERDICT: {edge_txt}; {ftmo_txt}.")

    # Emit a research_log-ready row block
    print("\n--- research_log.md rows ---")
    for r in results:
        if r["n"] == 0:
            print(f"| 2026-07-18 | {r['name']} | XAUUSD | M15 | 1% risk, no tuning | "
                  f"0 trades | setup never triggered |")
            continue
        print(f"| 2026-07-18 | {r['name']} | XAUUSD | M15 | 1% risk, fixed R, no tuning | "
              f"PF {r['pf']:.2f}, Sharpe {r['sharpe']:.2f}, DSR {r['dsr']:.2f}, "
              f"MaxDD {r['mdd']*100:.1f}%, {r['n']} trades | "
              f"FTMO P1 pass {r['ftmo']['pass_rate']*100:.0f}%; guard {r['guard'][:4]} |")

    return results


if __name__ == "__main__":
    main()
