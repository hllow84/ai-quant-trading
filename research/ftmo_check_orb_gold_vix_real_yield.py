"""
ftmo_check_orb_gold_vix_real_yield.py — FTMO Challenge ruleset check on the
Sec85 combined book (ORB gold RETEST + VIX/real-yield sleeve, fixed 50/50),
testing whether its ~42% maxDD reduction (vs ORB gold RETEST alone) actually
translates into a better funded probability, or whether its lower Sharpe
(+1.332 vs +1.479) costs more than the drawdown cut buys back — a real,
not-assumed question this project's own Sec58-Sec66 FTMO work has already
shown is path-dependent, not resolved by Sharpe/maxDD alone (Sec65: two
combined books with nearly identical Sharpe/maxDD funded at materially
different rates).

METHOD: identical to Sec59/Sec62's approach (linear risk-multiplier scaling,
Sharpe-invariant by construction; only maxDD/challenge-path behavior
change) applied to the Sec85 fixed-50/50 series, at the SAME reference
multipliers already established for the project's headline book (1x, 6x,
14x -- Sec58/Sec59/Sec62), for direct comparison against those already-
published numbers rather than a fresh, incomparable multiplier choice.

Zero new backtest trials on the underlying legs -- FTMO ruleset checks are
not a parameter search (Sec58's own convention). Cumulative trial count
unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.orb_gold_real_yield_combined_book import orb_gold_leg_daily_returns
from research.orb_gold_vix_real_yield_combined_book import build_sleeve_daily_returns
from research.ftmo_challenge_daily import simulate_challenge_daily, rolling_pass_rate_daily
from research.ftmo_engine import equity_from_returns
from research.metrics import max_drawdown, sharpe
from research.ftmo_check_6x_reference import two_phase_chain

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
MAX_DAYS = 60
BEST_DAY_CAP = None  # 2-Step ruleset has no consistency rule -- verified against ftmo.com 2026-09-16
MULTIPLIERS = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 14.0]
# 1x/6x/14x are the same reference points as Sec58/Sec59/Sec62 for direct
# comparison; the rest fill in to locate THIS book's own peak (6x already
# showed a materially different profile than the headline book, so its
# peak cannot be assumed to sit at the same multiplier).


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    g = orb_gold_leg_daily_returns()
    s = build_sleeve_daily_returns()
    idx = g.index.union(s.index)
    g = g.reindex(idx, fill_value=0.0)
    s = s.reindex(idx, fill_value=0.0)
    fixed = 0.5 * g + 0.5 * s

    data_start, data_end = idx.min(), idx.max()
    print(f"Combined data span: {data_start.date()} -> {data_end.date()} ({len(idx)} days)")
    print(f"1x standalone: Sharpe={sharpe(fixed, BARS_PER_YEAR):+.3f}  "
          f"maxDD={max_drawdown(equity_from_returns(fixed))*100:.1f}%\n")

    rows = []
    for mult in MULTIPLIERS:
        scaled = mult * fixed
        eq = equity_from_returns(scaled)
        sh = sharpe(scaled, BARS_PER_YEAR)
        dd = max_drawdown(eq)
        total_return = float(eq.iloc[-1] - 1)

        chain = two_phase_chain(scaled, data_start, data_end)
        n_total = len(chain)
        n_p1 = int(chain["phase1_pass"].sum())
        n_funded = int((chain["funded"] == True).sum())
        dd_breach_reasons = {"daily_loss", "total_dd"}
        n_dd_breach = int(chain["reason"].isin(dd_breach_reasons).sum())

        print(f"=== {mult:.0f}x standard risk ===")
        print(f"  Sharpe={sh:+.3f}  maxDD={dd*100:.1f}%  total_return={total_return*100:+.1f}%")
        print(f"  n_challenge_starts={n_total}  Phase1 pass={n_p1} ({n_p1/n_total*100:.1f}%)  "
              f"FUNDED (chained)={n_funded} ({n_funded/n_total*100:.1f}%)  "
              f"DD-breach rate={n_dd_breach/n_total*100:.1f}%")
        print(f"  Failure-point breakdown: {chain['reason'].value_counts().to_dict()}\n")

        rows.append(dict(multiplier=mult, sharpe=sh, max_dd=dd, total_return=total_return,
                          n_challenges=n_total, phase1_pass_rate=n_p1 / n_total,
                          funded_rate=n_funded / n_total, dd_breach_rate=n_dd_breach / n_total))

    df = pd.DataFrame(rows)
    out = RESULTS / "ftmo_check_orb_gold_vix_real_yield.csv"
    df.to_csv(out, index=False)
    print(f"Saved {out}")

    print("\n=== COMPARISON vs the project's headline book (Sec52/Sec62, ORB gold + US30 breakout, rolling RP) ===")
    print("Headline book (from Sec62's corrected table): 1x=0.0% funded, 6x=25.5%, 14x=33.0%")
    for _, row in df.iterrows():
        print(f"  This book at {row['multiplier']:.0f}x: {row['funded_rate']*100:.1f}% funded "
              f"(maxDD {row['max_dd']*100:.1f}%, Sharpe {row['sharpe']:+.3f})")

    print("\nTrial count: 0 new (FTMO-ruleset check on already-scored legs). "
          "Cumulative trials: N=1717 unchanged.")


if __name__ == "__main__":
    main()
