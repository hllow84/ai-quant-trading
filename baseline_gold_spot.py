#!/usr/bin/env python3
"""
baseline_gold_spot.py — SMA-200 long-only baseline for XAUUSD on REAL SPOT data.

Supersedes `baseline_sma200.py`, which used yfinance GC=F (CME futures — banned:
no bid/ask spread) with a PROVISIONAL flat 4 bps cost. This version uses the real
Dukascopy XAUUSD M1 SPOT feed (bid + ask + per-bar spread, UTC), aggregated to
daily bars, and charges the ACTUAL spread crossed at each trade.

Design intent (unchanged):
  - Honest, un-tuned benchmark, not a strategy to optimize (n_configs = 1).
  - A mediocre/negative result is the expected, correct outcome.
  - All costs applied before any metric. Look-ahead guard enforced.

Cost model:
  Round-turn = cross the spread twice (buy at ask on entry, sell at bid on exit).
  bt_run charges turnover = |Δposition|: 1 unit on entry, 1 unit on exit.
  Per unit of turnover we cross HALF the round-turn spread relative to mid:
        spread_cost[t] = turnover[t] * (spread_close[t] / 2) / mid_close[t]
  This uses the real spread quoted at the daily close — the moment we transact.
  An optional flat slippage (bps per turnover unit) is added and reported
  separately, so the spread-only and spread+slippage figures are both visible.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_daily_spot
from research.backtest import run as bt_run, guard_look_ahead, LookAheadError
from research.metrics import (
    sharpe, sortino, max_drawdown, profit_factor, hit_rate,
    deflated_sharpe_ratio,
)

# ══════════════════════════════════════════════════════════════════════════════
# PARAMETERS
# ══════════════════════════════════════════════════════════════════════════════
SYMBOL         = "XAUUSD"
BARS_PER_YEAR  = 252            # daily trading days per year
SMA_WINDOW     = 200            # fixed — no grid, no selection bias
SLIPPAGE_BPS   = 0.5            # per unit turnover, on top of measured spread


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 66)
    print(f"  Baseline: SMA-{SMA_WINDOW} long-only  |  {SYMBOL} SPOT  |  Daily bars")
    print("=" * 66)

    # ── 1. Data (real spot, aggregated to daily) ────────────────────────────────
    print("\n[1] DATA")
    daily      = load_daily_spot()
    mid_close  = daily["mid_close"]
    spread_cl  = daily["spread_close"]

    print(f"  Source      : Dukascopy XAUUSD M1 SPOT (bid/ask + spread), UTC")
    print(f"  Aggregation : M1 -> daily (UTC calendar day)")
    print(f"  Daily bars  : {len(daily):,}")
    print(f"  Date range  : {daily.index[0].date()} -> {daily.index[-1].date()}")
    print(f"  Price (mid) : ${mid_close.min():,.2f} - ${mid_close.max():,.2f}")
    rt_bps = (spread_cl / mid_close) * 10_000
    print(f"  Spread@close: median {spread_cl.median():.3f}  mean {spread_cl.mean():.3f} "
          f"(price units)")
    print(f"  Round-turn  : median {rt_bps.median():.2f} bps  mean {rt_bps.mean():.2f} bps of mid")

    # ── 2. Signal ───────────────────────────────────────────────────────────────
    print(f"\n[2] SIGNAL  (fixed — no optimization)")
    sma = mid_close.rolling(SMA_WINDOW, min_periods=SMA_WINDOW).mean()
    signal = (mid_close > sma).astype(int)
    signal = signal.where(sma.notna(), other=0).rename("sma_signal")
    returns = mid_close.pct_change().rename("asset_return")

    print(f"  Rule      : long if mid_close > SMA(mid_close, {SMA_WINDOW})")
    print(f"  Lag       : 1 bar inside bt_run (position = signal.shift(1))")
    print(f"  Values    : {{0, 1}}  (long-only)")
    print(f"  n_configs : 1")

    # Align
    idx     = signal.index.intersection(returns.dropna().index)
    signal  = signal.loc[idx]
    returns = returns.loc[idx]
    mid_a   = mid_close.loc[idx]
    spr_a   = spread_cl.loc[idx]

    # ── 3. Look-ahead guard ─────────────────────────────────────────────────────
    print(f"\n[3] LOOK-AHEAD GUARD")
    try:
        guard_look_ahead(signal, returns, threshold=0.5)
        print("  PASS — |corr| with same/next-bar returns < 0.5")
    except LookAheadError as exc:
        print(f"  FAIL: {exc}")
        sys.exit(1)

    # ── 4. Backtest (gross via engine, real-spread cost applied on top) ─────────
    print(f"\n[4] BACKTEST  (direction=long)")
    gross = bt_run(signal, returns, fee_bps=0, slippage_bps=0, direction="long")
    position  = gross["position"]
    gross_ret = gross["gross_ret"]
    turnover  = gross["turnover"]

    # Real per-bar spread cost: half round-turn per unit turnover, at the close.
    half_spread_frac = (spr_a / 2) / mid_a          # fraction of mid, per side
    spread_cost = turnover * half_spread_frac
    slip_cost   = turnover * (SLIPPAGE_BPS / 10_000)

    net_ret     = gross_ret - spread_cost - slip_cost
    equity_net  = (1 + net_ret).cumprod()
    equity_gross = (1 + gross_ret).cumprod()

    # ── 5. Metrics ──────────────────────────────────────────────────────────────
    sr_gross = sharpe(gross_ret, BARS_PER_YEAR)
    sr_net   = sharpe(net_ret,   BARS_PER_YEAR)
    sr_sort  = sortino(net_ret,  BARS_PER_YEAR)
    mdd      = max_drawdown(equity_net)
    pf       = profit_factor(net_ret)
    hr       = hit_rate(net_ret)

    total_spread_drag = float(spread_cost.sum())
    total_slip_drag   = float(slip_cost.sum())
    entries     = int((position.diff() > 0).sum())
    pos_changes = int(position.diff().abs().gt(0).sum())

    try:
        dsr_prob, e_max_sr = deflated_sharpe_ratio(
            sr_best=sr_net, sr_trials=[sr_net], n_obs=len(net_ret),
            skewness=float(net_ret.skew()),
            excess_kurtosis=float(net_ret.kurtosis()),
        )
    except Exception:
        dsr_prob, e_max_sr = float("nan"), float("nan")

    # Total & annualized return for context
    total_ret_net   = float(equity_net.iloc[-1] - 1)
    total_ret_gross = float(equity_gross.iloc[-1] - 1)
    years = len(net_ret) / BARS_PER_YEAR
    cagr_net = (equity_net.iloc[-1]) ** (1 / years) - 1 if years > 0 else float("nan")

    # ── 6. Report ───────────────────────────────────────────────────────────────
    sep = "=" * 66
    print(f"\n{sep}")
    print(f"  RESULTS  |  {SYMBOL} SPOT  |  SMA-{SMA_WINDOW}  |  "
          f"{daily.index[0].date()} - {daily.index[-1].date()}")
    print(sep)
    print(f"  {'Metric':<38}  {'Value':>14}")
    print(f"  {'-'*38}  {'-'*14}")
    print(f"  {'Gross Sharpe  (no costs)':<38}  {sr_gross:>14.3f}")
    print(f"  {'Net Sharpe    (real spread + slip)':<38}  {sr_net:>14.3f}")
    print(f"  {'Deflated Sharpe prob  (n=1)':<38}  {dsr_prob:>14.4f}  *")
    print(f"  {'Sortino ratio':<38}  {sr_sort:>14.3f}")
    print(f"  {'Max drawdown (net)':<38}  {mdd:>13.1%}")
    print(f"  {'Profit factor':<38}  {pf:>14.3f}")
    print(f"  {'Win rate (active bars)':<38}  {hr:>13.1%}")
    print(f"  {'Total return  (net)':<38}  {total_ret_net:>13.1%}")
    print(f"  {'Total return  (gross)':<38}  {total_ret_gross:>13.1%}")
    print(f"  {'CAGR (net)':<38}  {cagr_net:>13.1%}")
    print(f"  {'Trade entries':<38}  {entries:>14,}")
    print(f"  {'Position changes (entries+exits)':<38}  {pos_changes:>14,}")
    print(f"  {'Spread drag  (total, fraction)':<38}  {total_spread_drag:>14.5f}")
    print(f"  {'Slippage drag (total, fraction)':<38}  {total_slip_drag:>14.5f}")
    print(f"  {'Annualisation  (bars/yr)':<38}  {BARS_PER_YEAR:>14,}")
    print(sep)
    print("  * DSR n=1: no parameter selection -> no deflation needed (trivial).")
    print(sep)

    if sr_net > 0.1:
        verdict = "PROFITABLE after costs"
    elif sr_net > -0.1:
        verdict = "BREAK-EVEN after costs"
    else:
        verdict = "LOSS after costs"

    print(f"\n  ONE LINE: {verdict}  "
          f"(Gross SR={sr_gross:.3f} -> Net SR={sr_net:.3f}; "
          f"spread+slip drag={sr_gross - sr_net:.3f} SR units)")

    # ── 7. BENCHMARK: buy-and-hold gold (the real bar to clear) ─────────────────
    # 2018-2025 is a secular gold bull. A long-only SMA baseline is mostly long
    # beta; the honest question is whether it beats simply holding gold. SMA-200
    # can only justify itself by REDUCING RISK (drawdown), not by out-returning.
    bh_ret    = returns.copy()                    # always long, no timing
    bh_equity = (1 + bh_ret).cumprod()
    bh_sr     = sharpe(bh_ret, BARS_PER_YEAR)
    bh_mdd    = max_drawdown(bh_equity)
    bh_total  = float(bh_equity.iloc[-1] - 1)
    bh_cagr   = (bh_equity.iloc[-1]) ** (1 / years) - 1 if years > 0 else float("nan")
    time_in_mkt = float((position != 0).mean())

    print(f"\n{sep}")
    print(f"  BENCHMARK vs BUY-AND-HOLD GOLD  (is the timing worth anything?)")
    print(sep)
    print(f"  {'Metric':<26}  {'SMA-200':>12}  {'Buy&Hold':>12}")
    print(f"  {'-'*26}  {'-'*12}  {'-'*12}")
    print(f"  {'Net Sharpe':<26}  {sr_net:>12.3f}  {bh_sr:>12.3f}")
    print(f"  {'Max drawdown':<26}  {mdd:>11.1%}  {bh_mdd:>11.1%}")
    print(f"  {'CAGR':<26}  {cagr_net:>11.1%}  {bh_cagr:>11.1%}")
    print(f"  {'Total return':<26}  {total_ret_net:>11.1%}  {bh_total:>11.1%}")
    print(f"  {'Time in market':<26}  {time_in_mkt:>11.1%}  {1.0:>11.1%}")
    print(sep)

    if sr_net > bh_sr + 0.10:
        bench_verdict = ("SMA-200 ADDS risk-adjusted value over buy-and-hold "
                         f"(+{sr_net - bh_sr:.2f} Sharpe).")
    elif sr_net > bh_sr - 0.10:
        bench_verdict = ("SMA-200 ~= buy-and-hold on Sharpe; its only edge is "
                         f"lower drawdown ({mdd:.0%} vs {bh_mdd:.0%}) at "
                         f"{time_in_mkt:.0%} exposure.")
    else:
        bench_verdict = ("SMA-200 UNDERPERFORMS buy-and-hold risk-adjusted "
                         f"({sr_net:.2f} vs {bh_sr:.2f}) — the timing destroys value.")
    print(f"\n  VERDICT: {bench_verdict}")
    print(f"  NOTE: 2018-2025 is a secular gold bull. Both results are dominated by")
    print(f"        long-gold beta, NOT alpha. This is a benchmark, not a strategy.")
    print()


if __name__ == "__main__":
    main()
