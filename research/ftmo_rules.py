"""
ftmo_rules.py — Simulate the FTMO Challenge ruleset on a strategy's trade stream.

Rules modelled (stated assumptions — FTMO variants differ):
  - Max daily loss  : 5% of INITIAL balance, measured per UTC day (static denom).
  - Max total loss  : 10% of INITIAL balance (STATIC floor at 0.90 equity).
  - Profit target   : Phase 1 = +10%, Phase 2 = +5%.
  - Min trading days: 4 distinct days with >=1 closed trade (historical FTMO).
  - Challenge window: `max_days` calendar days of runway (default 60). If the
    target is not reached within the window without a breach -> NOT PASSED.

Rolling evaluation: start a fresh challenge on the 1st of each month; report the
share that would have PASSED Phase 1. This accounts for start-date luck.
"""

from __future__ import annotations

import pandas as pd


def simulate_challenge(
    trades_df: pd.DataFrame,
    start: pd.Timestamp,
    target: float = 0.10,
    daily_loss: float = 0.05,
    total_dd: float = 0.10,
    min_days: int = 4,
    max_days: int = 60,
) -> dict:
    """Run one challenge from `start`. Returns dict(passed, reason, days_used, trading_days, end_equity)."""
    end_window = start + pd.Timedelta(days=max_days)
    sub = trades_df[(trades_df["entry_time"] >= start) & (trades_df["exit_time"] <= end_window)]
    sub = sub.sort_values("exit_time")

    equity = 1.0
    day_pnl: dict = {}
    trading_days: set = set()

    for _, r in sub.iterrows():
        day = r["exit_time"].normalize()
        day_pnl[day] = day_pnl.get(day, 0.0) + r["ret_frac"]
        equity *= (1.0 + r["ret_frac"])
        trading_days.add(day)
        days_used = (r["exit_time"] - start).days

        if day_pnl[day] <= -daily_loss:
            return dict(passed=False, reason="daily_loss", days_used=days_used,
                        trading_days=len(trading_days), end_equity=equity)
        if equity <= 1.0 - total_dd:
            return dict(passed=False, reason="total_dd", days_used=days_used,
                        trading_days=len(trading_days), end_equity=equity)
        if equity >= 1.0 + target and len(trading_days) >= min_days:
            return dict(passed=True, reason="target", days_used=days_used,
                        trading_days=len(trading_days), end_equity=equity)

    return dict(passed=False, reason="no_target", days_used=max_days,
                trading_days=len(trading_days), end_equity=equity)


def rolling_pass_rate(
    trades_df: pd.DataFrame,
    data_start: pd.Timestamp,
    data_end: pd.Timestamp,
    phase: int = 1,
    max_days: int = 60,
) -> dict:
    """
    Start a challenge on the 1st of every month for which a full `max_days` of
    runway exists before data_end. Return pass count / rate and pass diagnostics.
    """
    target = 0.10 if phase == 1 else 0.05
    starts = pd.date_range(
        start=pd.Timestamp(data_start.year, data_start.month, 1, tz="UTC"),
        end=data_end, freq="MS", tz=None if data_start.tz is None else "UTC",
    )
    results = []
    for s in starts:
        if s < data_start or s + pd.Timedelta(days=max_days) > data_end:
            continue
        results.append(simulate_challenge(trades_df, s, target=target, max_days=max_days))

    n = len(results)
    n_pass = sum(r["passed"] for r in results)
    reasons: dict = {}
    for r in results:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    pass_days = [r["days_used"] for r in results if r["passed"]]
    return dict(
        n_challenges=n,
        n_pass=n_pass,
        pass_rate=(n_pass / n) if n else float("nan"),
        reasons=reasons,
        median_days_to_pass=(float(pd.Series(pass_days).median()) if pass_days else float("nan")),
        phase=phase,
    )
