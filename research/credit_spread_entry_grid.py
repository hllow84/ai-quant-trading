"""
credit_spread_entry_grid.py — credit-spread SPY: ENTRY (delta target, DTE)
grid, built on top of the already-established best exit (§38: 2pct width,
50% early profit-take) and best structure (§27: defined-risk, protective
long leg). Width and exit are HELD FIXED at their already-proven-best
values (a staged, resource-efficient design, stated explicitly — not a full
joint delta x DTE x width x exit grid, which would be 3x3x2x3=54 cells for
little extra insight once exit/width are already settled) — only entry
(delta, DTE) is new here.

WHY THIS IS GENUINELY NEW (checked against the log first): TARGET_DELTA
(0.10) and DTE_DAYS (37) have been FIXED constants, imported unchanged from
research/delta10_iv_filter.py, across every credit-spread section in this
project (§20, §26, §27, §38) — chosen originally to match Ultimate
Investor's live scanner defaults (TARGET_DELTA=0.10, 30-45 DTE), never
swept as a free parameter. Confirmed by grep: no script in this repo calls
solve_delta10_strike with a non-default target_delta, and DTE_DAYS is never
overridden.

MECHANISM for each (stated a priori):
  Delta controls the probability the short leg finishes ITM — a classic
  risk/reward dial. LOWER delta (0.05) = further OTM = smaller premium but
  higher win rate and smaller average loss when wrong. HIGHER delta (0.16,
  the other common convention besides 0.10) = closer to the money = more
  premium collected per trade but more frequent, larger losses. There is no
  a priori reason to expect 0.10 (chosen only because it matched an
  external app's default, not because it was found best here) is optimal
  for THIS backtest's specific cost/vol regime.

  DTE controls the theta/gamma tradeoff. SHORTER DTE (21, the widely-cited
  "sweet spot" in the same TastyTrade-style literature that motivated §38's
  50%-early-exit rule) sits in the steepest part of the theta decay curve
  relative to gamma risk. LONGER DTE (45, Ultimate Investor's own stated
  upper bound) collects more total premium per trade but ties up capital
  longer and sits further from the steep decay zone.

GRID (a priori): target_delta in {0.05, 0.10, 0.16} x dte_days in
{21, 37, 45} = 9 cells; (0.10, 37) reproduces the known §38 best cell
(2pct/early50%) exactly and is not counted as new. 8 new trials.
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
    load_data, bs_price, solve_delta10_strike, R_RATE, IV_LOOKBACK,
    HALF_SPREAD, COMMISSION_PCT, CONTRACT_MULT,
    CATASTROPHIC_SINGLE_DAY, CATASTROPHIC_SINGLE_MONTH, BARS_PER_YEAR,
)
from research.credit_spread_iv_filter import worst_day_month, year_stats

RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)

WIDTH_PCT = 0.02          # §27/§38-best fixed width
PROFIT_TARGET_FRAC = 0.50  # §38-best fixed early-exit threshold
DELTAS = (0.05, 0.10, 0.16)
DTES = (21, 37, 45)
START_CAPITAL = 100_000.0
RISK_PCT = 0.02
PRIOR_TRIALS = 1384
NEW_TRIALS = 8

OUT_CSV = RESULTS / "credit_spread_entry_grid.csv"


def _try_open_param(idx, i, decision_i, spy, vix, opt_type, eligible, capital,
                     target_delta: float, dte_days: int) -> dict | None:
    if not (bool(eligible.iloc[decision_i]) and np.isfinite(vix[i])):
        return None
    target_exp = idx[i] + pd.Timedelta(days=dte_days)
    j = idx.searchsorted(target_exp, side="right") - 1
    if not (j > i and j < len(idx)):
        return None
    S0, sig0 = float(spy[i]), float(vix[i])
    T0 = max((idx[j] - idx[i]).days, 1) / 365.0
    width_dollars = WIDTH_PCT * S0

    K_short = solve_delta10_strike(S0, T0, R_RATE, sig0, opt_type, target_delta=target_delta)
    K_long = (K_short - width_dollars) if opt_type == "put" else (K_short + width_dollars)
    actual_width = abs(K_short - K_long)

    short_mid = bs_price(S0, K_short, T0, R_RATE, sig0, opt_type)
    long_mid = bs_price(S0, K_long, T0, R_RATE, sig0, opt_type)
    if short_mid <= 1e-6:
        return {"rejected": "short leg unpriced"}

    short_recv = short_mid * (1.0 - HALF_SPREAD - COMMISSION_PCT)
    long_paid = long_mid * (1.0 + HALF_SPREAD + COMMISSION_PCT)
    net_credit = short_recv - long_paid
    gross_credit = short_mid - long_mid

    if net_credit <= 0:
        return {"rejected": "no net credit at this width"}
    if net_credit >= actual_width:
        return {"rejected": "credit exceeds width (bad quote/pricing)"}

    max_loss = (actual_width - net_credit) * CONTRACT_MULT
    contracts = (RISK_PCT * capital) / max_loss
    entry_equity_per_contract = net_credit * CONTRACT_MULT - gross_credit * CONTRACT_MULT

    return dict(
        exp_i=j, S0=S0, K_short=K_short, K_long=K_long, opt_type=opt_type,
        entry_date=idx[i], exp_date=idx[j], width=actual_width,
        net_credit=net_credit, gross_credit=gross_credit, max_loss=max_loss, contracts=contracts,
        prev_equity_per_contract=entry_equity_per_contract,
        entry_equity_per_contract=entry_equity_per_contract,
    )


def run_combined_book(df: pd.DataFrame, eligible: pd.Series, target_delta: float, dte_days: int):
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

            hit_target = profit_frac >= PROFIT_TARGET_FRAC
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
            trades.append(dict(
                opt_type=opt_type, entry_date=pos["entry_date"], exit_date=idx[i],
                days_held=(idx[i] - pos["entry_date"]).days,
                realized_pnl=realized_pnl, win=bool(realized_pnl > 0),
            ))
            open_pos[opt_type] = None

        capital_prev = capital
        capital += day_pnl_dollars
        equity.iloc[i] = capital
        daily_ret.iloc[i] = day_pnl_dollars / capital_prev if capital_prev > 0 else 0.0

    tr = pd.DataFrame(trades)
    return tr, daily_ret, equity


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    df = load_data()
    iv_rank = df["vix"].rolling(IV_LOOKBACK, min_periods=IV_LOOKBACK).rank(pct=True)
    eligible = iv_rank.notna()  # UNFILTERED, same convention as §38
    print(f"Data: {df.index[0].date()} -> {df.index[-1].date()}, {len(df)} rows\n")

    results = []
    for delta in DELTAS:
        for dte in DTES:
            is_baseline = (delta == 0.10 and dte == 37)
            tr, ret, eq = run_combined_book(df, eligible, delta, dte)
            sr = sharpe(ret, BARS_PER_YEAR)
            mdd = max_drawdown(eq / START_CAPITAL)
            wdm = worst_day_month(ret)
            yr, top_yr = year_stats(ret)
            total_ret = eq.iloc[-1] / START_CAPITAL - 1.0
            label = f"delta{delta:.2f}_dte{dte}" + (" [BASELINE=§38-best, repro-only]" if is_baseline else "")
            m = dict(label=label, delta=delta, dte=dte, is_baseline=is_baseline,
                     n_trades=len(tr), win_rate=float(tr["win"].mean()) if len(tr) else float("nan"),
                     avg_days_held=float(tr["days_held"].mean()) if len(tr) else float("nan"),
                     sharpe=sr, max_dd=mdd, total_return=total_ret,
                     worst_day=wdm["worst_day"], worst_month=wdm["worst_month"],
                     top_year_share=top_yr)
            results.append(m)
            print(f"--- {label} ---")
            print(f"  n_trades={m['n_trades']}  win_rate={m['win_rate']*100:.1f}%  "
                  f"avg_days_held={m['avg_days_held']:.1f}")
            print(f"  Sharpe={sr:+.3f}  maxDD={mdd*100:.1f}%  total_return={total_ret*100:+.1f}%  "
                  f"worst_day={wdm['worst_day']*100:.2f}%  worst_month={wdm['worst_month']*100:.2f}%  "
                  f"top_year_share={top_yr*100:.1f}%\n")

    new_rows = [m for m in results if not m["is_baseline"]]
    sharpes = [m["sharpe"] for m in new_rows]
    print(f"=== Deflated Sharpe (structural pool: family=credit_spread_entry_grid, N={len(sharpes)} new trials) ===")
    for m in new_rows:
        d = deflated_sharpe(m["sharpe"], sharpes, n_obs=m["n_trades"], ann_factor=BARS_PER_YEAR)
        print(f"  {m['label']}: Sharpe={m['sharpe']:+.3f}  DSR={d['dsr']:.4f}  pool_n={d['pool_n']}")

    baseline = [m for m in results if m["is_baseline"]][0]
    print(f"\nBaseline repro (delta=0.10, dte=37, §38-best exit/width): Sharpe={baseline['sharpe']:+.3f}  "
          f"(on-record §38: Sharpe +1.319)")

    out = pd.DataFrame(results)
    out.to_csv(OUT_CSV, index=False)
    print(f"\nSaved {OUT_CSV}")
    print(f"Trial count: {NEW_TRIALS} new. Cumulative N={PRIOR_TRIALS} -> {PRIOR_TRIALS + NEW_TRIALS}")


if __name__ == "__main__":
    main()
