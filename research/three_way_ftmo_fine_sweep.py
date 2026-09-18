"""
three_way_ftmo_fine_sweep.py — Sec89's coarse sweep {1,3,5,6,7,8,10,14}
found the 3-way rolling-RP book's peak at 14x (the top of that grid) --
meaning the TRUE peak could sit anywhere at or above 14x, not necessarily
AT 14x. This fills in 9x-24x at step 1 to actually locate it, rather than
reporting the edge of a coarse grid as if it were confirmed interior
optimum (the same plateau-vs-argmax discipline this project applies to
every other parameter search).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import pandas as pd

from research.orb_gold_real_yield_combined_book import orb_gold_leg_daily_returns
from research.orb_gold_vix_real_yield_combined_book import build_sleeve_daily_returns
from research.ftmo_check_headline_vs_new_book_same_window import us30_breakout_leg_daily_returns_full
from research.three_way_combined_book import rolling_weights_n
from research.run_cot_gold_signal import annualized_sharpe, max_drawdown
from research.ftmo_engine import equity_from_returns
from research.ftmo_check_6x_reference import two_phase_chain

RESULTS = _ROOT / "results"
MULTIPLIERS = list(range(9, 25))  # 9x..24x, step 1


def main():
    gold = orb_gold_leg_daily_returns()
    us30 = us30_breakout_leg_daily_returns_full()
    sleeve = build_sleeve_daily_returns()
    idx = gold.index.union(us30.index).union(sleeve.index)
    gold = gold.reindex(idx, fill_value=0.0)
    us30 = us30.reindex(idx, fill_value=0.0)
    sleeve = sleeve.reindex(idx, fill_value=0.0)

    w = rolling_weights_n({"orb_gold": gold, "us30_breakout": us30, "sleeve": sleeve})
    rp3 = w["orb_gold"] * gold + w["us30_breakout"] * us30 + w["sleeve"] * sleeve
    data_start, data_end = idx.min(), idx.max()

    rows = []
    for mult in MULTIPLIERS:
        scaled = float(mult) * rp3
        eq = equity_from_returns(scaled)
        sh = annualized_sharpe(scaled)
        dd = max_drawdown(eq)
        chain = two_phase_chain(scaled, data_start, data_end)
        n_total = len(chain)
        n_funded = int((chain["funded"] == True).sum())
        n_dd_breach = int(chain["reason"].isin({"daily_loss", "total_dd"}).sum())
        print(f"{mult:>3}x: Sharpe={sh:+.3f} maxDD={dd*100:6.1f}% "
              f"funded={n_funded}/{n_total} ({n_funded/n_total*100:5.1f}%)  "
              f"DD-breach={n_dd_breach/n_total*100:.1f}%")
        rows.append(dict(multiplier=mult, sharpe=sh, max_dd=dd,
                          funded_rate=n_funded / n_total, dd_breach_rate=n_dd_breach / n_total))

    df = pd.DataFrame(rows)
    out = RESULTS / "three_way_ftmo_fine_sweep.csv"
    df.to_csv(out, index=False)

    best = df.loc[df["funded_rate"].idxmax()]
    print(f"\nTrue peak: {best['funded_rate']*100:.1f}% at {best['multiplier']:.0f}x")
    is_edge = best["multiplier"] == MULTIPLIERS[-1]
    print(f"{'[!] STILL AT GRID EDGE -- extend further' if is_edge else 'Interior peak confirmed, not a grid-edge artifact.'}")
    print(f"\nSaved {out}")
    print("Trial count: 0 new (finer resolution on already-scored portfolio, not a new signal search).")


if __name__ == "__main__":
    main()
