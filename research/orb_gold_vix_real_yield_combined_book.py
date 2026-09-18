"""
orb_gold_vix_real_yield_combined_book.py — Pairs ORB gold RETEST (Sec39/
Sec68, Sharpe +1.479 standalone on the full 2013-2025 window, Sec76) with
the VIX+real-yield SLEEVE (Sec84, fixed-50/50 combined Sharpe +0.432 — the
first successful combination in the new-data-source thread), closing the
quality gap from Sec76's 4.3x (real-yield alone vs ORB gold) down to ~3.4x.

Sec47 already found a 3.2x quality gap defeats even the best correlation
this project has measured; this test is the honest, not-assumed check of
whether the sleeve's improved Sharpe (vs real-yield alone) is enough to
cross that line, or whether the gap is still too large regardless of
correlation, matching the project's own established rule (Sec47/Sec50/
Sec57/Sec76).

Zero new signal-construction trials — the sleeve is Sec84's already-scored
fixed-50/50 VIX+real-yield combination (not re-optimized here), and ORB
gold RETEST reuses Sec39/Sec68's unchanged params. Portfolio construction
only, matching Sec44-Sec57/Sec76/Sec84's convention.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from research.orb_gold_real_yield_combined_book import orb_gold_leg_daily_returns
from research.vix_real_yield_combined_book import (
    VIX_WINDOW, VIX_THRESHOLD, REAL_YIELD_LOOKBACK, leg_daily_returns,
)
from research.run_cot_gold_signal import load_full_daily_gold, annualized_sharpe, max_drawdown, COMMISSION_PER_OZ, SLIP_PER_SIDE_OZ
from research.run_vix_gold_joint_grid import build_signal as build_vix_signal
from research.run_real_yield_gold_lookback_grid import build_rate_signal_for_lookback
from research.combined_book_risk_parity_rolling import rolling_weight_series
from research.ftmo_engine import equity_from_returns

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252


def build_sleeve_daily_returns() -> pd.Series:
    daily = load_full_daily_gold()
    avg_spread_bps = float((daily["spread_close"] / daily["mid_close"]).mean() * 1e4)
    avg_price = float(daily["mid_close"].mean())
    commission_bps = (COMMISSION_PER_OZ / avg_price) * 1e4
    slip_bps = (SLIP_PER_SIDE_OZ / avg_price) * 1e4
    cost_bps_per_side = avg_spread_bps / 2.0 + commission_bps / 2.0 + slip_bps

    vix_signal = build_vix_signal(daily, VIX_WINDOW, VIX_THRESHOLD)
    v = leg_daily_returns(daily, vix_signal, cost_bps_per_side)
    ry_signal = build_rate_signal_for_lookback(daily, REAL_YIELD_LOOKBACK)
    r = leg_daily_returns(daily, ry_signal, cost_bps_per_side)

    idx = v.index.union(r.index)
    v = v.reindex(idx, fill_value=0.0)
    r = r.reindex(idx, fill_value=0.0)
    return 0.5 * v + 0.5 * r  # Sec84's winning fixed-50/50 sleeve


def main() -> None:
    g = orb_gold_leg_daily_returns()
    s = build_sleeve_daily_returns()

    idx = g.index.union(s.index)
    g = g.reindex(idx, fill_value=0.0)
    s = s.reindex(idx, fill_value=0.0)

    corr = float(g.corr(s))
    print(f"Correlation (ORB gold RETEST, VIX+real-yield sleeve) = {corr:.3f}")

    fixed = 0.5 * g + 0.5 * s
    w = rolling_weight_series(g, s)
    rp = w * g + (1.0 - w) * s

    rows = []
    for label, r_ in [("ORB gold RETEST standalone", g),
                       ("VIX+real-yield sleeve standalone", s),
                       ("Combined, fixed 50/50", fixed),
                       ("Combined, rolling risk-parity", rp)]:
        eq = equity_from_returns(r_)
        sh = annualized_sharpe(r_)
        dd = max_drawdown(eq)
        tot = float(eq.iloc[-1] - 1.0)
        yr_log = np.log1p(r_).groupby(r_.index.year).sum()
        n_pos = int((yr_log > 0).sum())
        n_years = len(yr_log)
        rows.append(dict(label=label, sharpe=sh, max_dd=dd, total_return=tot,
                          n_pos_years=n_pos, n_years=n_years))
        print(f"{label}: Sharpe={sh:+.3f}  maxDD={dd*100:.1f}%  total_return={tot*100:+.1f}%  "
              f"years+={n_pos}/{n_years}")

    out = RESULTS / "orb_gold_vix_real_yield_combined_book.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio construction on two already-scored legs).")


if __name__ == "__main__":
    main()
