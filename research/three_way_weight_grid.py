"""
three_way_weight_grid.py — Sec89 only tried equal-weight and rolling
risk-parity for the 3-way book (ORB gold RETEST + US30 breakout +
VIX/real-yield sleeve). This grids every FIXED weight combination on the
2-simplex (w_gold + w_us30 + w_sleeve = 1, step 0.1) to find the IN-SAMPLE
ceiling — explicitly flagged as an in-sample optimum (full-history argmax),
NOT a deployable weight, the same honest caveat this project applied to
Sec51's in-sample risk-parity before Sec52's causal rolling version. This
is a ceiling-finding exercise: how much is left on the table by rolling
RP's out-of-sample constraint, not a new recommendation.

66 grid cells (11x11 simplex with step 0.1, excluding infeasible w3<0).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from research.orb_gold_real_yield_combined_book import orb_gold_leg_daily_returns
from research.orb_gold_vix_real_yield_combined_book import build_sleeve_daily_returns
from research.ftmo_check_headline_vs_new_book_same_window import us30_breakout_leg_daily_returns_full
from research.run_cot_gold_signal import annualized_sharpe, max_drawdown
from research.ftmo_engine import equity_from_returns

RESULTS = _ROOT / "results"
STEP = 0.1


def main():
    gold = orb_gold_leg_daily_returns()
    us30 = us30_breakout_leg_daily_returns_full()
    sleeve = build_sleeve_daily_returns()
    idx = gold.index.union(us30.index).union(sleeve.index)
    gold = gold.reindex(idx, fill_value=0.0)
    us30 = us30.reindex(idx, fill_value=0.0)
    sleeve = sleeve.reindex(idx, fill_value=0.0)

    weights = np.round(np.arange(0.0, 1.0 + STEP / 2, STEP), 2)
    rows = []
    for w1 in weights:
        for w2 in weights:
            w3 = round(1.0 - w1 - w2, 2)
            if w3 < -1e-9 or w3 > 1.0 + 1e-9:
                continue
            w3 = max(0.0, w3)
            series = w1 * gold + w2 * us30 + w3 * sleeve
            sh = annualized_sharpe(series)
            dd = max_drawdown(equity_from_returns(series))
            rows.append(dict(w_gold=w1, w_us30=w2, w_sleeve=w3, sharpe=sh, max_dd=dd))

    df = pd.DataFrame(rows)
    out = RESULTS / "three_way_weight_grid.csv"
    df.to_csv(out, index=False)

    best = df.loc[df["sharpe"].idxmax()]
    print(f"IN-SAMPLE BEST (ceiling, NOT deployable): w_gold={best['w_gold']:.2f} "
          f"w_us30={best['w_us30']:.2f} w_sleeve={best['w_sleeve']:.2f} "
          f"Sharpe={best['sharpe']:+.3f} maxDD={best['max_dd']*100:.1f}%")

    # Reference points for comparison
    rp_row = df[(df["w_gold"].round(1) == 0.3) & (df["w_us30"].round(1) == 0.3)]
    equal = df[(df["w_gold"] == round(1/3, 2)) | ((df["w_gold"] - 1/3).abs() < 0.05)]
    print(f"\nReference: Sec89 rolling RP standalone Sharpe was +1.477 (not a fixed weight, causal)")
    print(f"Reference: equal-weight (1/3 each) Sharpe was +1.409 (Sec89)")

    top10 = df.sort_values("sharpe", ascending=False).head(10)
    print("\nTop 10 fixed-weight combos by Sharpe (in-sample):")
    print(top10.to_string(index=False))

    n_beat_rp = int((df["sharpe"] > 1.477).sum())
    print(f"\n{n_beat_rp}/{len(df)} fixed-weight combos beat the causal rolling RP's Sharpe (+1.477) "
          f"IN-SAMPLE -- expected, since rolling RP is out-of-sample-constrained and fixed weights "
          f"here are chosen with full hindsight. The gap between the best fixed weight and rolling RP "
          f"is the honest cost of causality, not free money left on the table.")

    print(f"\nSaved {out}")
    print(f"Trial count: {len(df)} new (grid cells).")


if __name__ == "__main__":
    main()
