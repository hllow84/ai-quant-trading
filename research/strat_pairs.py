#!/usr/bin/env python3
"""
STRATEGY 1 -- PAIRS TRADING / STATISTICAL ARBITRAGE, daily bars.

PAIRS CHOSEN, stated and justified before running:
  1. GLD vs SLV (gold vs silver ETFs) -- the textbook commodities pairs
     trade. Both are precious metals with a well-documented common demand
     driver (real-rate/inflation-hedge flows, dollar strength); the
     gold/silver ratio is one of the most widely followed cross-asset
     spreads in commodities trading. Daily adjusted close, both from
     yfinance (2004-2026 GLD, 2006-2026 SLV -- overlap from 2006-04-28).
  2. NAS100 vs US30 (Nasdaq-100 vs Dow Jones Industrial Average CFDs) --
     both are large-cap US equity indices sharing the same macro driver
     (US growth/rate expectations); daily correlation of returns over
     2013-2025 measured below (not assumed) before treating them as a pair.

METHOD, stated before running, no re-tuning:
  log_ratio = log(price_A) - log(price_B) (a log-spread, scale-invariant --
     more standard than a raw price ratio when the two legs' price levels
     differ by orders of magnitude, as GLD ~$100-300 vs SLV ~$15-45).
  ROLL_WINDOW = 60 trading days (task's stated example), causal (rolling
     mean/std computed on trailing 60 days, EXCLUDING today via .shift(1)).
  z = (log_ratio - roll_mean) / roll_std.
  ENTRY: |z| >= N, N in {1.5, 2.0} (task's stated values, BOTH tested,
     reported separately -- not picked after seeing which works).
     z >= +N  -> spread too wide -> SHORT A, LONG B (bet on convergence).
     z <= -N  -> spread too narrow -> LONG A, SHORT B.
  EXIT: |z| <= 0.25 (mean-reversion achieved, a token near-zero band, not
     tuned) OR a stated stop at |z| >= N + 2.0 (spread widens further
     instead of reverting -- a catastrophic-divergence stop).
  SIZING: dollar-neutral -- equal DOLLAR exposure long and short (not equal
     share count), rebalanced only at entry (not re-hedged daily), which is
     the standard simplification for a spread trade of this kind. Position
     return = 0.5*(ret_A - ret_B) if short-A/long-B, or 0.5*(ret_B - ret_A)
     if long-A/short-B (the 0.5 keeps gross exposure at 1x equity, matching
     a fully-collateralized long/short pair, not 2x).

LOOK-AHEAD: the rolling mean/std of log_ratio is shifted by 1 day before
comparison against TODAY's z, so today's own price never enters its own
entry threshold; the resulting position is applied to TOMORROW's return via
the standard 1-day-forward convention used throughout this project.

COSTS: GLD/SLV each carry the ETF assumption (2 bps round-turn per leg,
stated in six_strategies_engine.py); NAS100/US30 each carry the project's
real index cost model. Cost charged on BOTH legs whenever the position
(or its direction) changes.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.six_strategies_engine import (
    load_daily, drawdown_with_recovery, year_table, top_year_concentration,
    START_CAP, BARS_PER_YEAR,
)
from research.metrics import sharpe, max_drawdown, profit_factor

ROLL_WINDOW = 60
EXIT_BAND = 0.25
STOP_EXTRA = 2.0
NS = [1.5, 2.0]

PAIRS = [("GLD", "SLV"), ("NAS100", "US30")]


def build_pair_frame(a: str, b: str):
    da, db = load_daily(a), load_daily(b)
    idx = da.index.intersection(db.index)
    df = pd.DataFrame(index=idx)
    df["close_a"] = da["close"].reindex(idx)
    df["close_b"] = db["close"].reindex(idx)
    df["cost_a"] = da["spread_bps"].reindex(idx).fillna(da["spread_bps"].median())
    df["cost_b"] = db["spread_bps"].reindex(idx).fillna(db["spread_bps"].median())
    return df.dropna()


def run_pair(df: pd.DataFrame, N: float) -> dict:
    log_ratio = np.log(df["close_a"]) - np.log(df["close_b"])
    roll_mean = log_ratio.rolling(ROLL_WINDOW).mean().shift(1)
    roll_std = log_ratio.rolling(ROLL_WINDOW).std().shift(1)
    z = (log_ratio - roll_mean) / roll_std   # today's z vs yesterday's completed stats

    ret_a = df["close_a"].pct_change().fillna(0.0)
    ret_b = df["close_b"].pct_change().fillna(0.0)

    pos = pd.Series(0, index=df.index, dtype=int)  # +1 = long A/short B, -1 = short A/long B
    state = 0
    for i in range(len(df)):
        zv = z.iloc[i]
        if not np.isfinite(zv):
            pos.iloc[i] = 0
            continue
        if state == 0:
            if zv >= N:
                state = -1
            elif zv <= -N:
                state = 1
        else:
            if abs(zv) <= EXIT_BAND or abs(zv) >= N + STOP_EXTRA:
                state = 0
        pos.iloc[i] = state

    pos_prev = pos.shift(1).fillna(0.0)
    changed = (pos != pos_prev)
    round_turn_cost = ((df["cost_a"] + df["cost_b"]) / 2.0 / 1e4) * changed.astype(float)
    strat_ret = 0.5 * pos_prev * (ret_a - ret_b) - round_turn_cost
    equity = START_CAP * (1.0 + strat_ret).cumprod()
    return dict(daily_ret=strat_ret, equity=equity, n_changes=int(changed.sum()))


def report(label: str, df: pd.DataFrame, N: float) -> dict:
    out = run_pair(df, N)
    daily_ret, equity = out["daily_ret"], out["equity"]
    dd = drawdown_with_recovery(equity)
    yt = year_table(daily_ret, equity)
    conc = top_year_concentration(yt)
    end_bal = float(equity.iloc[-1])

    W = 116
    print("=" * W)
    print(f"  {label}  (N={N})")
    print("=" * W)
    for _, row in yt.iterrows():
        print(f"  {int(row['year']):<6} {row['start_equity']:>14,.0f} {row['end_equity']:>14,.0f} "
              f"{row['year_return_pct']:>+13.1f}%")
    total_ret = end_bal / START_CAP - 1
    print(f"\n  FULL-PERIOD: ${START_CAP:,.0f} -> ${end_bal:,.0f} ({total_ret*100:+.1f}%)   "
          f"Sharpe {sharpe(daily_ret, BARS_PER_YEAR):+.2f}   net PF {profit_factor(daily_ret):.3f}   "
          f"position changes {out['n_changes']}")
    print(f"  MAX DRAWDOWN: {dd['max_dd']*100:.1f}%  (peak {dd['peak_date'].date()}, trough {dd['trough_date'].date()}"
          + (f", recovered {dd['recovery_date'].date()})" if dd["recovery_date"] is not None else ", NOT recovered)"))
    conc_str = f"{conc*100:.0f}%" if np.isfinite(conc) else "n/a (total<=0)"
    print(f"  TOP-YEAR CONCENTRATION: {conc_str}  -> {'FLAG: concentrated' if (np.isfinite(conc) and conc>0.60) else 'not concentrated'}")
    print()
    return dict(label=label, N=N, end_balance=end_bal, total_return=total_ret,
                sharpe=sharpe(daily_ret, BARS_PER_YEAR), max_dd=dd["max_dd"],
                recovery_date=dd["recovery_date"], top_year_conc=conc)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("STRATEGY 1 -- PAIRS TRADING / STATISTICAL ARBITRAGE, 60-day rolling z-score, N in {1.5, 2.0}\n")

    corr = {}
    for a, b in PAIRS:
        df = build_pair_frame(a, b)
        ra, rb = df["close_a"].pct_change().dropna(), df["close_b"].pct_change().dropna()
        c = ra.corr(rb)
        corr[(a, b)] = c
        print(f"[{a} vs {b}] daily return correlation over {df.index[0].date()} -> {df.index[-1].date()}: {c:.3f}")
    print()

    results = []
    for a, b in PAIRS:
        df = build_pair_frame(a, b)
        for N in NS:
            r = report(f"PAIRS: {a} vs {b}", df, N)
            results.append(((a, b), N, r))
    return results, corr


if __name__ == "__main__":
    main()
