"""
nas100_macross_breakout_combined_book.py — NAS100 MACROSS + NAS100
BREAKOUT combined book (§50), completing the 2x2 same-instrument/cross-
family design started in §48 (US30 macross+breakout). §48 paired two
INDEPENDENTLY STRONG legs (both beat US30 B&H) and got the project's best
combined result. This section pairs one strong leg (NAS100 macross,
Sharpe +0.963, beats NAS100 B&H) with one WEAKER leg that does NOT beat
its own B&H (NAS100 breakout, §46, Sharpe +0.526) -- the same "one leg
weaker" shape as §47's failed NAS100+US30 breakout pairing, but on a
DIFFERENT axis (same instrument/cross-family here, vs cross-instrument/
same-family in §47) and a SMALLER quality gap (0.963 vs 0.526, ratio
~1.8x, vs §47's 1.684 vs 0.526, ratio ~3.2x).

Run to test whether §47's "a weaker leg always drags the book down" rule
is universal, or whether it depends on how large the quality gap actually
is relative to the correlation benefit -- a real, unresolved question
after §47/§48, worth checking directly rather than assuming either
answer.

Method: identical to §44/§47/§48 -- both legs run with their own
unchanged session-best params/functions on the SAME NAS100 H4 data, same
cost model/H4 resample/strictly_after=True, daily log-returns aligned on
the union of trading days, combined at fixed 50/50 weight.

Zero new trials -- a portfolio-construction check on two already-scored
cells, no parameter search. Cumulative trial count (N=1570) unchanged.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, load_m1_mid, resample_mid, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.ftmo_engine import simulate_trades, de_overlap, build_daily_returns, equity_from_returns, build_position_series
from strategies.sweep_families import ma_cross, breakout_retest, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
DATA = _ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv"

LEGS = {
    "NAS100_macross": dict(
        fn=ma_cross,
        params=dict(fast=10, slow=30, ema_trend=200, k_atr=1.0, R=4.0, H=192),
    ),
    "NAS100_breakout": dict(
        fn=breakout_retest,
        params=dict(N=70, k_atr=1.0, R=1.75, H=90),
    ),
}


def run_leg(name, cfg, m, daily_index):
    cands = cfg["fn"](m, cfg["params"], TF_DELTA["H4"])
    for tr in cands:
        tr["session_end"] = pd.Timestamp(tr["session_end"]).tz_convert("UTC") if pd.Timestamp(tr["session_end"]).tz else pd.Timestamp(tr["session_end"]).tz_localize("UTC")
        tr["entry_time"] = pd.Timestamp(tr["entry_time"]).tz_convert("UTC") if pd.Timestamp(tr["entry_time"]).tz else pd.Timestamp(tr["entry_time"]).tz_localize("UTC")
    trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=COST_BPS))
    pos = build_position_series(trades, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"
    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    standalone_sharpe = sharpe(daily_ret, BARS_PER_YEAR)
    standalone_dd = max_drawdown(equity)
    print(f"--- {name} standalone (leg re-run, unchanged params) ---")
    print(f"  n={len(trades)} guard={guard} grossPF={profit_factor(trades['gross_R']):.3f} "
          f"netPF={profit_factor(trades['net_R']):.3f} Sharpe={standalone_sharpe:+.3f} "
          f"maxDD={standalone_dd*100:.1f}%\n")
    return daily_ret, standalone_sharpe, standalone_dd


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    m1 = load_m1_mid(DATA)
    daily_index = aggregate_daily(load_m1_spot(DATA)).index
    m = resample_mid(m1, "4h")
    print(f"NAS100 H4 bars: {len(m):,}, {m.index[0]} -> {m.index[-1]}\n")

    daily_rets, standalone = {}, {}
    for name, cfg in LEGS.items():
        dr, sh, dd = run_leg(name, cfg, m, daily_index)
        daily_rets[name] = dr
        standalone[name] = dict(sharpe=sh, max_dd=dd)

    idx = daily_rets["NAS100_macross"].index.union(daily_rets["NAS100_breakout"].index)
    macross = daily_rets["NAS100_macross"].reindex(idx, fill_value=0.0)
    breakout = daily_rets["NAS100_breakout"].reindex(idx, fill_value=0.0)

    corr = float(np.corrcoef(macross.values, breakout.values)[0, 1])
    print(f"Correlation of daily log-returns (aligned, {len(idx)} days): {corr:+.3f}\n")

    combined = 0.5 * macross + 0.5 * breakout
    combined_equity = equity_from_returns(combined)
    combined_sharpe = sharpe(combined, BARS_PER_YEAR)
    combined_dd = max_drawdown(combined_equity)

    yr_log = combined.groupby(combined.index.year).sum()
    n_years = len(yr_log)
    n_pos = int((yr_log > 0).sum())
    worst_year = float(yr_log.min())
    worst_year_label = int(yr_log.idxmin())

    print("=== Combined book: 50% NAS100 macross + 50% NAS100 breakout ===")
    print(f"  Combined Sharpe: {combined_sharpe:+.3f}")
    print(f"  Combined maxDD:  {combined_dd*100:.1f}%")
    print(f"  Years positive:  {n_pos}/{n_years} (worst: {worst_year_label} {worst_year*100:+.1f}%)")
    print()
    print("=== Comparison ===")
    print(f"  NAS100 macross standalone:  Sharpe {standalone['NAS100_macross']['sharpe']:+.3f}, maxDD {standalone['NAS100_macross']['max_dd']*100:.1f}%")
    print(f"  NAS100 breakout standalone: Sharpe {standalone['NAS100_breakout']['sharpe']:+.3f}, maxDD {standalone['NAS100_breakout']['max_dd']*100:.1f}%")
    print(f"  50/50 combined:             Sharpe {combined_sharpe:+.3f}, maxDD {combined_dd*100:.1f}%")
    naive_avg_sharpe = 0.5 * (standalone["NAS100_macross"]["sharpe"] + standalone["NAS100_breakout"]["sharpe"])
    naive_avg_dd = 0.5 * (standalone["NAS100_macross"]["max_dd"] + standalone["NAS100_breakout"]["max_dd"])
    print(f"  (naive average of standalone Sharpes: {naive_avg_sharpe:+.3f}; "
          f"naive average of standalone maxDDs: {naive_avg_dd*100:.1f}%)")

    out_df = pd.DataFrame({
        "date": idx,
        "nas100_macross_ret": macross.values,
        "nas100_breakout_ret": breakout.values,
        "combined_ret": combined.values,
    })
    out = RESULTS / "nas100_macross_breakout_combined_book.csv"
    out_df.to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio-construction check on two already-scored "
          "session-best configs, no parameter search). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
