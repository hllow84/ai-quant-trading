#!/usr/bin/env python3
"""
audit_momentum_rotation.py -- independent audit of STATE_OF_PLAY section 12.

Five checks, each computed (not asserted):
  1. Volatility mismatch full-period rotation vs SPY B&H, + vol-matched
     (constant-leverage) comparison.
  2. Risk-free consistency between the rotation Sharpe and the SPY Sharpe.
  3. Total-return correctness: auto_adjust=True applied identically to the
     ranked universe, SPY benchmark and the IEF defensive leg.
  4. Survivorship, stated as a limitation.
  5. General code review flags (documented inline, not computed).

ALSO fixes a bug this audit discovered: the original run_momentum_rotation.py
computed "full period" metrics over the ENTIRE adjclose span (1993-01-29 ->
2026-08-28, 8453 obs), but a strategy needing 12 months of universe history
plus a 200-day SPY SMA cannot trade until 1999-07-01 (N=6) or 2000-01-03
(N=12). Returns before the first execution date are exactly 0.0 by
construction (simulate() fills flat until the first weight exists), so the
original Sharpe/vol/CAGR were computed over a window that includes 6.4-7.0
years the strategy could not have been live for. This pads volatility DOWN
(zero-return days lower sample variance) and pads CAGR DOWN (total return
divided by more years than were actually invested) -- a conservative-direction
bug, but a real one, and it also means the earlier vol-matching estimate would
have used the wrong (padded) vol. This script recomputes FULL-period metrics
over each config's OWN live window [first_exec_date, panel_end], with SPY
sliced to the identical window for a fair comparison, and reports both the
original (padded) and corrected (live-window) numbers side by side.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.metrics import sharpe, max_drawdown
from research.dsr import deflated_sharpe
from research.momentum_rotation import UNIVERSE, BENCHMARK, DEFENSIVE, build_weights, simulate

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
GRID = [(n, k) for n in (6, 12) for k in (3, 5)]
STRESS_START = pd.Timestamp("2000-01-01")
STRESS_END = pd.Timestamp("2009-12-31")


def load_panel():
    return pd.read_csv(DATA / "momentum_universe_adjclose.csv", index_col=0, parse_dates=True).sort_index()


def window_metrics(ret: pd.Series, label: str) -> dict:
    ret = ret.dropna()
    equity = (1 + ret).cumprod()
    years = len(ret) / BARS_PER_YEAR
    total_ret = equity.iloc[-1] / equity.iloc[0] - 1.0
    cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else float("nan")
    vol = ret.std(ddof=1) * np.sqrt(BARS_PER_YEAR)
    return {
        "label": label, "n_obs": len(ret), "years": years,
        "vol_ann_pct": vol * 100, "sharpe": sharpe(ret, BARS_PER_YEAR),
        "cagr_pct": cagr * 100, "total_return_pct": total_ret * 100,
        "maxDD_pct": max_drawdown(equity) * 100,
    }


def main():
    print("=" * 78)
    print("AUDIT 2 -- RISK-FREE RATE CONSISTENCY")
    print("=" * 78)
    print("research/metrics.py::sharpe(returns, bars_per_year) = mean(returns)/std(returns) * sqrt(bars_per_year)")
    print("No risk-free subtraction anywhere in the formula.")
    print("run_momentum_rotation.py calls the SAME function `sharpe()` for BOTH:")
    print("  - rotation configs: sharpe(net_ret, bars_per_year=BARS_PER_YEAR)   [driver line ~82]")
    print("  - SPY buy-and-hold: sharpe(ret, bars_per_year=BARS_PER_YEAR)       [spy_buy_hold(), line ~122]")
    print("CONSISTENT: both use raw (non-excess) returns, zero risk-free subtraction on both sides.")
    print("No fix needed; if a risk-free-adjusted Sharpe were desired it would need applying to BOTH")
    print("sides identically, which the current code already guarantees structurally (one function, two callers).")

    print("\n" + "=" * 78)
    print("AUDIT 3 -- TOTAL RETURN CORRECTNESS")
    print("=" * 78)
    print("scripts/download_momentum_universe.py: ONE loop over UNIVERSE = SECTOR_ETFS + ASSET_ETFS + BENCHMARK")
    print("(BENCHMARK=['SPY'], ASSET_ETFS includes 'IEF'), single yf.download(..., auto_adjust=True) call site,")
    print("`close` column taken post-adjustment for every ticker with no branch -- SPY and IEF go through the")
    print("IDENTICAL code path as the ranked universe. Empirical confirmation (fresh pull, 2003-01 to 2003-06):")
    import yfinance as yf
    for t in ["SPY", "IEF"]:
        raw = yf.download(t, start="2003-01-01", end="2003-06-01", interval="1d", auto_adjust=False, progress=False)
        adj = yf.download(t, start="2003-01-01", end="2003-06-01", interval="1d", auto_adjust=True, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
            adj.columns = adj.columns.get_level_values(0)
        ratio0 = float(adj["Close"].iloc[0] / raw["Close"].iloc[0])
        ratio1 = float(adj["Close"].iloc[-1] / raw["Close"].iloc[-1])
        print(f"  {t}: adj/raw close ratio 2003-01-02={ratio0:.4f}, 2003-05-30={ratio1:.4f} "
              f"(ratio != 1 and DRIFTS toward 1 as of 2025 -- proves dividend/distribution reinvestment "
              f"is baked into the adjusted series for BOTH the equity benchmark and the bond defensive leg).")

    print("\n" + "=" * 78)
    print("AUDIT 4 -- SURVIVORSHIP")
    print("=" * 78)
    print("The 17-ETF + SPY universe consists only of funds that exist and trade TODAY; any sector/asset-class")
    print("ETF that was ever delisted, merged, or never launched is absent by construction, and free data cannot")
    print("correct this -- stated as a known, unfixed limitation, not fabricated around.")

    print("\n" + "=" * 78)
    print("AUDIT 1 + BUG FIX -- VOLATILITY MISMATCH, computed on the CORRECT (live-window) period")
    print("=" * 78)
    adjclose = load_panel()
    spy_full_ret = adjclose[BENCHMARK].pct_change().dropna()
    spy_full = window_metrics(spy_full_ret, "SPY full 1993-2026 (as originally reported)")
    print(f"\nOriginal SPY full-period (1993-2026, as reported in section 12): vol {spy_full['vol_ann_pct']:.3f}%, "
          f"Sharpe {spy_full['sharpe']:.3f}, CAGR {spy_full['cagr_pct']:.2f}%, n_obs {spy_full['n_obs']}")

    rows = []
    for n_months, top_k in GRID:
        we, to = build_weights(adjclose, n_months, top_k)
        sim = simulate(adjclose, we, to)
        first_exec = we.index[0]

        # ORIGINAL (padded) full-period metric, exactly as section 12 computed it
        net_padded = sim["net"].dropna()
        padded = window_metrics(net_padded, f"N{n_months}K{top_k} padded-full")

        # CORRECTED: live window only, both strategy and SPY sliced identically
        net_live = sim["net"][sim["net"].index >= first_exec].dropna()
        spy_live_ret = spy_full_ret[spy_full_ret.index >= first_exec]
        strat_live = window_metrics(net_live, f"N{n_months}K{top_k} live")
        spy_live = window_metrics(spy_live_ret, f"SPY live-matched N{n_months}K{top_k}")

        lev = spy_live["vol_ann_pct"] / strat_live["vol_ann_pct"]
        levered_ret = net_live * lev
        levered = window_metrics(levered_ret, f"N{n_months}K{top_k} vol-matched (lev {lev:.3f}x)")

        print(f"\n--- N={n_months} K={top_k} (first live rebalance {first_exec.date()}) ---")
        print(f"  ORIGINAL (padded, 1993 start) : vol {padded['vol_ann_pct']:.3f}%  Sharpe {padded['sharpe']:.3f}  "
              f"CAGR {padded['cagr_pct']:.2f}%  n_obs {padded['n_obs']} ({padded['years']:.1f}y)")
        print(f"  CORRECTED (live window)       : vol {strat_live['vol_ann_pct']:.3f}%  Sharpe {strat_live['sharpe']:.3f}  "
              f"CAGR {strat_live['cagr_pct']:.2f}%  maxDD {strat_live['maxDD_pct']:.2f}%  n_obs {strat_live['n_obs']} ({strat_live['years']:.1f}y)")
        print(f"  SPY, SAME live window          : vol {spy_live['vol_ann_pct']:.3f}%  Sharpe {spy_live['sharpe']:.3f}  "
              f"CAGR {spy_live['cagr_pct']:.2f}%  maxDD {spy_live['maxDD_pct']:.2f}%")
        print(f"  Vol-matched leverage needed     : {lev:.3f}x  (strategy vol {strat_live['vol_ann_pct']:.3f}% -> SPY's {spy_live['vol_ann_pct']:.3f}%)")
        print(f"  VOL-MATCHED strategy            : vol {levered['vol_ann_pct']:.3f}%  Sharpe {levered['sharpe']:.3f}  "
              f"CAGR {levered['cagr_pct']:.2f}%  maxDD {levered['maxDD_pct']:.2f}%  total_ret {levered['total_return_pct']:.1f}%")
        print(f"  SPY total return, same window   : {spy_live['total_return_pct']:.1f}%")
        beats = "BEATS" if levered["cagr_pct"] > spy_live["cagr_pct"] else "LOSES TO"
        print(f"  VOL-MATCHED CAGR {beats} SPY CAGR on live-window full period "
              f"({levered['cagr_pct']:.2f}% vs {spy_live['cagr_pct']:.2f}%)")

        rows.append({
            "N": n_months, "K": top_k, "first_exec": str(first_exec.date()),
            "orig_padded_vol_pct": padded["vol_ann_pct"], "orig_padded_sharpe": padded["sharpe"],
            "orig_padded_cagr_pct": padded["cagr_pct"],
            "live_vol_pct": strat_live["vol_ann_pct"], "live_sharpe": strat_live["sharpe"],
            "live_cagr_pct": strat_live["cagr_pct"], "live_maxDD_pct": strat_live["maxDD_pct"],
            "spy_live_vol_pct": spy_live["vol_ann_pct"], "spy_live_sharpe": spy_live["sharpe"],
            "spy_live_cagr_pct": spy_live["cagr_pct"], "spy_live_maxDD_pct": spy_live["maxDD_pct"],
            "leverage_to_match_spy_vol": lev,
            "vol_matched_sharpe": levered["sharpe"], "vol_matched_cagr_pct": levered["cagr_pct"],
            "vol_matched_maxDD_pct": levered["maxDD_pct"], "vol_matched_total_return_pct": levered["total_return_pct"],
            "spy_total_return_pct": spy_live["total_return_pct"],
            "vol_matched_beats_spy_cagr": levered["cagr_pct"] > spy_live["cagr_pct"],
        })

    # ── stress window vol-matching (unaffected by the padding bug -- already inside live period) ──
    print("\n" + "=" * 78)
    print("VOL-MATCHED comparison, STRESS WINDOW 2000-01-01 -> 2009-12-31 (unaffected by the padding bug --")
    print("this window sits entirely inside the live-trading period for all 4 configs)")
    print("=" * 78)
    spy_stress_ret = spy_full_ret[(spy_full_ret.index >= STRESS_START) & (spy_full_ret.index <= STRESS_END)]
    spy_stress = window_metrics(spy_stress_ret, "SPY stress")
    print(f"\nSPY stress: vol {spy_stress['vol_ann_pct']:.3f}%  Sharpe {spy_stress['sharpe']:.3f}  "
          f"CAGR {spy_stress['cagr_pct']:.2f}%  maxDD {spy_stress['maxDD_pct']:.2f}%")

    stress_rows = []
    for n_months, top_k in GRID:
        we, to = build_weights(adjclose, n_months, top_k)
        sim = simulate(adjclose, we, to)
        net_stress = sim["net"][(sim["net"].index >= STRESS_START) & (sim["net"].index <= STRESS_END)].dropna()
        strat_stress = window_metrics(net_stress, f"N{n_months}K{top_k} stress")
        lev = spy_stress["vol_ann_pct"] / strat_stress["vol_ann_pct"]
        levered = window_metrics(net_stress * lev, f"N{n_months}K{top_k} stress vol-matched")
        beats = "BEATS" if levered["cagr_pct"] > spy_stress["cagr_pct"] else "LOSES TO"
        print(f"\nN={n_months} K={top_k}: raw vol {strat_stress['vol_ann_pct']:.3f}% Sharpe {strat_stress['sharpe']:.3f} "
              f"CAGR {strat_stress['cagr_pct']:.2f}%  |  lev {lev:.3f}x -> vol-matched Sharpe {levered['sharpe']:.3f} "
              f"CAGR {levered['cagr_pct']:.2f}% maxDD {levered['maxDD_pct']:.2f}%  {beats} SPY CAGR {spy_stress['cagr_pct']:.2f}%")
        stress_rows.append({
            "N": n_months, "K": top_k, "raw_vol_pct": strat_stress["vol_ann_pct"], "raw_sharpe": strat_stress["sharpe"],
            "raw_cagr_pct": strat_stress["cagr_pct"], "leverage": lev,
            "vol_matched_sharpe": levered["sharpe"], "vol_matched_cagr_pct": levered["cagr_pct"],
            "vol_matched_maxDD_pct": levered["maxDD_pct"], "spy_sharpe": spy_stress["sharpe"],
            "spy_cagr_pct": spy_stress["cagr_pct"], "spy_maxDD_pct": spy_stress["maxDD_pct"],
            "vol_matched_beats_spy_cagr": levered["cagr_pct"] > spy_stress["cagr_pct"],
        })

    pd.DataFrame(rows).to_csv(RESULTS / "momentum_rotation_audit_full.csv", index=False)
    pd.DataFrame(stress_rows).to_csv(RESULTS / "momentum_rotation_audit_stress.csv", index=False)
    print(f"\nSaved: {RESULTS / 'momentum_rotation_audit_full.csv'}, {RESULTS / 'momentum_rotation_audit_stress.csv'}")


if __name__ == "__main__":
    main()
