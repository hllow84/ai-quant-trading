#!/usr/bin/env python3
"""
run_momentum_rotation_expanded.py -- WIDENED-UNIVERSE test, run as a separate,
clearly-labeled step after the section 12 audit (scripts/audit_momentum_rotation.py).
Adds commodities (DBC, USO, UNG, SLV), international/country (VGK, INDA, FXI),
factor ETFs (MTUM, VTV) and mid-cap breadth (MDY) to the original 17-ETF
universe -- 27 ranked instruments total, SPY still benchmark-only.

Same causal rebalance logic, same 4-cell grid (N in {6,12}, K in {3,5}), same
market filter, same cost model, as the original run_momentum_rotation.py.
Metrics use the AUDIT-CORRECTED methodology (live-window only -- no zero-
return padding before a config's first tradable rebalance), since the audit
found the original run_momentum_rotation.py padded full-period metrics with
years before the strategy could trade, which understated both sides
inconsistently vs SPY's own matched window.

Reports full period (live window) and 2000-2009 stress window, separately
from (not combined with) the audit's vol-matching test.
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

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
GRID = [(n, k) for n in (6, 12) for k in (3, 5)]
STRESS_START = pd.Timestamp("2000-01-01")
STRESS_END = pd.Timestamp("2009-12-31")

NEW_TICKERS = ["DBC", "USO", "UNG", "SLV", "VGK", "INDA", "FXI", "MTUM", "VTV", "MDY"]
EXPANDED_UNIVERSE = SECTOR_ETFS + ASSET_ETFS + NEW_TICKERS   # 11 + 6 + 10 = 27


def load_panel():
    return pd.read_csv(DATA / "momentum_universe_expanded_adjclose.csv", index_col=0, parse_dates=True).sort_index()


def window_metrics(ret: pd.Series) -> dict:
    ret = ret.dropna()
    equity = (1 + ret).cumprod()
    years = len(ret) / BARS_PER_YEAR
    total_ret = equity.iloc[-1] / equity.iloc[0] - 1.0
    cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else float("nan")
    log_ret = np.log1p(ret)
    yearly = log_ret.groupby(ret.index.year).sum()
    total_log = yearly.sum()
    top_year_share = float(yearly.abs().max() / abs(total_log)) if total_log != 0 else float("nan")
    return {
        "n_obs": len(ret), "years": years, "vol_ann_pct": ret.std(ddof=1) * np.sqrt(BARS_PER_YEAR) * 100,
        "sharpe": sharpe(ret, BARS_PER_YEAR), "cagr_pct": cagr * 100, "maxDD_pct": max_drawdown(equity) * 100,
        "total_return_pct": total_ret * 100, "top_year_share_pct": top_year_share * 100,
    }


def main():
    adjclose = load_panel()
    print(f"Expanded panel: {adjclose.shape[0]} rows x {adjclose.shape[1]} cols, "
          f"{adjclose.index[0].date()} -> {adjclose.index[-1].date()}")
    for t in EXPANDED_UNIVERSE:
        fv = adjclose[t].first_valid_index()
        print(f"  {t}: data from {fv.date() if fv is not None else 'MISSING'}")

    spy_ret_all = adjclose[BENCHMARK].pct_change().dropna()

    print("\n=== FULL PERIOD (live-window, expanded 27-instrument universe) ===")
    full_rows = []
    for n_months, top_k in GRID:
        we, to = build_weights(adjclose, n_months, top_k, universe=EXPANDED_UNIVERSE)
        guard = look_ahead_guard(we, adjclose, n_months)
        sim = simulate(adjclose, we, to, universe=EXPANDED_UNIVERSE)
        first_exec = we.index[0]
        net_live = sim["net"][sim["net"].index >= first_exec].dropna()
        spy_live = spy_ret_all[spy_ret_all.index >= first_exec]
        m = window_metrics(net_live)
        s = window_metrics(spy_live)
        m.update({"N": n_months, "K": top_k, "first_exec": str(first_exec.date()), "guard_pass": guard,
                   "spy_sharpe": s["sharpe"], "spy_cagr_pct": s["cagr_pct"], "spy_maxDD_pct": s["maxDD_pct"],
                   "beats_spy_sharpe": m["sharpe"] > s["sharpe"]})
        full_rows.append(m)
        print(f"N={n_months} K={top_k} (live from {first_exec.date()}): Sharpe {m['sharpe']:.3f} "
              f"(SPY {s['sharpe']:.3f})  CAGR {m['cagr_pct']:.2f}% (SPY {s['cagr_pct']:.2f}%)  "
              f"maxDD {m['maxDD_pct']:.2f}%  top_year_share {m['top_year_share_pct']:.1f}%  "
              f"beats_spy_sharpe={m['sharpe'] > s['sharpe']}")

    print("\n=== STRESS WINDOW 2000-01-01 -> 2009-12-31 (SAME 4 configs, expanded universe) ===")
    print("New-ticker coverage in stress window (stated, not backfilled):")
    for t in NEW_TICKERS:
        fv = adjclose[t].first_valid_index()
        if fv <= STRESS_END:
            cov = "FULL" if fv <= STRESS_START else f"PARTIAL from {fv.date()}"
        else:
            cov = f"NOT AVAILABLE until {fv.date()}"
        print(f"  {t}: {cov}")

    spy_stress = window_metrics(spy_ret_all[(spy_ret_all.index >= STRESS_START) & (spy_ret_all.index <= STRESS_END)])
    stress_rows = []
    for n_months, top_k in GRID:
        we, to = build_weights(adjclose, n_months, top_k, universe=EXPANDED_UNIVERSE)
        sim = simulate(adjclose, we, to, universe=EXPANDED_UNIVERSE)
        net_stress = sim["net"][(sim["net"].index >= STRESS_START) & (sim["net"].index <= STRESS_END)].dropna()
        m = window_metrics(net_stress)
        m.update({"N": n_months, "K": top_k, "beats_spy_sharpe": m["sharpe"] > spy_stress["sharpe"]})
        stress_rows.append(m)
        print(f"N={n_months} K={top_k}: Sharpe {m['sharpe']:.3f} (SPY {spy_stress['sharpe']:.3f})  "
              f"CAGR {m['cagr_pct']:.2f}% (SPY {spy_stress['cagr_pct']:.2f}%)  maxDD {m['maxDD_pct']:.2f}%  "
              f"beats_spy_sharpe={m['sharpe'] > spy_stress['sharpe']}")

    # DSR, this batch's own 4-cell pools
    full_pool = np.array([r["sharpe"] for r in full_rows])
    stress_pool = np.array([r["sharpe"] for r in stress_rows])
    print("\n=== DSR (structural pool = this batch's own 4 a priori cells) ===")
    for r in full_rows:
        res = deflated_sharpe(r["sharpe"], full_pool, n_obs=r["n_obs"], ann_factor=BARS_PER_YEAR)
        r["dsr"] = res["dsr"]; r["e_max_sr"] = res["e_max_sr"]
        print(f"FULL N={r['N']} K={r['K']}: DSR={res['dsr']:.4f} (E[maxSR]={res['e_max_sr']:.4f})")
    for r in stress_rows:
        res = deflated_sharpe(r["sharpe"], stress_pool, n_obs=r["n_obs"], ann_factor=BARS_PER_YEAR)
        r["dsr"] = res["dsr"]; r["e_max_sr"] = res["e_max_sr"]
        print(f"STRESS N={r['N']} K={r['K']}: DSR={res['dsr']:.4f} (E[maxSR]={res['e_max_sr']:.4f})")

    pd.DataFrame(full_rows).to_csv(RESULTS / "momentum_rotation_expanded_full.csv", index=False)
    pd.DataFrame(stress_rows).to_csv(RESULTS / "momentum_rotation_expanded_stress.csv", index=False)

    print("\n=== VERDICT (expanded universe, live-window methodology) ===")
    survivors = 0
    for r in full_rows:
        sr = next(s for s in stress_rows if s["N"] == r["N"] and s["K"] == r["K"])
        gates = {
            "dsr_gt_0.95_full": r["dsr"] > 0.95, "dsr_gt_0.95_stress": sr["dsr"] > 0.95,
            "top_year_le_60pct": r["top_year_share_pct"] <= 60,
            "beats_spy_sharpe_full": r["beats_spy_sharpe"], "beats_spy_sharpe_stress": sr["beats_spy_sharpe"],
        }
        ok = all(gates.values())
        survivors += ok
        print(f"N={r['N']} K={r['K']}: {gates} -> {'SURVIVES' if ok else 'fails'}")
    print(f"\nSurvivors: {survivors}/4")
    print(f"\nSaved: {RESULTS / 'momentum_rotation_expanded_full.csv'}, {RESULTS / 'momentum_rotation_expanded_stress.csv'}")


if __name__ == "__main__":
    main()
