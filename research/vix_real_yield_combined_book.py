"""
vix_real_yield_combined_book.py — Combines Sec79/Sec83's VIX flight-to-safety
signal with Sec75/Sec82's real-yield trend signal — two signals of COMPARABLE
magnitude (both ~+0.2 to +0.35 standalone Sharpe), unlike Sec76's ORB-gold-
RETEST pairing which failed purely on the quality-gap rule (a ~1.5-Sharpe
leg diluted by a ~0.3-Sharpe leg, regardless of correlation). This tests
whether two comparably-weak-but-positive, mechanistically DIFFERENT signals
(options-implied equity fear vs. a real-rate trend) combine constructively
before considering pairing the result with a much stronger leg.

PARAMETER CHOICES (both picked from their own plateau, not argmax, per this
project's spec §8.1 convention):
    VIX:        window=120d, threshold=1.25 (Sharpe +0.190 standalone) — an
                interior point of Sec83's identified 90-252d/1.0-1.5 plateau,
                not its single best cell (180d/1.25, +0.346), to avoid
                selecting the lucky peak.
    Real-yield: lookback=20d (Sharpe +0.345 standalone) — Sec75's ORIGINAL a
                priori choice. Sec82 found this sits in a FRAGILE 2-cell
                spike, not a robust plateau — used here anyway since it is
                the only real-yield parameterization tested end-to-end so
                far, with that fragility caveat carried forward explicitly,
                not hidden.

Zero new signal-construction trials (both legs reuse already-scored
mechanisms) — this is a portfolio-construction check, matching Sec44-Sec57/
Sec76's convention.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from research.run_cot_gold_signal import (
    load_full_daily_gold, annualized_sharpe, max_drawdown,
    COMMISSION_PER_OZ, SLIP_PER_SIDE_OZ,
)
from research.run_vix_gold_joint_grid import build_signal as build_vix_signal
from research.run_real_yield_gold_lookback_grid import build_rate_signal_for_lookback
from research.backtest import run as run_backtest
from research.combined_book_risk_parity_rolling import rolling_weight_series
from research.ftmo_engine import equity_from_returns

RESULTS = _ROOT / "results"
VIX_WINDOW = 120
VIX_THRESHOLD = 1.25
REAL_YIELD_LOOKBACK = 20


def leg_daily_returns(daily: pd.DataFrame, signal: pd.Series, cost_bps_per_side: float) -> pd.Series:
    asset_ret = daily["mid_close"].pct_change()
    result = run_backtest(signal=signal, asset_returns=asset_ret, fee_bps=cost_bps_per_side,
                           slippage_bps=0.0, direction="both", guard=True)
    ret = result["net_ret"].copy()
    ret.index = ret.index.tz_localize(None)
    return ret.dropna()


def main() -> None:
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

    corr = float(v.corr(r))
    print(f"VIX leg: window={VIX_WINDOW}d thr={VIX_THRESHOLD} | Real-yield leg: lookback={REAL_YIELD_LOOKBACK}d")
    print(f"Correlation (VIX daily returns, real-yield daily returns) = {corr:.3f}\n")

    fixed = 0.5 * v + 0.5 * r
    w = rolling_weight_series(v, r)
    rp = w * v + (1.0 - w) * r

    bh_ret = daily["mid_close"].pct_change().dropna()
    bh_ret.index = bh_ret.index.tz_localize(None)
    bh_eq = equity_from_returns(bh_ret.reindex(idx, fill_value=0.0))
    bh_sh = annualized_sharpe(bh_ret)

    rows = []
    for label, s in [("VIX standalone", v),
                      ("Real-yield standalone", r),
                      ("Combined, fixed 50/50", fixed),
                      ("Combined, rolling risk-parity", rp)]:
        eq = equity_from_returns(s)
        sh = annualized_sharpe(s)
        dd = max_drawdown(eq)
        tot = float(eq.iloc[-1] - 1.0)
        yr_log = np.log1p(s).groupby(s.index.year).sum()
        n_pos = int((yr_log > 0).sum())
        n_years = len(yr_log)
        rows.append(dict(label=label, sharpe=sh, max_dd=dd, total_return=tot,
                          n_pos_years=n_pos, n_years=n_years))
        print(f"{label}: Sharpe={sh:+.3f}  maxDD={dd*100:.1f}%  total_return={tot*100:+.1f}%  "
              f"years+={n_pos}/{n_years}")

    print(f"\nBuy-and-hold gold (reference): Sharpe={bh_sh:+.3f}  total_return={(bh_eq.iloc[-1]-1)*100:+.1f}%")

    out = RESULTS / "vix_real_yield_combined_book.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio construction on two already-scored legs).")


if __name__ == "__main__":
    main()
