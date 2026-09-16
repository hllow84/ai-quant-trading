"""
us30_macross_breakout_combined_book.py — US30 MACROSS + US30 BREAKOUT
combined book (§48), a fourth combined-book pairing, on a NEW
diversification axis vs §44/§47: SAME instrument, DIFFERENT signal
families (trend-continuation macross vs breakout-retest), rather than
same family across two instruments.

§44 tested same-family/cross-instrument (NAS100+US30 macross) and found a
genuine diversification win (both legs strong, near-zero correlation,
combined beat both legs). §47 tested the same axis on breakout (NAS100+
US30) and found the OPPOSITE — one leg (NAS100) was materially weaker, and
equal-weighting just diluted the strong US30 leg. This section asks a
different question: does diversifying across SIGNAL FAMILIES on the SAME
instrument help, when both families are independently strong there?

Both US30 legs individually beat US30 buy-and-hold (Sharpe +0.547, maxDD
37.0%, §43):
- US30 macross (§43): fast=10/slow=30/ema_trend=100/k_atr=2.5/R=1.0/H=72,
  Sharpe +0.999 standalone, maxDD 6.1%.
- US30 breakout (§45): N=20/k_atr=4.0/R=0.25/H=20, Sharpe +1.684
  standalone, maxDD 4.1%.

Mechanism (a priori): a trend-continuation crossover and a breakout-retest
entry are structurally different triggers (moving-average state vs a
price level break) even on the same instrument/timeframe, so a priori
there is a real reason to expect lower correlation than, say, two
macross variants would have on the same instrument — worth checking
directly rather than assuming.

Method: identical to §44/§47 — both legs run with their own unchanged
session-best params/functions, same cost model/H4 resample/
strictly_after=True, daily log-returns aligned on the union of trading
days (missing days = flat), combined at fixed 50/50 weight.

Zero new trials — a portfolio-construction check on two already-scored
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
DATA = _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv"

LEGS = {
    "US30_macross": dict(
        fn=ma_cross,
        params=dict(fast=10, slow=30, ema_trend=100, k_atr=2.5, R=1.0, H=72),
    ),
    "US30_breakout": dict(
        fn=breakout_retest,
        params=dict(N=20, k_atr=4.0, R=0.25, H=20),
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
    print(f"US30 H4 bars: {len(m):,}, {m.index[0]} -> {m.index[-1]}\n")

    daily_rets = {}
    standalone = {}
    for name, cfg in LEGS.items():
        dr, sh, dd = run_leg(name, cfg, m, daily_index)
        daily_rets[name] = dr
        standalone[name] = dict(sharpe=sh, max_dd=dd)

    idx = daily_rets["US30_macross"].index.union(daily_rets["US30_breakout"].index)
    macross = daily_rets["US30_macross"].reindex(idx, fill_value=0.0)
    breakout = daily_rets["US30_breakout"].reindex(idx, fill_value=0.0)

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

    print("=== Combined book: 50% US30 macross + 50% US30 breakout ===")
    print(f"  Combined Sharpe: {combined_sharpe:+.3f}")
    print(f"  Combined maxDD:  {combined_dd*100:.1f}%")
    print(f"  Years positive:  {n_pos}/{n_years} (worst: {worst_year_label} {worst_year*100:+.1f}%)")
    print()
    print("=== Comparison ===")
    print(f"  US30 macross standalone:  Sharpe {standalone['US30_macross']['sharpe']:+.3f}, maxDD {standalone['US30_macross']['max_dd']*100:.1f}%")
    print(f"  US30 breakout standalone: Sharpe {standalone['US30_breakout']['sharpe']:+.3f}, maxDD {standalone['US30_breakout']['max_dd']*100:.1f}%")
    print(f"  50/50 combined:           Sharpe {combined_sharpe:+.3f}, maxDD {combined_dd*100:.1f}%")
    naive_avg_sharpe = 0.5 * (standalone["US30_macross"]["sharpe"] + standalone["US30_breakout"]["sharpe"])
    naive_avg_dd = 0.5 * (standalone["US30_macross"]["max_dd"] + standalone["US30_breakout"]["max_dd"])
    print(f"  (naive average of standalone Sharpes: {naive_avg_sharpe:+.3f}; "
          f"naive average of standalone maxDDs: {naive_avg_dd*100:.1f}%)")
    print(f"  (100% US30-breakout-only, for reference: Sharpe {standalone['US30_breakout']['sharpe']:+.3f}, "
          f"maxDD {standalone['US30_breakout']['max_dd']*100:.1f}%)")

    out_df = pd.DataFrame({
        "date": idx,
        "us30_macross_ret": macross.values,
        "us30_breakout_ret": breakout.values,
        "combined_ret": combined.values,
    })
    out = RESULTS / "us30_macross_breakout_combined_book.csv"
    out_df.to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio-construction check on two already-scored "
          "session-best configs, no parameter search). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
