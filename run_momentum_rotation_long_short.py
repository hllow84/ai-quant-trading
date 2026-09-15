#!/usr/bin/env python3
"""
run_momentum_rotation_long_short.py -- STATE_OF_PLAY section 34.

Long top-5 (20% each, 100% gross) / short bottom-3 (10% each, 30% gross)
momentum rotation, vs the existing long-only baseline. Widened 27-instrument
universe (section 12.2's canonical wider test -- SECTOR_ETFS+ASSET_ETFS+
NEW_TICKERS), same causal ranking/lag/market-filter/cost model as section
12, N in {6, 12} months (K fixed at long=5/short=3 per the task brief, not
a K grid this time). Full period (live-window only, audit-corrected
methodology per section 12.3) + 2000-2009 stress window. Reuses simulate()
and look_ahead_guard() from research/momentum_rotation.py UNCHANGED.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.metrics import sharpe, max_drawdown
from research.dsr import deflated_sharpe
from research.momentum_rotation import (
    SECTOR_ETFS, ASSET_ETFS, BENCHMARK, DEFENSIVE, build_weights, simulate, look_ahead_guard,
)
from research.momentum_rotation_long_short import build_weights_long_short, LONG_K, SHORT_K, LONG_WEIGHT, SHORT_WEIGHT
from research.six_strategies_engine import drawdown_with_recovery

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
GRID_N = [6, 12]
STRESS_START = pd.Timestamp("2000-01-01")
STRESS_END = pd.Timestamp("2009-12-31")

NEW_TICKERS = ["DBC", "USO", "UNG", "SLV", "VGK", "INDA", "FXI", "MTUM", "VTV", "MDY"]
EXPANDED_UNIVERSE = SECTOR_ETFS + ASSET_ETFS + NEW_TICKERS


def load_panel():
    return pd.read_csv(DATA / "momentum_universe_expanded_adjclose.csv", index_col=0, parse_dates=True).sort_index()


def window_metrics(ret: pd.Series, equity: pd.Series) -> dict:
    ret = ret.dropna()
    eq = equity.reindex(ret.index)
    years = len(ret) / BARS_PER_YEAR
    total_ret = eq.iloc[-1] / eq.iloc[0] - 1.0
    cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else float("nan")
    log_ret = np.log1p(ret)
    yearly = log_ret.groupby(ret.index.year).sum()
    total_log = yearly.sum()
    top_year_share = float(yearly.abs().max() / abs(total_log)) if total_log != 0 else float("nan")
    dd = drawdown_with_recovery(eq)
    rec_days = (dd["recovery_date"] - dd["trough_date"]).days if dd["recovery_date"] is not None else None
    return {
        "n_obs": len(ret), "years": years, "sharpe": sharpe(ret, BARS_PER_YEAR), "cagr_pct": cagr * 100,
        "maxDD_pct": max_drawdown(eq) * 100, "recovery_days": rec_days,
        "total_return_pct": total_ret * 100, "top_year_share_pct": top_year_share * 100,
    }


def year_by_year(ret: pd.Series, equity: pd.Series) -> pd.DataFrame:
    idx = ret.index
    eq = equity.reindex(idx)
    eq_prev = eq.shift(1)
    eq_prev.iloc[0] = float(eq.iloc[0]) / (1 + ret.iloc[0]) if (1 + ret.iloc[0]) != 0 else eq.iloc[0]
    rows = []
    for yr in sorted(idx.year.unique()):
        m = idx.year == yr
        start_eq = float(eq_prev[m].iloc[0])
        end_eq = float(eq[m].iloc[-1])
        rows.append(dict(year=int(yr), start_equity=start_eq, end_equity=end_eq,
                          year_return_pct=(end_eq / start_eq - 1.0) * 100))
    return pd.DataFrame(rows)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    W = 112
    print("=" * W)
    print("  SECTION 34.1 -- LONG/SHORT MOMENTUM ROTATION vs LONG-ONLY BASELINE")
    print("=" * W)
    print(f"\nSplit: LONG top {LONG_K} @ {LONG_WEIGHT*100:.0f}% each ({LONG_K*LONG_WEIGHT*100:.0f}% gross long), "
          f"SHORT bottom {SHORT_K} @ {abs(SHORT_WEIGHT)*100:.0f}% each ({SHORT_K*abs(SHORT_WEIGHT)*100:.0f}% gross "
          f"short). Total gross exposure {(LONG_K*LONG_WEIGHT + SHORT_K*abs(SHORT_WEIGHT))*100:.0f}%. Risk-off "
          f"behaviour unchanged from baseline (100% IEF, no shorts).")

    adjclose = load_panel()
    print(f"\nPanel: {adjclose.shape[0]} rows x {adjclose.shape[1]} cols, {adjclose.index[0].date()} -> "
          f"{adjclose.index[-1].date()}, widened 27-instrument universe (section 12.2 canonical wider test)")
    spy_ret_all = adjclose[BENCHMARK].pct_change().dropna()
    spy_eq_all = (1 + spy_ret_all).cumprod()

    full_rows, stress_rows = [], []
    yearly_tables = {}

    for n_months in GRID_N:
        # ---- long-only baseline (unchanged mechanism) ----
        we_lo, to_lo = build_weights(adjclose, n_months, LONG_K, universe=EXPANDED_UNIVERSE)
        guard_lo = look_ahead_guard(we_lo, adjclose, n_months)
        sim_lo = simulate(adjclose, we_lo, to_lo, universe=EXPANDED_UNIVERSE)

        # ---- long/short variant ----
        we_ls, to_ls = build_weights_long_short(adjclose, n_months, universe=EXPANDED_UNIVERSE)
        guard_ls = look_ahead_guard(we_ls, adjclose, n_months)
        sim_ls = simulate(adjclose, we_ls, to_ls, universe=EXPANDED_UNIVERSE)

        first_exec = max(we_lo.index[0], we_ls.index[0])  # common live-window start, live-window methodology (sec 12.3)

        for label, sim, guard in [("LONG-ONLY", sim_lo, guard_lo), ("LONG-SHORT", sim_ls, guard_ls)]:
            net_live = sim["net"][sim["net"].index >= first_exec].dropna()
            eq_live = (1 + net_live).cumprod()
            spy_live = spy_ret_all[spy_ret_all.index >= first_exec]
            spy_eq_live = (1 + spy_live).cumprod()
            m = window_metrics(net_live, eq_live)
            s = window_metrics(spy_live, spy_eq_live)
            m.update({"variant": label, "N": n_months, "first_exec": str(first_exec.date()), "guard_pass": guard,
                      "spy_sharpe": s["sharpe"], "spy_cagr_pct": s["cagr_pct"], "spy_maxDD_pct": s["maxDD_pct"],
                      "beats_spy_sharpe": m["sharpe"] > s["sharpe"]})
            full_rows.append(m)
            print(f"\nFULL PERIOD  {label}  N={n_months} (live from {first_exec.date()}, guard={'PASS' if guard else 'FAIL'}):")
            print(f"  Sharpe {m['sharpe']:.3f} (SPY {s['sharpe']:.3f})  CAGR {m['cagr_pct']:.2f}% "
                  f"(SPY {s['cagr_pct']:.2f}%)  maxDD {m['maxDD_pct']:.2f}% (SPY {s['maxDD_pct']:.2f}%)  "
                  f"recovery {m['recovery_days']}d  top_year_share {m['top_year_share_pct']:.1f}%  "
                  f"beats_spy_sharpe={m['sharpe'] > s['sharpe']}")
            yearly_tables[f"{label}_N{n_months}_full"] = year_by_year(net_live, eq_live)

        # ---- stress window 2000-2009 ----
        spy_stress_ret = spy_ret_all[(spy_ret_all.index >= STRESS_START) & (spy_ret_all.index <= STRESS_END)]
        spy_stress_eq = (1 + spy_stress_ret).cumprod()
        s_stress = window_metrics(spy_stress_ret, spy_stress_eq)
        for label, sim in [("LONG-ONLY", sim_lo), ("LONG-SHORT", sim_ls)]:
            net_stress = sim["net"][(sim["net"].index >= STRESS_START) & (sim["net"].index <= STRESS_END)].dropna()
            eq_stress = (1 + net_stress).cumprod()
            m = window_metrics(net_stress, eq_stress)
            m.update({"variant": label, "N": n_months, "beats_spy_sharpe": m["sharpe"] > s_stress["sharpe"]})
            stress_rows.append(m)
            print(f"STRESS 2000-2009  {label}  N={n_months}: Sharpe {m['sharpe']:.3f} (SPY {s_stress['sharpe']:.3f})  "
                  f"CAGR {m['cagr_pct']:.2f}% (SPY {s_stress['cagr_pct']:.2f}%)  maxDD {m['maxDD_pct']:.2f}% "
                  f"(SPY {s_stress['maxDD_pct']:.2f}%)  beats_spy_sharpe={m['sharpe'] > s_stress['sharpe']}")
            yearly_tables[f"{label}_N{n_months}_stress"] = year_by_year(net_stress, eq_stress)

    # ---- down-year-specific comparison (the user's specific ask) ----
    print("\n" + "=" * W)
    print("  DOWN-YEAR-SPECIFIC COMPARISON (SPY negative years only, N=12 shown -- both N behave the same way)")
    print("=" * W)
    spy_yearly = spy_ret_all.groupby(spy_ret_all.index.year).apply(lambda s: (1 + s).prod() - 1)
    down_years = sorted(spy_yearly[spy_yearly < 0].index.tolist())
    print(f"  SPY down years in the full available panel: {down_years}")
    for n_months in GRID_N:
        lo_yt = yearly_tables[f"LONG-ONLY_N{n_months}_full"].set_index("year")
        ls_yt = yearly_tables[f"LONG-SHORT_N{n_months}_full"].set_index("year")
        print(f"\n  N={n_months}:")
        for yr in down_years:
            if yr in lo_yt.index and yr in ls_yt.index:
                print(f"    {yr}: SPY {spy_yearly.loc[yr]*100:+6.2f}%   LONG-ONLY {lo_yt.loc[yr,'year_return_pct']:+7.2f}%   "
                      f"LONG-SHORT {ls_yt.loc[yr,'year_return_pct']:+7.2f}%   "
                      f"short-leg delta {ls_yt.loc[yr,'year_return_pct']-lo_yt.loc[yr,'year_return_pct']:+6.2f}pp")

    # ---- DSR reference (pool = this batch's own cells) ----
    print("\n" + "=" * W)
    print("  DSR REFERENCE (pool = this batch's own 4 full-period cells: 2 variants x 2 N)")
    print("=" * W)
    full_pool = np.array([r["sharpe"] for r in full_rows])
    for r in full_rows:
        res = deflated_sharpe(r["sharpe"], full_pool, n_obs=r["n_obs"], ann_factor=BARS_PER_YEAR)
        r["dsr"] = res["dsr"]; r["e_max_sr"] = res["e_max_sr"]
        print(f"  FULL {r['variant']} N={r['N']}: DSR={res['dsr']:.4f} (E[maxSR]={res['e_max_sr']:.4f}, pool N=4)")
    stress_pool = np.array([r["sharpe"] for r in stress_rows])
    for r in stress_rows:
        res = deflated_sharpe(r["sharpe"], stress_pool, n_obs=r["n_obs"], ann_factor=BARS_PER_YEAR)
        r["dsr"] = res["dsr"]; r["e_max_sr"] = res["e_max_sr"]
        print(f"  STRESS {r['variant']} N={r['N']}: DSR={res['dsr']:.4f} (E[maxSR]={res['e_max_sr']:.4f}, pool N=4)")

    pd.DataFrame(full_rows).to_csv(RESULTS / "momentum_rotation_long_short_full.csv", index=False)
    pd.DataFrame(stress_rows).to_csv(RESULTS / "momentum_rotation_long_short_stress.csv", index=False)
    for k, v in yearly_tables.items():
        v.to_csv(RESULTS / f"momentum_rotation_long_short_yearly_{k}.csv", index=False)
    print(f"\nSaved: results/momentum_rotation_long_short_{{full,stress}}.csv, "
          f"momentum_rotation_long_short_yearly_*.csv ({len(yearly_tables)} tables)")


if __name__ == "__main__":
    main()
