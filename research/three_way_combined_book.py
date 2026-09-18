"""
three_way_combined_book.py — natural next step after Sec87: does adding the
VIX/real-yield sleeve to the project's actual best DEPLOYABLE 2-leg book
(Sec52: ORB gold RETEST + US30 breakout, rolling risk-parity) improve on
either the 2-leg book or the ORB-gold+sleeve pairing (Sec85/Sec87) alone?

Sec85/Sec87 paired the sleeve with ORB gold RETEST ONLY (not the full Sec52
book) because that was the natural apples-to-apples comparison at the time.
This section builds the full 3-way portfolio: ORB gold RETEST + US30
breakout + VIX/real-yield sleeve, under a GENERALIZED rolling (causal,
monthly-rebalanced) inverse-vol weighting scheme (extending research/
combined_book_risk_parity_rolling.py's 2-leg version to N legs, same
methodology: trailing 90-calendar-day std, monthly rebalance, no look-
ahead, defaults to equal weight before 90 days of history exist).

All three legs reuse already-scored, UNCHANGED mechanisms:
  - ORB gold RETEST: Sec39/Sec68 params (tol_frac=0.20, stop_mode='moderate')
  - US30 breakout: Sec45 params (N=20, k_atr=4.0, R=0.25, H=20), full
    2013-2025 window per Sec87's leg reconstruction
  - VIX/real-yield sleeve: Sec84's fixed-50/50 combination (VIX window=120d/
    thr=1.25, real-yield lookback=20d)

Zero new backtest trials -- portfolio construction on three already-scored
legs, matching Sec44-Sec57/Sec76/Sec84/Sec87's convention.
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
from research.ftmo_check_headline_vs_new_book_same_window import us30_breakout_leg_daily_returns_full
from research.run_cot_gold_signal import annualized_sharpe, max_drawdown
from research.ftmo_engine import equity_from_returns
from research.ftmo_check_6x_reference import two_phase_chain

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
VOL_WINDOW_DAYS = 90


def rolling_weights_n(legs: dict[str, pd.Series]) -> pd.DataFrame:
    """Causal monthly-rebalanced inverse-vol weights across N legs. Returns a
    DataFrame of weights (one column per leg name) indexed like the legs.
    Extends research/combined_book_risk_parity_rolling.py's 2-leg version."""
    names = list(legs.keys())
    df = pd.DataFrame(legs)
    idx = df.index
    tz = idx.tz
    month_key = idx.tz_localize(None).to_period("M") if tz is not None else idx.to_period("M")
    last_pos_per_month = pd.Series(np.arange(len(idx)), index=month_key).groupby(level=0).max()
    rebalance_positions = last_pos_per_month.to_numpy()

    weights_at_pos = {}
    for pos in rebalance_positions:
        window = df.iloc[max(0, pos - VOL_WINDOW_DAYS + 1): pos + 1]
        if len(window) < VOL_WINDOW_DAYS:
            weights_at_pos[pos] = {n: 1.0 / len(names) for n in names}
            continue
        stds = window.std()
        inv = 1.0 / stds
        w = inv / inv.sum()
        weights_at_pos[pos] = w.to_dict()

    out = pd.DataFrame(index=idx, columns=names, dtype=float)
    sorted_positions = sorted(weights_at_pos.keys())
    for i, pos in enumerate(sorted_positions):
        start = pos + 1
        end = sorted_positions[i + 1] if i + 1 < len(sorted_positions) else len(idx)
        for n in names:
            out.iloc[start:end, out.columns.get_loc(n)] = weights_at_pos[pos][n]
    # before the first rebalance point, equal weight
    first_pos = sorted_positions[0]
    for n in names:
        out.iloc[: first_pos + 1, out.columns.get_loc(n)] = 1.0 / len(names)
    return out.ffill().fillna(1.0 / len(names))


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

    legs = {"orb_gold": gold, "us30_breakout": us30, "sleeve": sleeve}
    w = rolling_weights_n(legs)
    rp3 = (w["orb_gold"] * gold + w["us30_breakout"] * us30 + w["sleeve"] * sleeve)
    fixed3 = (gold + us30 + sleeve) / 3.0

    data_start, data_end = idx.min(), idx.max()
    print(f"Window: {data_start.date()} -> {data_end.date()}\n")

    rows = []
    for label, series in [
        ("ORB gold RETEST standalone", gold),
        ("US30 breakout standalone", us30),
        ("VIX+real-yield sleeve standalone", sleeve),
        ("2-leg headline (gold+US30, rolling RP)", None),  # computed below for reference
        ("2-leg new book (gold+sleeve, fixed 50/50)", None),
        ("3-way, fixed equal-weight", fixed3),
        ("3-way, rolling risk-parity", rp3),
    ]:
        if series is None:
            continue
        eq = equity_from_returns(series)
        sh = annualized_sharpe(series)
        dd = max_drawdown(eq)
        tot = float(eq.iloc[-1] - 1.0)
        yr_log = np.log1p(series).groupby(series.index.year).sum()
        n_pos, n_years = int((yr_log > 0).sum()), len(yr_log)
        rows.append(dict(label=label, sharpe=sh, max_dd=dd, total_return=tot, n_pos_years=n_pos, n_years=n_years))
        print(f"{label}: Sharpe={sh:+.3f}  maxDD={dd*100:.1f}%  total_return={tot*100:+.1f}%  years+={n_pos}/{n_years}")

    print()
    # FTMO chained sweep on the 3-way rolling RP book, since it's the deployable candidate.
    print("FTMO chained funded-probability sweep, 3-way rolling risk-parity:")
    ftmo_rows = []
    for mult in [1.0, 3.0, 5.0, 6.0, 7.0, 8.0, 10.0, 14.0]:
        scaled = mult * rp3
        eq = equity_from_returns(scaled)
        sh = annualized_sharpe(scaled)
        dd = max_drawdown(eq)
        chain = two_phase_chain(scaled, data_start, data_end)
        n_total = len(chain)
        n_funded = int((chain["funded"] == True).sum())
        print(f"  {mult:.0f}x: Sharpe={sh:+.3f} maxDD={dd*100:.1f}% funded={n_funded}/{n_total} ({n_funded/n_total*100:.1f}%)")
        ftmo_rows.append(dict(multiplier=mult, sharpe=sh, max_dd=dd, funded_rate=n_funded / n_total))

    out1 = RESULTS / "three_way_combined_book.csv"
    pd.DataFrame(rows).to_csv(out1, index=False)
    out2 = RESULTS / "three_way_combined_book_ftmo.csv"
    pd.DataFrame(ftmo_rows).to_csv(out2, index=False)
    print(f"\nSaved {out1}\nSaved {out2}")

    best = pd.DataFrame(ftmo_rows).loc[pd.DataFrame(ftmo_rows)["funded_rate"].idxmax()]
    peak_mult = float(best["multiplier"])
    print(f"\n3-way book peak: {best['funded_rate']*100:.1f}% at {peak_mult:.0f}x "
          f"(vs 2-leg new book's 35.7% at 6x, Sec87; vs headline's 33.1% at 14x, Sec87)")

    # Period-robustness check on the 3-way peak, same method as Sec88 -- not assumed stable.
    tz = data_start.tz
    halves = [
        ("2013-2019 (H1)", pd.Timestamp("2013-01-01", tz=tz), pd.Timestamp("2019-07-01", tz=tz)),
        ("2019-2026 (H2)", pd.Timestamp("2019-07-01", tz=tz), pd.Timestamp("2026-01-01", tz=tz)),
    ]
    thirds = [
        ("2013-2017 (T1)", pd.Timestamp("2013-01-01", tz=tz), pd.Timestamp("2017-05-01", tz=tz)),
        ("2017-2021 (T2)", pd.Timestamp("2017-05-01", tz=tz), pd.Timestamp("2021-09-01", tz=tz)),
        ("2021-2026 (T3)", pd.Timestamp("2021-09-01", tz=tz), pd.Timestamp("2026-01-01", tz=tz)),
    ]
    chain_peak = two_phase_chain(peak_mult * rp3, data_start, data_end)
    print(f"\nPeriod-robustness check on the 3-way peak ({peak_mult:.0f}x):")
    for label, bins in [("HALVES", halves), ("THIRDS", thirds)]:
        print(f"  --- {label} ---")
        for name, lo, hi in bins:
            sub = chain_peak[(chain_peak["start"] >= lo) & (chain_peak["start"] < hi)]
            n = len(sub)
            if n == 0:
                continue
            n_funded = int((sub["funded"] == True).sum())
            print(f"    {name}: n={n}  FUNDED={n_funded}/{n}={n_funded/n*100:.1f}%")

    print("\nTrial count: 0 new (portfolio construction on three already-scored legs).")


if __name__ == "__main__":
    main()
