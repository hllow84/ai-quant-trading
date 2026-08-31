#!/usr/bin/env python3
"""
monitor.py -- decay detection. Run monthly, after each rebalance (or any
time). Reads live/logs/equity_log.csv (written every rebalance.py run),
builds a monthly live-return series, computes a trailing Sharpe, and
compares against:
  (a) the audited backtest's expected Sharpe range (0.51-0.64, sec 12.1), and
  (b) SPY buy-and-hold over the same live period (pulled fresh via yfinance).

STOP-LIVE RULE (stated plainly, not just implied by numbers on a screen):
  Stop trading this strategy live if BOTH of the following hold for
  STOP_RULE_CONSECUTIVE_RUNS (2) consecutive monthly monitor runs:
    1. trailing 12-month live Sharpe < 0, AND
    2. trailing 12-month live CAGR underperforms SPY buy-and-hold's CAGR
       over the same window by more than STOP_RULE_UNDERPERFORM_SPY_CAGR_PP
       (10) percentage points.
  This means live behavior looks nothing like ANY audited perturbation
  variant (all of which stayed solidly positive-Sharpe and beat SPY
  risk-adjusted, sec 12.1/12.3) -- a single bad month is noise; two straight
  months of both a negative Sharpe AND a double-digit CAGR gap behind the
  benchmark it exists to beat is not.
  The kill switch (15% drawdown from peak) is a separate, harder, automatic
  halt that doesn't wait for this monthly check.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import numpy as np
import pandas as pd
import yfinance as yf

from live import config, state as state_mod
from live.logging_utils import EQUITY_LOG


def monthly_equity_series() -> pd.Series:
    if not EQUITY_LOG.exists():
        return pd.Series(dtype=float)
    df = pd.read_csv(EQUITY_LOG, parse_dates=["timestamp"])
    df = df.dropna(subset=["equity"]).sort_values("timestamp")
    df["month"] = df["timestamp"].dt.to_period("M")
    monthly = df.groupby("month")["equity"].last()
    return monthly


def sharpe_of(monthly_returns: pd.Series) -> float:
    if len(monthly_returns) < 2 or monthly_returns.std() == 0:
        return float("nan")
    return float(monthly_returns.mean() / monthly_returns.std() * np.sqrt(12))


def cagr_of(monthly_returns: pd.Series) -> float:
    if len(monthly_returns) == 0:
        return float("nan")
    total_return = float((1 + monthly_returns).prod() - 1)
    years = len(monthly_returns) / 12.0
    if years <= 0:
        return float("nan")
    return (1 + total_return) ** (1 / years) - 1


def spy_monthly_returns(start_period: pd.Period, end_period: pd.Period) -> pd.Series:
    start = start_period.to_timestamp("D")
    end = (end_period + 1).to_timestamp("D")
    df = yf.download("SPY", start=start, end=end, interval="1d",
                      auto_adjust=True, actions=False, progress=False, threads=False)
    if df is None or df.empty:
        return pd.Series(dtype=float)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    close = df["Close"]
    close.index = pd.PeriodIndex(close.index, freq="M")
    monthly_close = close.groupby(level=0).last()
    return monthly_close.pct_change().dropna()


def main() -> int:
    monthly_equity = monthly_equity_series()
    n_months = max(len(monthly_equity) - 1, 0)

    print("=== momentum rotation live-performance monitor ===")
    print(f"Equity log has {len(monthly_equity)} monthly snapshot(s) "
          f"({n_months} return observation(s)).")

    if n_months < config.MONITOR_MIN_MONTHS_FOR_SHARPE:
        print(
            f"Fewer than {config.MONITOR_MIN_MONTHS_FOR_SHARPE} monthly returns logged -- "
            f"too early to compute a meaningful Sharpe. Run rebalance.py monthly and "
            f"come back."
        )
        return 0

    monthly_returns = monthly_equity.pct_change().dropna()
    trailing = monthly_returns.tail(12)
    live_sharpe = sharpe_of(trailing)
    live_cagr = cagr_of(trailing)

    spy_ret = spy_monthly_returns(trailing.index[0], trailing.index[-1])
    spy_ret = spy_ret.reindex(trailing.index)
    spy_sharpe = sharpe_of(spy_ret.dropna())
    spy_cagr = cagr_of(spy_ret.dropna())

    partial = n_months < config.MONITOR_MIN_MONTHS_FOR_FULL_COMPARE
    label = "PARTIAL (< 12 months, treat as indicative only)" if partial else "FULL 12-month window"

    print(f"\nTrailing window: {trailing.index[0]} .. {trailing.index[-1]}  [{label}]")
    print(f"Live   Sharpe: {live_sharpe:.3f}   CAGR: {live_cagr:.2%}")
    print(f"SPY    Sharpe: {spy_sharpe:.3f}   CAGR: {spy_cagr:.2%}")
    print(f"Backtest audited Sharpe range: {config.BACKTEST_SHARPE_LOW:.2f}-{config.BACKTEST_SHARPE_HIGH:.2f}")

    if not (config.MONITOR_SHARPE_WIDE_LOW <= live_sharpe <= config.MONITOR_SHARPE_WIDE_HIGH):
        print(
            f"\n⚠ SOFT FLAG: live Sharpe {live_sharpe:.3f} is outside the wide tolerance "
            f"band [{config.MONITOR_SHARPE_WIDE_LOW}, {config.MONITOR_SHARPE_WIDE_HIGH}] "
            f"around the audited range. Not an automatic stop -- investigate."
        )

    cagr_gap_pp = (live_cagr - spy_cagr) * 100.0
    bad_this_run = (live_sharpe < 0.0) and (cagr_gap_pp < -config.STOP_RULE_UNDERPERFORM_SPY_CAGR_PP)

    st = state_mod.load_state()
    if bad_this_run:
        st["consecutive_bad_monitor_runs"] += 1
    else:
        st["consecutive_bad_monitor_runs"] = 0
    state_mod.save_state(st)

    print(f"\nCAGR gap vs SPY: {cagr_gap_pp:+.2f}pp   "
          f"Bad-run this check: {bad_this_run}   "
          f"Consecutive bad runs: {st['consecutive_bad_monitor_runs']}")

    if st["consecutive_bad_monitor_runs"] >= config.STOP_RULE_CONSECUTIVE_RUNS:
        print(
            "\n" + "#" * 70 +
            f"\n# STOP-LIVE RULE TRIGGERED: {st['consecutive_bad_monitor_runs']} consecutive "
            f"monitor runs with\n"
            f"# negative trailing Sharpe AND >{config.STOP_RULE_UNDERPERFORM_SPY_CAGR_PP:.0f}pp "
            f"CAGR underperformance vs SPY.\n"
            f"# Live behavior no longer resembles any audited perturbation variant.\n"
            f"# RECOMMENDATION: halt new rebalances and review before continuing.\n" +
            "#" * 70
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
