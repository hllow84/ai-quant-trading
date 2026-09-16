"""
ftmo_challenge_daily.py — FTMO Challenge ruleset simulator operating on a
DAILY RETURN series (fraction of equity per calendar day) instead of a
raw per-trade stream. This is the natural fit for a COMBINED, dynamically-
weighted book (multiple legs summed into one daily portfolio return),
where "one trade" no longer means one thing across legs.

Extends research/ftmo_rules.py's per-trade `simulate_challenge` /
`rolling_pass_rate` with the same modelled rules.

**CORRECTION (2026-09-16, verified live against ftmo.com's own
"Trading Objectives" page and cross-checked against two independent
third-party rule summaries): the 2-Step Challenge/Verification ruleset
this module models (5% daily loss / 10% total loss / +10% Phase 1 /
+5% Phase 2 / 4 min trading days — the exact numbers below) has NO
Best Day or consistency rule of any kind, in either phase or on the
funded account.** An earlier version of this module added a 30%-
threshold Best Day check as a hard, account-terminating filter — that
was wrong on three separate counts, not just an "assumption that
varies by account type": (1) the 2-Step account has no such rule at
all, confirmed directly against FTMO's published Trading Objectives;
(2) FTMO's Best Day rule, where it DOES exist, applies ONLY to the
1-Step account/Challenge, at a 50% threshold, not 30%; (3) even there
it is explicitly a SOFT, non-breach "payout gate" (must keep trading
until compliant) — never an account termination, which is how it was
being applied here. The Best Day machinery below is KEPT (as
`best_day_cap`, default `None` = disabled) purely for anyone who later
wants to model the 1-Step account correctly (soft gate, 50%, no
termination) — it must never again be used to fail/terminate a 2-Step
simulation. §58-§61's "consistency-adjusted" figures computed against
the 2-Step ruleset were WRONG and are superseded by §62's corrected
numbers using `passed_raw` (which never applied this filter and was
therefore always the historically correct field for the 2-Step model).

Rules modelled for the 2-Step Challenge/Verification, verified live
against ftmo.com/en/trading-objectives/ on 2026-09-16:
  - Max daily loss  : 5% of INITIAL balance, measured per UTC calendar day,
    recalculated at 00:00 CE(S)T (a daily reset, NOT trailing).
  - Max total loss  : 10% of INITIAL balance, a STATIC floor (NOT trailing
    — confirmed against FTMO's own page, which explicitly distinguishes
    this from the 1-Step account's trailing max-loss rule).
  - Profit target   : Phase 1 (Challenge) = +10%, Phase 2 (Verification) = +5%.
  - Min trading days: 4 distinct days with at least one closed position,
    required in BOTH phases.
  - Challenge window: `max_days` calendar days of runway (default 60,
    FTMO's own standard time limit for the 2-Step product as of this
    writing — always re-verify if account type or FTMO's own published
    terms change).
  - Best Day / consistency: NONE for the 2-Step product (see correction
    above) — `best_day_cap=None` is the correct, default setting.
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
    best_day_cap: float | None = None,
) -> dict:
    """Run one challenge from `start` on a daily-return series (fraction of
    equity per day, 0.0 on no-trade days). `passed_raw` is the CORRECT
    pass/fail for FTMO's actual 2-Step ruleset (no consistency rule at
    all). `passed_consistency` only differs from it if `best_day_cap` is
    explicitly set to a number (for modelling the 1-Step account's real,
    SOFT 50% gate elsewhere — never treat it as a 2-Step breach)."""
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
            if best_day_cap is None:
                consistency_ok = True  # 2-Step ruleset: no such rule exists
            else:
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
    best_day_cap: float | None = None,
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
