"""
ftmo_check_period_robustness_new_book.py — Sec63 found the headline book's
old 14x peak (on the 2017-2025 window) was front-loaded: strong in
2017-2021, decaying to nearly 6x's own level by 2021-2025. Sec87 found a
NEW project-best (ORB gold + VIX/real-yield sleeve, peak 35.7% at 6x,
vs the headline book's 33.1% at 14x, apples-to-apples on the full
2013-2025 window) — this section checks whether that new 6x peak is
MORE era-stable than the old 14x peak, as its lower multiplier would
suggest by analogy to Sec63's own finding (6x was comparatively stable
there too), or whether that pattern doesn't hold on this extended window
and instrument pairing. NOT ASSUMED either way -- tested directly.

Splits the SAME already-computed challenge-by-challenge chained results
(both books re-scored on the full 2013-2025 window per Sec87) by which
era each challenge START falls in -- halves and thirds -- for BOTH books
at their own respective peaks (headline@14x, new book@6x) so the
comparison is fair (each book at ITS OWN best setting, not an arbitrary
shared multiplier).

Zero new backtest trials -- a period-based partition of already-computed
FTMO challenge outcomes, not a parameter search.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import pandas as pd

from research.orb_gold_real_yield_combined_book import orb_gold_leg_daily_returns
from research.orb_gold_vix_real_yield_combined_book import build_sleeve_daily_returns
from research.ftmo_check_headline_vs_new_book_same_window import us30_breakout_leg_daily_returns_full
from research.combined_book_risk_parity_rolling import rolling_weight_series
from research.ftmo_check_6x_reference import two_phase_chain

RESULTS = _ROOT / "results"


def report_split(chain: pd.DataFrame, label: str, bins: list[tuple[str, pd.Timestamp, pd.Timestamp]]):
    print(f"  --- {label} ---")
    rows = []
    for name, lo, hi in bins:
        sub = chain[(chain["start"] >= lo) & (chain["start"] < hi)]
        n = len(sub)
        if n == 0:
            print(f"    {name}: 0 challenges in this window")
            continue
        n_funded = int((sub["funded"] == True).sum())
        print(f"    {name}: n={n}  FUNDED={n_funded}/{n}={n_funded/n*100:.1f}%")
        rows.append(dict(period=name, n=n, funded_rate=n_funded / n))
    return rows


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    gold = orb_gold_leg_daily_returns()
    us30 = us30_breakout_leg_daily_returns_full()
    sleeve = build_sleeve_daily_returns()
    idx = gold.index.union(us30.index).union(sleeve.index)
    gold = gold.reindex(idx, fill_value=0.0)
    us30 = us30.reindex(idx, fill_value=0.0)
    sleeve = sleeve.reindex(idx, fill_value=0.0)

    w = rolling_weight_series(gold, us30)
    headline_rp = w * gold + (1.0 - w) * us30
    new_book_fixed = 0.5 * gold + 0.5 * sleeve

    data_start, data_end = idx.min(), idx.max()
    tz = data_start.tz
    print(f"Window: {data_start.date()} -> {data_end.date()}\n")

    halves = [
        ("2013-2019 (H1)", pd.Timestamp("2013-01-01", tz=tz), pd.Timestamp("2019-07-01", tz=tz)),
        ("2019-2026 (H2)", pd.Timestamp("2019-07-01", tz=tz), pd.Timestamp("2026-01-01", tz=tz)),
    ]
    thirds = [
        ("2013-2017 (T1)", pd.Timestamp("2013-01-01", tz=tz), pd.Timestamp("2017-05-01", tz=tz)),
        ("2017-2021 (T2)", pd.Timestamp("2017-05-01", tz=tz), pd.Timestamp("2021-09-01", tz=tz)),
        ("2021-2026 (T3)", pd.Timestamp("2021-09-01", tz=tz), pd.Timestamp("2026-01-01", tz=tz)),
    ]

    all_rows = []
    for label, series, mult in [("Headline (ORB gold + US30 breakout)", headline_rp, 14.0),
                                 ("New book (ORB gold + VIX/real-yield sleeve)", new_book_fixed, 6.0)]:
        scaled = mult * series
        chain = two_phase_chain(scaled, data_start, data_end)
        n_total = len(chain)
        n_funded_total = int((chain["funded"] == True).sum())
        print(f"=== {label} @ {mult:.0f}x (its own peak) — pooled: {n_funded_total}/{n_total} "
              f"= {n_funded_total/n_total*100:.1f}% funded ===")

        rows_h = report_split(chain, "HALVES", halves)
        for row in rows_h:
            all_rows.append(dict(book=label, multiplier=mult, split="halves", **row))
        rows_t = report_split(chain, "THIRDS", thirds)
        for row in rows_t:
            all_rows.append(dict(book=label, multiplier=mult, split="thirds", **row))
        print()

    out = RESULTS / "ftmo_check_period_robustness_new_book.csv"
    pd.DataFrame(all_rows).to_csv(out, index=False)
    print(f"Saved {out}")
    print("Trial count: 0 new (period-based partition of already-computed FTMO challenge outcomes).")


if __name__ == "__main__":
    main()
