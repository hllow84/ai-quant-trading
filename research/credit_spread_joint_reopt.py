"""
credit_spread_joint_reopt.py — JOINT re-optimization: does §40's new best
entry (delta=0.16, dte=21) change the optimal early-exit threshold found in
§38 (50%, tuned against the OLD entry delta=0.10/dte=37)?

WHY: §38 and §40 were staged (exit optimized first holding entry fixed,
then entry optimized holding exit fixed) for efficiency — but staged
optimization can miss a genuine interaction between dimensions. This
script closes that gap: fix the new best entry (delta=0.16, dte=21, width
2%, from §40) and re-sweep profit_target_frac to see whether 50% is still
optimal once entry has moved.

GRID: profit_target_frac in {0.25, 0.50, 0.75, 0.85, 0.95} at the fixed
delta=0.16/dte=21 entry. 0.50 reproduces §40's headline cell exactly (not
counted). 4 new trials (0.25/0.75 are a re-run of the §38-style bracket at
the new entry; 0.85/0.95 extend past 0.75 IF 0.75 beats 0.50, per the same
follow-the-gradient-past-the-edge discipline as §39/§40).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.dsr import deflated_sharpe
from research.metrics import sharpe, max_drawdown
from research.delta10_iv_filter import (
    load_data, bs_price, R_RATE, IV_LOOKBACK, HALF_SPREAD, COMMISSION_PCT,
    CONTRACT_MULT, BARS_PER_YEAR,
)
from research.credit_spread_iv_filter import worst_day_month, year_stats
from research.credit_spread_entry_grid import _try_open_param, START_CAPITAL

RESULTS = _ROOT / "results"
PROFIT_TARGETS = (0.25, 0.50, 0.75, 0.85, 0.95)
DELTA, DTE = 0.16, 21
PRIOR_TRIALS = 1395
NEW_TRIALS = 4  # 0.25, 0.75, 0.85, 0.95 (0.50 reproduces §40)


def run_combined_book_pt(df, eligible, target_delta, dte_days, profit_target_frac):
    idx = df.index
    spy = df["spy"].to_numpy()
    vix = df["vix"].to_numpy() / 100.0
    n = len(df)
    capital = START_CAPITAL
    equity = pd.Series(START_CAPITAL, index=idx)
    daily_ret = pd.Series(0.0, index=idx)
    open_pos = {"put": None, "call": None}
    trades = []
    for i in range(1, n):
        decision_i = i - 1
        day_pnl_dollars = 0.0
        S_t, sig_t = float(spy[i]), float(vix[i])
        for opt_type in ("put", "call"):
            pos = open_pos[opt_type]
            if pos is None:
                cand = _try_open_param(idx, i, decision_i, spy, vix, opt_type, eligible, capital,
                                        target_delta, dte_days)
                if cand is None or "rejected" in cand:
                    continue
                open_pos[opt_type] = cand
                day_pnl_dollars += cand["entry_equity_per_contract"] * cand["contracts"]
                continue
            j = pos["exp_i"]
            T_rem = max((idx[j] - idx[i]).days, 0) / 365.0
            val_short = bs_price(S_t, pos["K_short"], T_rem, R_RATE, sig_t, opt_type)
            val_long = bs_price(S_t, pos["K_long"], T_rem, R_RATE, sig_t, opt_type)
            liability = (val_short - val_long) * CONTRACT_MULT
            equity_per_contract = pos["net_credit"] * CONTRACT_MULT - liability
            max_gain = pos["net_credit"] * CONTRACT_MULT
            profit_frac = equity_per_contract / max_gain if max_gain > 0 else -1.0
            hit_target = profit_frac >= profit_target_frac
            expired = i >= j
            if not (hit_target or expired):
                day_pnl_dollars += (equity_per_contract - pos["prev_equity_per_contract"]) * pos["contracts"]
                pos["prev_equity_per_contract"] = equity_per_contract
                continue
            if expired and not hit_target:
                intrinsic_short = max(S_t - pos["K_short"], 0.0) if opt_type == "call" else max(pos["K_short"] - S_t, 0.0)
                intrinsic_long = max(S_t - pos["K_long"], 0.0) if opt_type == "call" else max(pos["K_long"] - S_t, 0.0)
                payoff = intrinsic_short - intrinsic_long
                realized_pnl = pos["net_credit"] * CONTRACT_MULT - payoff * CONTRACT_MULT
            else:
                buy_back_short = val_short * (1.0 + HALF_SPREAD + COMMISSION_PCT)
                sell_long = val_long * (1.0 - HALF_SPREAD - COMMISSION_PCT)
                close_liability = (buy_back_short - sell_long) * CONTRACT_MULT
                realized_pnl = pos["net_credit"] * CONTRACT_MULT - close_liability
            day_pnl_dollars += (realized_pnl - pos["prev_equity_per_contract"]) * pos["contracts"]
            trades.append(dict(opt_type=opt_type, entry_date=pos["entry_date"], exit_date=idx[i],
                                days_held=(idx[i] - pos["entry_date"]).days,
                                realized_pnl=realized_pnl, win=bool(realized_pnl > 0)))
            open_pos[opt_type] = None
        capital_prev = capital
        capital += day_pnl_dollars
        equity.iloc[i] = capital
        daily_ret.iloc[i] = day_pnl_dollars / capital_prev if capital_prev > 0 else 0.0
    return pd.DataFrame(trades), daily_ret, equity


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    df = load_data()
    iv_rank = df["vix"].rolling(IV_LOOKBACK, min_periods=IV_LOOKBACK).rank(pct=True)
    eligible = iv_rank.notna()

    results = []
    for pt in PROFIT_TARGETS:
        tr, ret, eq = run_combined_book_pt(df, eligible, DELTA, DTE, pt)
        sr = sharpe(ret, BARS_PER_YEAR)
        mdd = max_drawdown(eq / START_CAPITAL)
        wdm = worst_day_month(ret)
        yr, top_yr = year_stats(ret)
        tot = eq.iloc[-1] / START_CAPITAL - 1.0
        m = dict(label=f"delta{DELTA:.2f}_dte{DTE}_pt{int(pt*100)}", profit_target=pt,
                 n_trades=len(tr), win_rate=float(tr["win"].mean()) if len(tr) else float("nan"),
                 sharpe=sr, max_dd=mdd, total_return=tot,
                 worst_day=wdm["worst_day"], worst_month=wdm["worst_month"], top_year_share=top_yr)
        results.append(m)
        print(f"--- {m['label']} ---")
        print(f"  n={m['n_trades']}  win={m['win_rate']*100:.1f}%  Sharpe={sr:+.3f}  maxDD={mdd*100:.1f}%  "
              f"ret={tot*100:+.1f}%  worst_day={wdm['worst_day']*100:.2f}%  worst_month={wdm['worst_month']*100:.2f}%  "
              f"topyr={top_yr*100:.1f}%\n")

    new_rows = [m for m in results if m["profit_target"] != 0.50]
    sharpes = [m["sharpe"] for m in new_rows]
    print(f"=== Deflated Sharpe (structural pool: family=credit_spread_joint_reopt, N={len(sharpes)} new trials) ===")
    for m in new_rows:
        d = deflated_sharpe(m["sharpe"], sharpes, n_obs=m["n_trades"], ann_factor=BARS_PER_YEAR)
        print(f"  {m['label']}: Sharpe={m['sharpe']:+.3f}  DSR={d['dsr']:.4f}  pool_n={d['pool_n']}")

    out = RESULTS / "credit_spread_joint_reopt.csv"
    pd.DataFrame(results).to_csv(out, index=False)
    print(f"\nSaved {out}")
    print(f"Trial count: {NEW_TRIALS} new. Cumulative N={PRIOR_TRIALS} -> {PRIOR_TRIALS + NEW_TRIALS}")


if __name__ == "__main__":
    main()
