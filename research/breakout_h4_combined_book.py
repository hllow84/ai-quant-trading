"""
breakout_h4_combined_book.py — NAS100 + US30 H4 breakout-retest combined
book, same portfolio-construction check as §44 (macross_h4_combined_book.py)
applied to the two §45/§46 breakout-retest legs. Not a new parameter
search: both legs use their already-found session-best configs unchanged.

US30 best (§45): N=20/k_atr=4.0/R=0.25/H=20, Sharpe +1.684 standalone,
DECISIVELY beats US30 buy-and-hold (+0.547).
NAS100 best (§46): N=70/k_atr=1.0/R=1.75/H=90, Sharpe +0.526 standalone,
does NOT beat NAS100 buy-and-hold (+0.842) — a real but weaker, more
concentrated edge (4/8 positive years vs US30's 8/8).

Unlike §44's two macross legs (both genuinely strong, both beating their
own B&H), this pairing combines one strong leg with one weak leg — worth
checking explicitly whether the weak leg still adds diversification value
riding alongside the strong one, or whether it just drags the combined
book down.

Method: identical to §44 — run each leg's own trade simulation unchanged
(same cost model, same H4 resample, same strictly_after=True resolution),
build each leg's own daily log-return series, align on the union of
trading days (missing days = 0 return), combine as 50/50 fixed-weight
daily log-return sum, then rebuild one combined equity curve and combined
Sharpe/maxDD/year table. Correlation of the two daily return series is
reported directly.

This section produces ZERO new backtest trials (no parameter search) — a
portfolio-construction check on two already-scored candidates, so it adds
0 to the project's cumulative trial count (N=1570 unchanged).
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
from strategies.sweep_families import breakout_retest, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)

LEGS = {
    "NAS100": dict(
        data=_ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv",
        params=dict(N=70, k_atr=1.0, R=1.75, H=90),
    ),
    "US30": dict(
        data=_ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",
        params=dict(N=20, k_atr=4.0, R=0.25, H=20),
    ),
}


def run_leg(name, cfg):
    m1 = load_m1_mid(cfg["data"])
    daily_index = aggregate_daily(load_m1_spot(cfg["data"])).index
    m = resample_mid(m1, "4h")
    cands = breakout_retest(m, cfg["params"], TF_DELTA["H4"])
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

    daily_rets = {}
    standalone = {}
    for name, cfg in LEGS.items():
        dr, sh, dd = run_leg(name, cfg)
        daily_rets[name] = dr
        standalone[name] = dict(sharpe=sh, max_dd=dd)

    idx = daily_rets["NAS100"].index.union(daily_rets["US30"].index)
    nas = daily_rets["NAS100"].reindex(idx, fill_value=0.0)
    us30 = daily_rets["US30"].reindex(idx, fill_value=0.0)

    corr = float(np.corrcoef(nas.values, us30.values)[0, 1])
    print(f"Correlation of daily log-returns (aligned, {len(idx)} days): {corr:+.3f}\n")

    combined = 0.5 * nas + 0.5 * us30
    combined_equity = equity_from_returns(combined)
    combined_sharpe = sharpe(combined, BARS_PER_YEAR)
    combined_dd = max_drawdown(combined_equity)

    yr_log = combined.groupby(combined.index.year).sum()
    n_years = len(yr_log)
    n_pos = int((yr_log > 0).sum())
    worst_year = float(yr_log.min())
    worst_year_label = int(yr_log.idxmin())

    print("=== Combined book: 50% NAS100 breakout + 50% US30 breakout ===")
    print(f"  Combined Sharpe: {combined_sharpe:+.3f}")
    print(f"  Combined maxDD:  {combined_dd*100:.1f}%")
    print(f"  Years positive:  {n_pos}/{n_years} (worst: {worst_year_label} {worst_year*100:+.1f}%)")
    print()
    print("=== Comparison ===")
    print(f"  NAS100 standalone: Sharpe {standalone['NAS100']['sharpe']:+.3f}, maxDD {standalone['NAS100']['max_dd']*100:.1f}%")
    print(f"  US30 standalone:   Sharpe {standalone['US30']['sharpe']:+.3f}, maxDD {standalone['US30']['max_dd']*100:.1f}%")
    print(f"  50/50 combined:    Sharpe {combined_sharpe:+.3f}, maxDD {combined_dd*100:.1f}%")
    naive_avg_sharpe = 0.5 * (standalone["NAS100"]["sharpe"] + standalone["US30"]["sharpe"])
    naive_avg_dd = 0.5 * (standalone["NAS100"]["max_dd"] + standalone["US30"]["max_dd"])
    print(f"  (naive average of standalone Sharpes: {naive_avg_sharpe:+.3f}; "
          f"naive average of standalone maxDDs: {naive_avg_dd*100:.1f}%)")
    # 100% US30-only benchmark: is diluting the strong leg with the weak
    # NAS100 leg actually worth it, or does it just drag the book down?
    us30_only_sharpe = standalone["US30"]["sharpe"]
    print(f"  (100% US30-only, for reference: Sharpe {us30_only_sharpe:+.3f}, "
          f"maxDD {standalone['US30']['max_dd']*100:.1f}%)")

    out_df = pd.DataFrame({
        "date": idx,
        "nas100_ret": nas.values,
        "us30_ret": us30.values,
        "combined_ret": combined.values,
    })
    out = RESULTS / "breakout_h4_combined_book.csv"
    out_df.to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio-construction check on two already-scored "
          "session-best configs, no parameter search). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
