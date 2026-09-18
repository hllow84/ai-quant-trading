"""
orb_gold_real_yield_combined_book.py -- combined-book check: ORB gold RETEST
(Sec39/Sec68, intraday session strategy) + the real-yield trend signal
(Sec75, a multi-day swing overlay on the SAME underlying, XAUUSD), on the
FULL 2013-2025 window.

WHY THIS PAIRING: Sec75 found the real-yield trend signal has a genuine
gross+net edge and tighter drawdown than gold buy-and-hold, but loses to
buy-and-hold overall because it fights gold's 2023-2025 rally -- while
winning decisively in gold's 2013-2017 bear/chop years. ORB gold RETEST
(Sec68) is ALSO strongly profitable in exactly that 2013-2017 window
(Sharpe +1.457) and is unrelated in mechanism (intraday session
opening-range retest vs a multi-day macro trend read) -- a real a priori
reason to expect low correlation between the two, unlike combining two
signals on the same instrument that both reference price momentum.

METHOD: identical to the project's established combined-book convention
(Sec44-Sec57, Sec68's out-of-regime re-run) -- each leg computed with its
own unchanged, already-tuned parameters (no re-optimization), daily returns
aligned on the union of trading days, combined at fixed 50/50 AND rolling
(causal, monthly-rebalanced) risk-parity via the same rolling_weight_series()
used throughout this project.

Zero new trials -- a portfolio-construction check on two already-scored
legs (Sec39/Sec68's ORB gold RETEST, Sec75's real-yield trend signal), no
parameter search. Cumulative trial count unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import aggregate_daily
from research.ftmo_engine import build_daily_returns, equity_from_returns
from research.metrics import sharpe, max_drawdown
from research.orb_retest_entry_stop_grid import mid_frame, build_trades as gold_build_trades
from research.combined_book_risk_parity_rolling import rolling_weight_series
from research.run_cot_gold_signal import load_full_daily_gold
from research.run_real_yield_gold_signal import build_rate_signal, COMMISSION_PER_OZ, SLIP_PER_SIDE_OZ
from research.backtest import run as run_backtest

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
GOLD_FULL_2013_2017 = _ROOT / "data" / "XAUUSD_M1_2013_2017_spot_dukascopy.csv"
GOLD_2018_2025 = _ROOT / "data" / "XAUUSD_M1_2018_2025_spot_dukascopy.csv"


def orb_gold_leg_daily_returns() -> pd.Series:
    m17, spot17 = mid_frame(GOLD_FULL_2013_2017)
    m18, spot18 = mid_frame(GOLD_2018_2025)
    m = pd.concat([m17, m18]).sort_index()
    spot = pd.concat([spot17, spot18]).sort_index()
    daily_index = aggregate_daily(spot).index
    tr = gold_build_trades(m, tol_frac=0.20, stop_mode="moderate")
    ret = build_daily_returns(tr, daily_index)
    ret.index = ret.index.tz_localize(None)
    return ret


def real_yield_leg_daily_returns() -> pd.Series:
    daily = load_full_daily_gold()
    signal = build_rate_signal(daily)
    asset_ret = daily["mid_close"].pct_change()

    avg_spread_bps = float((daily["spread_close"] / daily["mid_close"]).mean() * 1e4)
    avg_price = float(daily["mid_close"].mean())
    commission_bps = (COMMISSION_PER_OZ / avg_price) * 1e4
    slip_bps = (SLIP_PER_SIDE_OZ / avg_price) * 1e4
    cost_bps_per_side = avg_spread_bps / 2.0 + commission_bps / 2.0 + slip_bps

    result = run_backtest(signal=signal, asset_returns=asset_ret, fee_bps=cost_bps_per_side,
                           slippage_bps=0.0, direction="both", guard=True)
    ret = result["net_ret"].copy()
    ret.index = ret.index.tz_localize(None)
    return ret.dropna()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    g = orb_gold_leg_daily_returns()
    r = real_yield_leg_daily_returns()

    idx = g.index.union(r.index)
    g = g.reindex(idx, fill_value=0.0)
    r = r.reindex(idx, fill_value=0.0)

    corr = float(g.corr(r))
    print(f"Correlation (ORB gold RETEST daily returns, real-yield trend daily returns) = {corr:.3f}")

    fixed = 0.5 * g + 0.5 * r
    w = rolling_weight_series(g, r)
    rp = w * g + (1.0 - w) * r

    rows = []
    for label, s in [("ORB gold RETEST standalone", g),
                      ("Real-yield trend standalone", r),
                      ("Combined, fixed 50/50", fixed),
                      ("Combined, rolling risk-parity (deployable)", rp)]:
        eq = equity_from_returns(s)
        sh = sharpe(s, BARS_PER_YEAR)
        dd = max_drawdown(eq)
        tot = float(eq.iloc[-1] - 1.0)
        yr_log = np.log1p(s).groupby(s.index.year).sum()
        n_pos = int((yr_log > 0).sum())
        n_years = len(yr_log)
        rows.append(dict(label=label, sharpe=sh, max_dd=dd, total_return=tot,
                          n_pos_years=n_pos, n_years=n_years))
        print(f"{label}: Sharpe={sh:+.3f}  maxDD={dd*100:.1f}%  total_return={tot*100:+.1f}%  "
              f"years+={n_pos}/{n_years}")

    out = RESULTS / "orb_gold_real_yield_combined_book.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio construction on two already-scored legs).")


if __name__ == "__main__":
    main()
