"""
ftmo_challenge_daily.py — FTMO Challenge ruleset simulator operating on a
DAILY RETURN series (fraction of equity per calendar day) instead of a
raw per-trade stream. This is the natural fit for a COMBINED, dynamically-
weighted book (multiple legs summed into one daily portfolio return),
where "one trade" no longer means one thing across legs.

Extends research/ftmo_rules.py's per-trade `simulate_challenge` /
`rolling_pass_rate` with the same modelled rules, PLUS the Best Day
(consistency) rule required by this project's standing rule 6
(CLAUDE.md) which the original per-trade engine does not implement.

Rules modelled (stated assumptions, per research/ftmo_rules.py's own
disclaimer style — FTMO variants differ):
  - Max daily loss  : 5% of INITIAL balance, measured per UTC calendar day.
  - Max total loss  : 10% of INITIAL balance (static floor at 0.90 equity).
  - Profit target   : Phase 1 = +10%, Phase 2 = +5%.
  - Min trading days: 4 distinct days with a nonzero daily return.
  - Challenge window: `max_days` calendar days of runway (default 60).
  - Best Day (consistency): no single day's profit may exceed a stated
    fraction of TOTAL profit earned by the pass point. FTMO's own public
    rule text for this varies by account type and has changed over time;
    **30% is used here as the assumed threshold, stated explicitly** (the
    same "assumptions — FTMO variants differ" caveat as the rest of this
    module). Both the RAW pass/fail (ignoring consistency) and the
    CONSISTENCY-ADJUSTED pass/fail are reported side by side, never only
    one, so the assumption's impact is visible rather than baked in
    silently.
"""
from __future__ import annotations

import pandas as pd


def simulate_challenge_daily(
    daily_ret: pd.Series,
    start: pd.Timestamp,
    target: float = 0.10,
    daily_loss: float = 0.05,
    total_dd: float = 0.10,
    min_days: int = 4,
    max_days: int = 60,
    best_day_cap: float = 0.30,
) -> dict:
    """Run one challenge from `start` on a daily-return series (fraction of
    equity per day, 0.0 on no-trade days). Returns a dict with both the RAW
    (ignoring consistency) and CONSISTENCY-ADJUSTED pass/fail."""
    end_window = start + pd.Timedelta(days=max_days)
    window = daily_ret[(daily_ret.index >= start) & (daily_ret.index <= end_window)]
    window = window.sort_index()

    equity = 1.0
    trading_days: set = set()
    day_pnls: list[float] = []  # realized daily P&L fractions up to the pass point

    for day, r in window.items():
        if r != 0.0:
            trading_days.add(day)
            day_pnls.append(r)
        equity *= (1.0 + r)
        days_used = (day - start).days

        if r <= -daily_loss:
            return dict(passed_raw=False, passed_consistency=False, reason="daily_loss",
                        days_used=days_used, trading_days=len(trading_days), end_equity=equity)
        if equity <= 1.0 - total_dd:
            return dict(passed_raw=False, passed_consistency=False, reason="total_dd",
                        days_used=days_used, trading_days=len(trading_days), end_equity=equity)
        if equity >= 1.0 + target and len(trading_days) >= min_days:
            total_profit = sum(p for p in day_pnls if p > 0)
            best_day = max(day_pnls) if day_pnls else 0.0
            consistency_ok = (total_profit <= 0) or (best_day <= best_day_cap * total_profit)
            return dict(
                passed_raw=True,
                passed_consistency=bool(consistency_ok),
                reason="target" if consistency_ok else "best_day_consistency",
                days_used=days_used, trading_days=len(trading_days), end_equity=equity,
                best_day_share=(best_day / total_profit) if total_profit > 0 else float("nan"),
            )

    return dict(passed_raw=False, passed_consistency=False, reason="no_target",
                days_used=max_days, trading_days=len(trading_days), end_equity=equity)


def rolling_pass_rate_daily(
    daily_ret: pd.Series,
    data_start: pd.Timestamp,
    data_end: pd.Timestamp,
    phase: int = 1,
    max_days: int = 60,
    best_day_cap: float = 0.30,
) -> dict:
    """Start a challenge on the 1st of every month with a full max_days runway
    before data_end. Returns raw and consistency-adjusted pass rates."""
    target = 0.10 if phase == 1 else 0.05
    starts = pd.date_range(
        start=pd.Timestamp(data_start.year, data_start.month, 1, tz=data_start.tz),
        end=data_end, freq="MS",
    )
    results = []
    for s in starts:
        if s < data_start or s + pd.Timedelta(days=max_days) > data_end:
            continue
        results.append(simulate_challenge_daily(daily_ret, s, target=target,
                                                  max_days=max_days, best_day_cap=best_day_cap))

    n = len(results)
    n_pass_raw = sum(r["passed_raw"] for r in results)
    n_pass_consistency = sum(r["passed_consistency"] for r in results)
    reasons: dict = {}
    for r in results:
        reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    pass_days = [r["days_used"] for r in results if r["passed_consistency"]]
    return dict(
        n_challenges=n,
        n_pass_raw=n_pass_raw,
        n_pass_consistency=n_pass_consistency,
        pass_rate_raw=(n_pass_raw / n) if n else float("nan"),
        pass_rate_consistency=(n_pass_consistency / n) if n else float("nan"),
        reasons=reasons,
        median_days_to_pass=(float(pd.Series(pass_days).median()) if pass_days else float("nan")),
        phase=phase,
    )
