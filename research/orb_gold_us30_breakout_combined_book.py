"""
orb_gold_us30_breakout_combined_book.py — ORB gold RETEST (XAUUSD) + US30
BREAKOUT combined book (§49), a fifth combined-book pairing on a THIRD new
diversification axis: cross-ASSET-CLASS (commodity vs equity index),
cross-instrument, cross-family, pairing this project's two single
strongest individual candidates.

§44 tested same-family/cross-instrument (both equity indices).
§47 tested the same axis with a mismatched (weak) leg -- failed.
§48 tested same-instrument/cross-family (both US30) -- worked best so far.
This section asks whether the "both legs must be independently strong"
rule (the one lesson that has survived every prior pairing) also holds
when the two legs come from completely different asset classes with
completely different cost models and data sources (gold spot bid/ask vs
US30 CFD), not just different equity indices.

Legs, both independently strong (both already flagged as this project's
top two pure spot/CFD Sharpes before this section):
- ORB gold RETEST (§39): XAUUSD, retest_tol_frac=0.20/stop_mode='moderate'
  /target=1R, Sharpe +1.488 standalone (full 2017-2025 continuous span),
  beats gold buy-and-hold (+1.18).
- US30 breakout-retest (§45): N=20/k_atr=4.0/R=0.25/H=20, Sharpe +1.684
  standalone, decisively beats US30 buy-and-hold (+0.547).

Mechanism (a priori): gold and a US equity index are driven by
substantially different macro factors (safe-haven/inflation/real-rate
demand vs US corporate earnings/equity risk premium) even before
considering the two strategies' different entry logic (session opening-
range retest vs multi-day-lookback breakout) -- a real a priori reason to
expect very low correlation, the lowest of any pairing tested so far.

Method: identical to §44/§47/§48 -- each leg run with its own unchanged
session-best params/engine (ORB gold reuses
research/orb_retest_entry_stop_grid.py's build_trades() unchanged; US30
breakout reuses strategies/sweep_families.py's breakout_retest()
unchanged), daily log-returns aligned on the union of trading days
(missing days = flat), combined at fixed 50/50 weight. ORB gold's own
continuous span (2017-2025) is longer than US30's CFD data (2018-2025);
the union-alignment handles the mismatch by treating US30 as flat during
gold's extra 2017 stub -- flagged, not hidden.

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
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns, build_position_series,
)
from research.orb_retest_entry_stop_grid import mid_frame, build_trades, FILE_2017, FILE_2018_2025
from strategies.sweep_families import breakout_retest, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
US30_DATA = _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv"


def run_orb_gold_leg():
    m17, spot17 = mid_frame(FILE_2017)
    m18, spot18 = mid_frame(FILE_2018_2025)
    m = pd.concat([m17, m18]).sort_index()
    spot = pd.concat([spot17, spot18]).sort_index()
    daily_index = aggregate_daily(spot).index

    tr = build_trades(m, tol_frac=0.20, stop_mode="moderate")
    pos = build_position_series(tr, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"
    daily_ret = build_daily_returns(tr, daily_index)
    equity = equity_from_returns(daily_ret)
    sh = sharpe(daily_ret, BARS_PER_YEAR)
    dd = max_drawdown(equity)
    print("--- ORB gold RETEST standalone (leg re-run, unchanged params) ---")
    print(f"  n={len(tr)} guard={guard} grossPF={profit_factor(tr['gross_R']):.3f} "
          f"netPF={profit_factor(tr['net_R']):.3f} Sharpe={sh:+.3f} maxDD={dd*100:.1f}%\n")
    return daily_ret, sh, dd


def run_us30_breakout_leg():
    m1 = load_m1_mid(US30_DATA)
    daily_index = aggregate_daily(load_m1_spot(US30_DATA)).index
    m = resample_mid(m1, "4h")
    params = dict(N=20, k_atr=4.0, R=0.25, H=20)
    cands = breakout_retest(m, params, TF_DELTA["H4"])
    for t in cands:
        t["session_end"] = pd.Timestamp(t["session_end"]).tz_convert("UTC") if pd.Timestamp(t["session_end"]).tz else pd.Timestamp(t["session_end"]).tz_localize("UTC")
        t["entry_time"] = pd.Timestamp(t["entry_time"]).tz_convert("UTC") if pd.Timestamp(t["entry_time"]).tz else pd.Timestamp(t["entry_time"]).tz_localize("UTC")
    trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=COST_BPS))
    pos = build_position_series(trades, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"
    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    sh = sharpe(daily_ret, BARS_PER_YEAR)
    dd = max_drawdown(equity)
    print("--- US30 breakout standalone (leg re-run, unchanged params) ---")
    print(f"  n={len(trades)} guard={guard} grossPF={profit_factor(trades['gross_R']):.3f} "
          f"netPF={profit_factor(trades['net_R']):.3f} Sharpe={sh:+.3f} maxDD={dd*100:.1f}%\n")
    return daily_ret, sh, dd


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    gold_ret, gold_sh, gold_dd = run_orb_gold_leg()
    us30_ret, us30_sh, us30_dd = run_us30_breakout_leg()

    idx = gold_ret.index.union(us30_ret.index)
    gold = gold_ret.reindex(idx, fill_value=0.0)
    us30 = us30_ret.reindex(idx, fill_value=0.0)

    corr = float(np.corrcoef(gold.values, us30.values)[0, 1])
    print(f"Correlation of daily log-returns (aligned, {len(idx)} days): {corr:+.3f}\n")

    combined = 0.5 * gold + 0.5 * us30
    combined_equity = equity_from_returns(combined)
    combined_sharpe = sharpe(combined, BARS_PER_YEAR)
    combined_dd = max_drawdown(combined_equity)

    yr_log = combined.groupby(combined.index.year).sum()
    n_years = len(yr_log)
    n_pos = int((yr_log > 0).sum())
    worst_year = float(yr_log.min())
    worst_year_label = int(yr_log.idxmin())

    print("=== Combined book: 50% ORB gold RETEST + 50% US30 breakout ===")
    print(f"  Combined Sharpe: {combined_sharpe:+.3f}")
    print(f"  Combined maxDD:  {combined_dd*100:.1f}%")
    print(f"  Years positive:  {n_pos}/{n_years} (worst: {worst_year_label} {worst_year*100:+.1f}%)")
    print()
    print("=== Comparison ===")
    print(f"  ORB gold standalone:  Sharpe {gold_sh:+.3f}, maxDD {gold_dd*100:.1f}%")
    print(f"  US30 breakout standalone: Sharpe {us30_sh:+.3f}, maxDD {us30_dd*100:.1f}%")
    print(f"  50/50 combined:       Sharpe {combined_sharpe:+.3f}, maxDD {combined_dd*100:.1f}%")
    naive_avg_sharpe = 0.5 * (gold_sh + us30_sh)
    naive_avg_dd = 0.5 * (gold_dd + us30_dd)
    print(f"  (naive average of standalone Sharpes: {naive_avg_sharpe:+.3f}; "
          f"naive average of standalone maxDDs: {naive_avg_dd*100:.1f}%)")

    out_df = pd.DataFrame({
        "date": idx,
        "orb_gold_ret": gold.values,
        "us30_breakout_ret": us30.values,
        "combined_ret": combined.values,
    })
    out = RESULTS / "orb_gold_us30_breakout_combined_book.csv"
    out_df.to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio-construction check on two already-scored "
          "session-best configs, no parameter search). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
