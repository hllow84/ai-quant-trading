"""
ftmo_check_6x_reference.py — §59: adopts 6x standard risk-per-trade as
the REFERENCE sizing for FTMO deployment of §52's ORB gold + US30
breakout rolling-risk-parity book, per user direction following §58's
sensitivity sweep (6x was the "near-peak" pass-rate point identified
there: Phase 1 consistency-adjusted 32.1%, Phase 2 47.2%, before
daily-loss/total-DD breaches start dominating at 8x-10x).

This section goes beyond §58's independent per-phase pass rates and
computes the REALISTIC, CHAINED two-phase "actually gets funded"
probability: for each rolling monthly Challenge start, simulate Phase 1
(target +10%); if and only if it passes (including the consistency
rule), immediately start Phase 2 (target +5%) from the day Phase 1
ended, with the same 60-day runway and rule set. This is the number that
actually matters for someone deciding whether to attempt this — the
independent per-phase rates in §58 overstate the true "funded" chance
because they don't require the SAME window to clear both phases in
sequence.

Reuses both legs' trade engines and the §52 rolling weight scheme
UNCHANGED (research/ftmo_check_best_candidate.py's leg builders,
research/combined_book_risk_parity_rolling.py's rolling_weight_series) —
only a fixed 6x linear risk-multiplier is applied to the same daily
return series already computed in §52/§58 (Sharpe-invariant by
construction; only maxDD and challenge behavior change). Zero new
backtest trials.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.ftmo_check_best_candidate import gold_leg_daily_returns, us30_breakout_leg_daily_returns
from research.combined_book_risk_parity_rolling import rolling_weight_series
from research.ftmo_challenge_daily import simulate_challenge_daily, rolling_pass_rate_daily
from research.ftmo_engine import equity_from_returns
from research.metrics import max_drawdown, sharpe

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
MAX_DAYS = 60
BEST_DAY_CAP = None    # 2026-09-16 correction: verified against ftmo.com -- the 2-Step ruleset has NO Best Day/consistency rule at all
RISK_MULTIPLIER = 6.0   # adopted reference sizing, per user direction after §58


def two_phase_chain(daily_ret, data_start, data_end):
    """For each rolling monthly Challenge start, chain Phase 1 -> Phase 2
    and report the joint (fully-funded) pass rate, which the independent
    per-phase rates in §58 do not."""
    starts = pd.date_range(
        start=pd.Timestamp(data_start.year, data_start.month, 1, tz=data_start.tz),
        end=data_end, freq="MS",
    )
    rows = []
    for s in starts:
        if s < data_start or s + pd.Timedelta(days=MAX_DAYS) > data_end:
            continue
        p1 = simulate_challenge_daily(daily_ret, s, target=0.10, max_days=MAX_DAYS, best_day_cap=BEST_DAY_CAP)
        if not p1["passed_consistency"]:
            rows.append(dict(start=s, phase1_pass=False, phase2_pass=False, funded=False, reason=p1["reason"]))
            continue
        p2_start = s + pd.Timedelta(days=p1["days_used"])
        if p2_start + pd.Timedelta(days=MAX_DAYS) > data_end:
            rows.append(dict(start=s, phase1_pass=True, phase2_pass=None, funded=None, reason="phase2_no_runway"))
            continue
        p2 = simulate_challenge_daily(daily_ret, p2_start, target=0.05, max_days=MAX_DAYS, best_day_cap=BEST_DAY_CAP)
        rows.append(dict(start=s, phase1_pass=True, phase2_pass=p2["passed_consistency"],
                          funded=bool(p2["passed_consistency"]), reason=p2["reason"]))
    return pd.DataFrame(rows)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    gold = gold_leg_daily_returns()
    us30 = us30_breakout_leg_daily_returns()
    idx = gold.index.union(us30.index)
    gold_a = gold.reindex(idx, fill_value=0.0)
    us30_a = us30.reindex(idx, fill_value=0.0)
    w_roll = rolling_weight_series(gold_a, us30_a)
    rolling_rp = w_roll * gold_a + (1.0 - w_roll) * us30_a

    scaled = RISK_MULTIPLIER * rolling_rp
    equity = equity_from_returns(scaled)
    sh = sharpe(scaled, BARS_PER_YEAR)
    dd = max_drawdown(equity)
    total_return = float(equity.iloc[-1] - 1)
    yr_log = np.log1p(scaled).groupby(scaled.index.year).sum()
    n_pos, n_years = int((yr_log > 0).sum()), len(yr_log)
    worst_year, worst_year_label = float(yr_log.min()), int(yr_log.idxmin())
    worst_day = float(scaled.min())

    print(f"=== ORB gold + US30 breakout, rolling risk-parity, {RISK_MULTIPLIER:.0f}x standard risk ===")
    print(f"Sharpe: {sh:+.3f} (unchanged from 1x -- linear rescaling)")
    print(f"maxDD: {dd*100:.1f}%")
    print(f"Total compounded return: {total_return*100:+.1f}% over {(idx[-1]-idx[0]).days/365.25:.2f} years")
    print(f"Years positive: {n_pos}/{n_years} (worst: {worst_year_label} {worst_year*100:+.1f}%)")
    print(f"Worst single day: {worst_day*100:+.2f}%\n")

    data_start, data_end = idx.min(), idx.max()
    r1 = rolling_pass_rate_daily(scaled, data_start, data_end, phase=1, max_days=MAX_DAYS, best_day_cap=BEST_DAY_CAP)
    r2 = rolling_pass_rate_daily(scaled, data_start, data_end, phase=2, max_days=MAX_DAYS, best_day_cap=BEST_DAY_CAP)
    print(f"Phase 1 (independent, target +10%): n={r1['n_challenges']}, "
          f"raw={r1['pass_rate_raw']*100:.1f}%, consistency-adj={r1['pass_rate_consistency']*100:.1f}%, "
          f"reasons={r1['reasons']}")
    print(f"Phase 2 (independent, target +5%):  n={r2['n_challenges']}, "
          f"raw={r2['pass_rate_raw']*100:.1f}%, consistency-adj={r2['pass_rate_consistency']*100:.1f}%, "
          f"reasons={r2['reasons']}\n")

    chain = two_phase_chain(scaled, data_start, data_end)
    n_total = len(chain)
    n_p1 = int(chain["phase1_pass"].sum())
    n_funded = int((chain["funded"] == True).sum())
    print("=== REALISTIC CHAINED TWO-PHASE RESULT (the number that matters) ===")
    print(f"n_challenge_starts={n_total}")
    print(f"Phase 1 passes: {n_p1} ({n_p1/n_total*100:.1f}%)")
    print(f"FULLY FUNDED (Phase 1 -> Phase 2 in sequence): {n_funded} ({n_funded/n_total*100:.1f}%)")
    print(f"Failure-point breakdown: {chain['reason'].value_counts().to_dict()}")

    out = RESULTS / "ftmo_check_6x_reference.csv"
    chain.to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (fixed-multiplier FTMO check + two-phase chain "
          "on already-scored legs). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
