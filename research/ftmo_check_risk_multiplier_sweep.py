"""
ftmo_check_risk_multiplier_sweep.py — §60: chained two-phase "actually
gets funded" probability at 2x, 3x, 4x, 5x, 6x standard risk-per-trade,
for direct comparison against §59's adopted 6x reference. §58 only
reported independent per-phase pass rates at each multiplier; §59 added
the realistic CHAINED two-phase metric but only at 6x. This section runs
the SAME chained metric across the full 2x-6x range so the tradeoff curve
(not just its endpoint) is visible.

Reuses §59's two_phase_chain() and both legs' trade engines UNCHANGED —
only the fixed linear risk-multiplier varies. Sharpe is invariant to the
multiplier by construction (linear rescaling of the same return series);
only maxDD, absolute return, and challenge dynamics change. Zero new
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
from research.ftmo_check_6x_reference import two_phase_chain
from research.ftmo_challenge_daily import rolling_pass_rate_daily
from research.ftmo_engine import equity_from_returns
from research.metrics import max_drawdown, sharpe

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
MAX_DAYS = 60
BEST_DAY_CAP = 0.30
MULTIPLIERS = (2.0, 3.0, 4.0, 5.0, 6.0)


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
    data_start, data_end = idx.min(), idx.max()

    rows = []
    for m in MULTIPLIERS:
        scaled = m * rolling_rp
        equity = equity_from_returns(scaled)
        sh = sharpe(scaled, BARS_PER_YEAR)
        dd = max_drawdown(equity)
        total_return = float(equity.iloc[-1] - 1)
        yr_log = np.log1p(scaled).groupby(scaled.index.year).sum()
        n_pos, n_years = int((yr_log > 0).sum()), len(yr_log)
        worst_day = float(scaled.min())

        r1 = rolling_pass_rate_daily(scaled, data_start, data_end, phase=1, max_days=MAX_DAYS, best_day_cap=BEST_DAY_CAP)
        r2 = rolling_pass_rate_daily(scaled, data_start, data_end, phase=2, max_days=MAX_DAYS, best_day_cap=BEST_DAY_CAP)

        chain = two_phase_chain(scaled, data_start, data_end)
        n_total = len(chain)
        n_p1 = int(chain["phase1_pass"].sum())
        n_funded = int((chain["funded"] == True).sum())
        n_dd_breach = int(chain["reason"].isin(["daily_loss", "total_dd"]).sum())

        print(f"=== {m:.0f}x standard risk ===")
        print(f"  Sharpe={sh:+.3f}  maxDD={dd*100:.1f}%  total_return={total_return*100:+.1f}%  "
              f"years_pos={n_pos}/{n_years}  worst_day={worst_day*100:+.2f}%")
        print(f"  Independent: Phase1={r1['pass_rate_consistency']*100:.1f}%  "
              f"Phase2={r2['pass_rate_consistency']*100:.1f}%")
        print(f"  CHAINED (funded): {n_funded}/{n_total} = {n_funded/n_total*100:.1f}%  "
              f"(Phase1-only: {n_p1}/{n_total} = {n_p1/n_total*100:.1f}%)")
        print(f"  Attempts breaching a drawdown limit at some point: {n_dd_breach}/{n_total} "
              f"({n_dd_breach/n_total*100:.1f}%)\n")

        rows.append(dict(
            multiplier=m, sharpe=sh, max_dd=dd, total_return=total_return,
            years_pos=n_pos, years_total=n_years, worst_day=worst_day,
            phase1_independent=r1["pass_rate_consistency"], phase2_independent=r2["pass_rate_consistency"],
            phase1_only_chain=n_p1 / n_total, funded_chained=n_funded / n_total,
            dd_breach_rate=n_dd_breach / n_total,
        ))

    out = RESULTS / "ftmo_check_risk_multiplier_sweep.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Saved {out}")
    print("Trial count: 0 new (fixed-multiplier FTMO checks on already-scored legs). "
          "Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
