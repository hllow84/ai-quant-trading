"""
ftmo_check_period_robustness.py — §63: does the chained FTMO funding
probability found in §59-§62 hold up across different historical
sub-periods, or is it an artifact of pooling all 106 rolling monthly-
start challenges (2017-2025) into one number? Splits the SAME already-
computed challenge-by-challenge results (§62's corrected, no-fabricated-
rule model) by which historical era each challenge START falls in,
rather than re-running anything — a pure post-hoc partition of results
already on record.

Tested at BOTH reference points found in this project's FTMO work:
- 6x (§59's original, since-superseded reference point)
- 14x (§62's corrected true peak)

Splits: halves (2017-2021 / 2021-2025) and thirds (2017-2020 / 2020-2023
/ 2023-2025), both computed from the same underlying challenge set so
the comparison is apples-to-apples at two different levels of
granularity.

Zero new backtest trials — a period-based partition of already-computed
FTMO challenge outcomes, not a parameter search. Cumulative trial count
(N=1570) unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import pandas as pd

from research.ftmo_check_best_candidate import gold_leg_daily_returns, us30_breakout_leg_daily_returns
from research.combined_book_risk_parity_rolling import rolling_weight_series
from research.ftmo_check_6x_reference import two_phase_chain

RESULTS = _ROOT / "results"
MULTIPLIERS = (6.0, 14.0)


def report_split(chain: pd.DataFrame, label: str, bins: list[tuple[str, pd.Timestamp, pd.Timestamp]]):
    print(f"  --- {label} ---")
    rows = []
    for name, lo, hi in bins:
        sub = chain[(chain["start"] >= lo) & (chain["start"] < hi)]
        n = len(sub)
        if n == 0:
            print(f"    {name}: 0 challenges in this window")
            continue
        n_p1 = int(sub["phase1_pass"].sum())
        n_funded = int((sub["funded"] == True).sum())
        print(f"    {name}: n={n}  Phase1-only={n_p1}/{n}={n_p1/n*100:.1f}%  "
              f"FUNDED={n_funded}/{n}={n_funded/n*100:.1f}%")
        rows.append(dict(period=name, n=n, phase1_rate=n_p1 / n, funded_rate=n_funded / n))
    return rows


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

    tz = data_start.tz
    halves = [
        ("2017-2021 (H1)", pd.Timestamp("2017-01-01", tz=tz), pd.Timestamp("2021-06-01", tz=tz)),
        ("2021-2025 (H2)", pd.Timestamp("2021-06-01", tz=tz), pd.Timestamp("2026-01-01", tz=tz)),
    ]
    thirds = [
        ("2017-2020 (T1)", pd.Timestamp("2017-01-01", tz=tz), pd.Timestamp("2020-05-01", tz=tz)),
        ("2020-2023 (T2)", pd.Timestamp("2020-05-01", tz=tz), pd.Timestamp("2023-09-01", tz=tz)),
        ("2023-2025 (T3)", pd.Timestamp("2023-09-01", tz=tz), pd.Timestamp("2026-01-01", tz=tz)),
    ]

    all_rows = []
    for m in MULTIPLIERS:
        scaled = m * rolling_rp
        chain = two_phase_chain(scaled, data_start, data_end)
        n_total = len(chain)
        n_funded_total = int((chain["funded"] == True).sum())
        print(f"=== {m:.0f}x standard risk (pooled full-sample: {n_funded_total}/{n_total} = "
              f"{n_funded_total/n_total*100:.1f}% funded) ===")

        rows_h = report_split(chain, "HALVES", halves)
        for row in rows_h:
            all_rows.append(dict(multiplier=m, split="halves", **row))
        rows_t = report_split(chain, "THIRDS", thirds)
        for row in rows_t:
            all_rows.append(dict(multiplier=m, split="thirds", **row))
        print()

    out = RESULTS / "ftmo_check_period_robustness.csv"
    pd.DataFrame(all_rows).to_csv(out, index=False)
    print(f"Saved {out}")
    print("Trial count: 0 new (period-based partition of already-computed FTMO "
          "challenge outcomes). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
