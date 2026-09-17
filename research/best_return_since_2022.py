"""
best_return_since_2022.py -- ad hoc user query: which candidate has the
best COMPOUNDED RETURN from 2022-01-01 onwards, not full-period Sharpe?
Reuses every leg-builder function already in the codebase unchanged (no
new backtest trials) and simply re-slices each daily-return series to
the 2022+ window, then reports compounded return, Sharpe, and maxDD
computed WITHIN that window only (not full-period stats truncated).

Covers: the 5 standalone candidates (ORB gold, credit-spread SPY, NAS100
macross, US30 macross, US30 breakout), the weaker 5th-family momentum
candidate (Sec64), and the two strongest combined books (Sec52 ORB
gold+US30 breakout rolling-RP; Sec48/Sec65 US30 macross+breakout rolling-RP).

Zero new backtest trials -- pure re-slicing of already-scored return
series. Not a STATE_OF_PLAY section; ad hoc user request.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, load_m1_mid, resample_mid, aggregate_daily
from research.metrics import sharpe, max_drawdown
from research.ftmo_engine import simulate_trades, de_overlap, build_daily_returns, equity_from_returns
from research.combined_book_risk_parity_rolling import rolling_weight_series
from research.ftmo_check_best_candidate import gold_leg_daily_returns, us30_breakout_leg_daily_returns
from research.ftmo_check_us30_macross_breakout import us30_macross_leg_daily_returns
from strategies.sweep_families import ma_cross, momentum, TF_DELTA

BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
CUTOFF = pd.Timestamp("2022-01-01", tz="UTC")


def _leg(data_path, fn, params):
    m1 = load_m1_mid(data_path)
    daily_index = aggregate_daily(load_m1_spot(data_path)).index
    m = resample_mid(m1, "4h")
    cands = fn(m, params, TF_DELTA["H4"])
    for t in cands:
        t["session_end"] = pd.Timestamp(t["session_end"]).tz_convert("UTC") if pd.Timestamp(t["session_end"]).tz else pd.Timestamp(t["session_end"]).tz_localize("UTC")
        t["entry_time"] = pd.Timestamp(t["entry_time"]).tz_convert("UTC") if pd.Timestamp(t["entry_time"]).tz else pd.Timestamp(t["entry_time"]).tz_localize("UTC")
    trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=COST_BPS))
    return build_daily_returns(trades, daily_index)


def nas100_macross():
    return _leg(_ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv", ma_cross,
                dict(fast=10, slow=30, ema_trend=200, k_atr=1.0, R=4.0, H=192))


def us30_momentum():
    return _leg(_ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv", momentum,
                dict(N=96, k_atr=1.25, R=5.0, H=192))


def credit_spread_spy():
    from research.delta10_iv_filter import load_data, IV_LOOKBACK
    from research.credit_spread_joint_reopt import run_combined_book_pt
    df = load_data()
    iv_rank = df["vix"].rolling(IV_LOOKBACK, min_periods=IV_LOOKBACK).rank(pct=True)
    eligible = iv_rank.notna()
    _, ret, _ = run_combined_book_pt(df, eligible, 0.16, 21, 0.50)
    if ret.index.tz is None:
        ret.index = ret.index.tz_localize("UTC")
    return ret


def report(label, daily_ret):
    since = daily_ret[daily_ret.index >= CUTOFF]
    if since.empty:
        print(f"{label}: no data >= 2022-01-01")
        return None
    eq = equity_from_returns(since)
    sh = sharpe(since, BARS_PER_YEAR)
    dd = max_drawdown(eq)
    total = float(eq.iloc[-1] - 1.0)
    yr_log = np.log1p(since).groupby(since.index.year).sum()
    n_pos = int((yr_log > 0).sum())
    print(f"{label}: 2022+ compounded return = {total*100:+.1f}%   Sharpe(2022+) = {sh:+.3f}   "
          f"maxDD(2022+) = {dd*100:.1f}%   years positive = {n_pos}/{len(yr_log)}   "
          f"span = {since.index[0].date()} -> {since.index[-1].date()}")
    return dict(label=label, total_return=total, sharpe=sh, max_dd=dd, n_pos=n_pos, n_years=len(yr_log))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=== Standalone candidates, project-standard 1% risk/trade fixed-fractional, 2022-01-01 onward ===\n")

    gold = gold_leg_daily_returns()
    us30_bo = us30_breakout_leg_daily_returns()
    us30_mx = us30_macross_leg_daily_returns()
    nas_mx = nas100_macross()
    mom = us30_momentum()
    spy = credit_spread_spy()

    rows = []
    rows.append(report("ORB gold RETEST (Sec39)", gold))
    rows.append(report("US30 H4 breakout-retest (Sec45)", us30_bo))
    rows.append(report("US30 H4 macross (Sec43)", us30_mx))
    rows.append(report("NAS100 H4 macross (Sec42)", nas_mx))
    rows.append(report("US30 H4 momentum (Sec64, weak 5th candidate)", mom))
    rows.append(report("Credit-spread SPY (Sec41/Sec45 joint-reopt, OPTIONS)", spy))

    print("\n=== Combined books (rolling risk-parity), 2022-01-01 onward ===\n")

    idx1 = gold.index.union(us30_bo.index)
    gold_a = gold.reindex(idx1, fill_value=0.0)
    us30bo_a = us30_bo.reindex(idx1, fill_value=0.0)
    w1 = rolling_weight_series(gold_a, us30bo_a)
    book1 = w1 * gold_a + (1.0 - w1) * us30bo_a
    rows.append(report("ORB gold + US30 breakout, rolling RP (Sec52, deployable best)", book1))

    idx2 = us30_mx.index.union(us30_bo.index)
    us30mx_a = us30_mx.reindex(idx2, fill_value=0.0)
    us30bo_a2 = us30_bo.reindex(idx2, fill_value=0.0)
    w2 = rolling_weight_series(us30mx_a, us30bo_a2)
    book2 = w2 * us30mx_a + (1.0 - w2) * us30bo_a2
    rows.append(report("US30 macross + US30 breakout, rolling RP (Sec48/Sec65)", book2))

    df = pd.DataFrame([r for r in rows if r is not None]).sort_values("total_return", ascending=False)
    print("\n=== RANKED BY 2022+ COMPOUNDED RETURN ===")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
