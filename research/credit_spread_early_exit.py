"""
credit_spread_early_exit.py — TP refinement on §27's defined-risk credit
spread (research/credit_spread_iv_filter.py): close the position EARLY once
a stated fraction of max potential profit (the net credit received) has been
captured, instead of always holding to expiration (§27's only exit rule).

MECHANISM (stated a priori): real-world options-selling practice — closing a
credit spread at ~50% of max profit rather than riding it to expiration is
one of the most widely cited, independently studied rules in this literature
(TastyTrade's own published backtest research; the logic is that most of a
short option's theta decay is captured well before expiration, while the
LAST portion of premium is the most exposed to gap/tail risk for the least
incremental reward — giving it back on one bad day is a worse trade than
banking most of the profit early and redeploying capital). This is a
genuinely untested exit dimension in this project: §26/§27 only varied the
ENTRY filter (IV-rank) and the structural WIDTH (1%/2%) — no exit besides
"hold to expiration" has ever been coded (verified: credit_spread_iv_filter.
run_combined_book's only close condition is `if i >= j: # expired today`).

DESIGN: reuses §27's `_try_open` (per-contract candidate construction) and
constants UNCHANGED — only the close condition inside the daily loop is new.
A position closes on the FIRST day (after entry) that its unrealized gain
(entry net credit minus current mark-to-market liability) reaches
`profit_target_frac` of the maximum possible gain (the net credit itself),
OR at expiration if that threshold is never reached — whichever comes first.
Early closes pay a REAL closing cost: crossing the spread again on both legs
(buy back the short at its ask, sell the long at its bid), same HALF_SPREAD
+ COMMISSION_PCT model as entry — not free, stated explicitly, since a real
early close is a real additional transaction.

GRID (a priori): profit_target_frac in {0.25, 0.50, 0.75} (25%/50%/75% of
max credit — 50% is the most commonly cited rule; 25%/75% bracket it as a
genuine sensitivity check, not cherry-picked) x width in {1%, 2%}. UNFILTERED
only — §26 and §27 BOTH already independently found the IV-rank filter loses
to unfiltered on Sharpe/DSR/total-return in every single cell tested (8/8
cells across the two sections); re-testing the filter a third time on top of
a new exit rule would not be a genuinely new question, so it is not repeated
here. 6 configs total.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.dsr import deflated_sharpe
from research.metrics import sharpe, max_drawdown, profit_factor
from research.delta10_iv_filter import (
    load_data, bs_price, HALF_SPREAD, COMMISSION_PCT, CONTRACT_MULT,
    CATASTROPHIC_SINGLE_DAY, CATASTROPHIC_SINGLE_MONTH, BARS_PER_YEAR, R_RATE,
    IV_LOOKBACK,
)
from research.credit_spread_iv_filter import _try_open, worst_day_month, year_stats, bh_spy

RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)

WIDTH_PCTS = {"1pct": 0.01, "2pct": 0.02}
PROFIT_TARGETS = (0.25, 0.50, 0.75)
START_CAPITAL = 100_000.0
RISK_PCT = 0.02
PRIOR_TRIALS = 1373  # §37 (2026-09-15) is the latest prior cumulative count
NEW_TRIALS = 6        # 3 profit targets x 2 widths, unfiltered only

OUT_CSV = RESULTS / "credit_spread_early_exit.csv"
OUT_TRADES_CSV = RESULTS / "credit_spread_early_exit_trades.csv"


def run_combined_book_early_exit(df: pd.DataFrame, eligible: pd.Series,
                                  group_label: str, width_pct: float,
                                  profit_target_frac: float):
    """Same shared-capital, put+call book as §27's run_combined_book, with one
    new close condition: profit_target_frac of max credit reached -> close
    TODAY at the current mark, paying a real round-trip closing cost."""
    idx = df.index
    spy = df["spy"].to_numpy()
    vix = df["vix"].to_numpy() / 100.0
    n = len(df)

    capital = START_CAPITAL
    equity = pd.Series(START_CAPITAL, index=idx)
    daily_ret = pd.Series(0.0, index=idx)
    open_pos = {"put": None, "call": None}
    trades, rejected = [], []

    for i in range(1, n):
        decision_i = i - 1
        day_pnl_dollars = 0.0
        S_t, sig_t = float(spy[i]), float(vix[i])

        for opt_type in ("put", "call"):
            pos = open_pos[opt_type]
            if pos is None:
                cand = _try_open(idx, i, decision_i, spy, vix, opt_type, width_pct, eligible, capital)
                if cand is None:
                    continue
                if "rejected" in cand:
                    rejected.append((idx[i], opt_type, cand["rejected"]))
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

            max_gain_per_contract = pos["net_credit"] * CONTRACT_MULT
            profit_frac = equity_per_contract / max_gain_per_contract if max_gain_per_contract > 0 else -1.0
            # pos is only ever inspected here on a day STRICTLY AFTER it was
            # opened (the opening branch above `continue`s before reaching
            # this code on the entry day itself), so no same-day-close check
            # is needed.
            hit_target = profit_frac >= profit_target_frac
            expired = i >= j

            if not (hit_target or expired):
                day_pnl_dollars += (equity_per_contract - pos["prev_equity_per_contract"]) * pos["contracts"]
                pos["prev_equity_per_contract"] = equity_per_contract
                continue

            if expired and not hit_target:
                # same as §27: settle to intrinsic, no extra closing transaction cost
                intrinsic_short = max(S_t - pos["K_short"], 0.0) if opt_type == "call" else max(pos["K_short"] - S_t, 0.0)
                intrinsic_long = max(S_t - pos["K_long"], 0.0) if opt_type == "call" else max(pos["K_long"] - S_t, 0.0)
                payoff = intrinsic_short - intrinsic_long
                realized_pnl = pos["net_credit"] * CONTRACT_MULT - payoff * CONTRACT_MULT
                exit_reason = "expired"
            else:
                # EARLY CLOSE: cross the spread again on both legs (real cost)
                buy_back_short = val_short * (1.0 + HALF_SPREAD + COMMISSION_PCT)
                sell_long = val_long * (1.0 - HALF_SPREAD - COMMISSION_PCT)
                close_liability = (buy_back_short - sell_long) * CONTRACT_MULT
                realized_pnl = pos["net_credit"] * CONTRACT_MULT - close_liability
                exit_reason = f"early_{profit_target_frac:.0%}"

            day_pnl_dollars += (realized_pnl - pos["prev_equity_per_contract"]) * pos["contracts"]

            loss_amount = max(-realized_pnl, 0.0)
            trades.append(dict(
                opt_type=opt_type, entry_date=pos["entry_date"], exp_date=pos["exp_date"],
                exit_date=idx[i], exit_reason=exit_reason,
                days_held=(idx[i] - pos["entry_date"]).days,
                dte_at_entry=(pos["exp_date"] - pos["entry_date"]).days,
                width=pos["width"], width_pct=pos["width_pct"], contracts=pos["contracts"],
                net_credit=pos["net_credit"] * CONTRACT_MULT,
                realized_pnl=realized_pnl, realized_pnl_sized=realized_pnl * pos["contracts"],
                ret_on_credit=realized_pnl / (pos["net_credit"] * CONTRACT_MULT),
                ret_on_max_loss=realized_pnl / pos["max_loss"],
                win=bool(realized_pnl > 0), loss_amount=loss_amount,
            ))
            open_pos[opt_type] = None

        capital_prev = capital
        capital += day_pnl_dollars
        equity.iloc[i] = capital
        daily_ret.iloc[i] = day_pnl_dollars / capital_prev if capital_prev > 0 else 0.0

    tr = pd.DataFrame(trades)
    rej = pd.DataFrame(rejected, columns=["date", "opt_type", "reason"]) if rejected else pd.DataFrame(columns=["date", "opt_type", "reason"])
    return tr, daily_ret, equity, rej


def cell_metrics(pooled_ret: pd.Series, equity: pd.Series, pooled_trades: pd.DataFrame, label: str) -> dict:
    active = pooled_ret[pooled_ret != 0.0]
    sr = sharpe(pooled_ret, BARS_PER_YEAR)
    mdd = max_drawdown(equity / START_CAPITAL)
    wdm = worst_day_month(pooled_ret)
    yr, top_yr = year_stats(pooled_ret)
    total_ret = equity.iloc[-1] / START_CAPITAL - 1.0
    kill_tail = (wdm["worst_day"] < CATASTROPHIC_SINGLE_DAY) or (wdm["worst_month"] < CATASTROPHIC_SINGLE_MONTH)
    early_pct = (pooled_trades["exit_reason"].str.startswith("early").mean() * 100
                 if len(pooled_trades) else 0.0)
    avg_days_held = float(pooled_trades["days_held"].mean()) if len(pooled_trades) else float("nan")
    avg_dte = float(pooled_trades["dte_at_entry"].mean()) if len(pooled_trades) else float("nan")
    return dict(
        label=label, n_trades=len(pooled_trades),
        win_rate=float(pooled_trades["win"].mean()) if len(pooled_trades) else float("nan"),
        pct_early_close=early_pct, avg_days_held=avg_days_held, avg_dte_at_entry=avg_dte,
        sharpe=sr, max_dd=mdd, total_return=total_ret,
        worst_day=wdm["worst_day"], worst_day_date=str(wdm["worst_day_date"]),
        worst_month=wdm["worst_month"], worst_month_date=wdm["worst_month_date"],
        kill_tail=kill_tail, top_year_share=top_yr,
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    df = load_data()
    # UNFILTERED, matching §27's exact definition (still requires the
    # IV_LOOKBACK warm-up so the eligible window is identical to §27's
    # control group, not an unconditional True from day 1).
    iv_rank = df["vix"].rolling(IV_LOOKBACK, min_periods=IV_LOOKBACK).rank(pct=True)
    eligible_all = iv_rank.notna()

    print(f"Data: {df.index[0].date()} -> {df.index[-1].date()}, {len(df)} rows\n")

    results = []
    for width_name, width_pct in WIDTH_PCTS.items():
        for pt in PROFIT_TARGETS:
            label = f"{width_name}_UNFILTERED_early{int(pt*100)}pct"
            tr, ret, eq, rej = run_combined_book_early_exit(df, eligible_all, label, width_pct, pt)
            m = cell_metrics(ret, eq, tr, label)
            results.append(m)
            tr["cell"] = label
            tr.to_csv(RESULTS / f"credit_spread_early_exit_trades_{label}.csv", index=False)
            print(f"--- {label} ---")
            print(f"  n_trades={m['n_trades']}  win_rate={m['win_rate']*100:.1f}%  "
                  f"early_close={m['pct_early_close']:.1f}%  avg_days_held={m['avg_days_held']:.1f} "
                  f"(of avg {m['avg_dte_at_entry']:.0f} DTE at entry)")
            print(f"  Sharpe={m['sharpe']:+.3f}  maxDD={m['max_dd']*100:.1f}%  "
                  f"total_return={m['total_return']*100:+.1f}%")
            print(f"  worst_day={m['worst_day']*100:.2f}% ({m['worst_day_date']})  "
                  f"worst_month={m['worst_month']*100:.2f}% ({m['worst_month_date']})  "
                  f"kill_tail={m['kill_tail']}\n")

    # §27 baseline (hold-to-expiration, same widths, unfiltered) for direct comparison
    print("=" * 80)
    print("§27 baseline (hold-to-expiration, unfiltered) for reference:")
    print("  1pct UNFILTERED: Sharpe +1.04, DSR 0.272, total_return +94%")
    print("  2pct UNFILTERED: Sharpe +1.15, DSR 0.490, total_return +92%")
    print("=" * 80)

    sharpes = [m["sharpe"] for m in results]
    print(f"\n=== Deflated Sharpe (structural pool: family=credit_spread_early_exit, N={len(results)} trials) ===")
    for m, sr in zip(results, sharpes):
        d = deflated_sharpe(sr, sharpes, n_obs=m["n_trades"], ann_factor=BARS_PER_YEAR)
        print(f"  {m['label']}: Sharpe={sr:+.3f}  DSR={d['dsr']:.4f}  pool_n={d['pool_n']}")

    out = pd.DataFrame(results)
    out.to_csv(OUT_CSV, index=False)
    print(f"\nSaved {OUT_CSV}")
    print(f"Trial count: {NEW_TRIALS} new. Cumulative N={PRIOR_TRIALS} -> {PRIOR_TRIALS + NEW_TRIALS}")


if __name__ == "__main__":
    main()
