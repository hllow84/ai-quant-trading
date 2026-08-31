#!/usr/bin/env python3
"""
run_momentum_rotation_generalization.py — does the audited momentum-
rotation mechanism (trailing N-month return ranking + causal long-SMA
market filter, STATE_OF_PLAY sections 12/12.1-12.4) generalize to universes
it has never been tested on?

`research/momentum_rotation.py::build_weights()`/`simulate()` are reused
COMPLETELY UNCHANGED in mechanism. The only code change to that file was
additive (see its own docstring): `benchmark`/`defensive` are now optional
parameters (default "SPY"/"IEF", preserving sections 12/12.1-12.4
byte-identically -- VERIFIED before this run, see verification note below)
so a different universe's own market-filter basis and defensive leg can be
supplied without hardcoding SPY/IEF into a universe that has neither. Same
additive-parameter convention already used twice before in that file
(sma_window, rebalance_step).

VERIFICATION: `build_weights(adjclose, 6, 3)` and `build_weights(adjclose,
12, 5)` on the original 17-ETF panel reproduce first_exec dates 1999-07-01
and 2000-01-03 exactly, matching STATE_OF_PLAY section 12.1's audited
values -- the refactor changes nothing for existing call sites.

GRID: same as the original -- N in {6, 12} months, K in {3, 5} holdings.
Same causal execution lag (unchanged code). Same live-window methodology as
the CORRECTED (audited, section 12.1) run: metrics start at each config's
own first live execution date, never padded with pre-tradeable zero-return
days -- this run implements that correctly from the start, it does not
repeat the original section-12 bug.

UNIVERSE A -- CRYPTO SECTORS (scripts/download_crypto_momentum_universe.py):
  benchmark=BTC (excluded from ranking, market-filter basis), defensive=
  CASH_USD (synthetic, flat, 0% return -- no crypto equivalent of IEF
  exists; conservative, understates the true defensive return).
  Ranked: ETH, SOL, BNB, ADA, AVAX, UNI, AAVE, LINK, SAND, MANA, DOGE (11
  instruments, 6 categories: L1-general/benchmark, L1-smart-contract,
  DeFi, oracle/infra, gaming/metaverse, meme).
  Costs: Binance spot taker fee dominates (section 13 finding) -- 12 bps
  per side (10bps taker + 2bps stated slippage cushion), 24bps round-turn.
  STRESS WINDOW: 2022-01-01 -> 2022-12-31 (LUNA collapse May 2022, FTX
  collapse Nov 2022) -- crypto's own severe stress period, the closest
  analogue available; crypto data does not reach back to a 2000-2009-style
  decade-scale holdout (stated, not faked).

UNIVERSE B -- COUNTRY/REGION EQUITY ETFs (scripts/download_momentum_countries.py):
  benchmark=ACWI (global, excluded from ranking -- SPY is now a RANKED
  competitor, per the task's explicit instruction), defensive=IEF (SAME
  instrument as the original study, reused unchanged).
  Ranked: EWJ, EWG, EWU, EWZ, INDA, FXI, EFA, EEM, SPY, IEF (10 instruments).
  Costs: same 3bps/side (6bps round-turn) as the original study -- same
  instrument class (liquid major ETFs), no reason to re-derive.
  STRESS WINDOW: 2008-01-01 -> 2012-12-31 (GFC + Eurozone debt crisis) --
  the earliest stress period available given ACWI's 2008-03-28 inception
  constrains when the market filter can evaluate at all.

BENCHMARK FOR COMPARISON: an EQUAL-WEIGHT, buy-and-hold-from-first-live-date
basket of that universe's OWN ranked instruments (not the excluded
benchmark ticker) -- per the task's explicit instruction. Weights fixed at
1/n_available at the first live execution date (same date the rotation
strategy itself first has enough history to trade), no further rebalancing,
no cost (matching the original study's own spy_buy_hold() convention,
which also charges no cost).

HONESTY GATES: look-ahead guard (research/momentum_rotation.py::
look_ahead_guard(), unchanged), DSR against the cumulative project count
(structural pool = each universe's own 4 a priori cells, same convention
sections 12.1/12.2 used), per-year concentration (top year <= 60% of net
log-return, same bar as every other sweep in this repo -- NOT applied in
the original section 12 run, added here as this task explicitly asks for
it), out-of-regime stress window (see above, per universe), vs buy-and-hold
equal-weight basket.

Usage: python run_momentum_rotation_generalization.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.dsr import deflated_sharpe, expected_max_sharpe
from research.metrics import sharpe, max_drawdown
from research.momentum_rotation import build_weights, simulate, look_ahead_guard

BARS_PER_YEAR = 252
GRID = [(n, k) for n in (6, 12) for k in (3, 5)]
DSR_BAR = 0.95
CONC_BAR = 0.60

PRIOR_TRIALS = 916  # STATE_OF_PLAY.md current cumulative
PRIOR_CSVS = [
    "sweep_progress.csv", "htf_breakout.csv", "sweep_indices.csv",
    "basket_configs.csv", "basket_configs_scored_pre2018.csv",
    "sneaky_pivot.csv", "sneaky_pivot_pre2018.csv", "orb.csv", "orb_pre2018.csv",
    "sweep_m1_scored.csv", "sweep_m1_rth_scored.csv",
    "sweep_crypto_scored.csv", "sweep_stocks_scored.csv", "sweep_stocks_pre2018_scored.csv",
    "regime_switch.csv", "regime_switch_longlb.csv",
]

UNIVERSES = {
    "crypto_sectors": dict(
        panel_path=_ROOT / "data" / "momentum_crypto_adjclose.csv",
        benchmark="BTC", defensive="CASH_USD",
        ranked=["ETH", "SOL", "BNB", "ADA", "AVAX", "UNI", "AAVE", "LINK", "SAND", "MANA", "DOGE", "CASH_USD"],
        cost_bps_per_side=12.0,
        stress_start=pd.Timestamp("2022-01-01"), stress_end=pd.Timestamp("2022-12-31"),
        stress_label="2022 crypto bear (LUNA + FTX collapse)",
    ),
    "country_etfs": dict(
        panel_path=_ROOT / "data" / "momentum_countries_adjclose.csv",
        benchmark="ACWI", defensive="IEF",
        ranked=["EWJ", "EWG", "EWU", "EWZ", "INDA", "FXI", "EFA", "EEM", "SPY", "IEF"],
        cost_bps_per_side=3.0,
        stress_start=pd.Timestamp("2008-01-01"), stress_end=pd.Timestamp("2012-12-31"),
        stress_label="2008-2012 GFC + Eurozone debt crisis (ACWI-inception-constrained)",
    ),
}

OUT_CSV = _ROOT / "results" / "momentum_rotation_generalization.csv"


def window_metrics(ret: pd.Series) -> dict:
    ret = ret.dropna()
    if ret.empty:
        return dict(n_obs=0, years=0.0, sharpe=float("nan"), cagr_pct=float("nan"),
                    total_return_pct=float("nan"), maxDD_pct=float("nan"),
                    skew=0.0, ekurt=0.0)
    equity = (1 + ret).cumprod()
    years = len(ret) / BARS_PER_YEAR
    total_ret = equity.iloc[-1] / equity.iloc[0] - 1.0
    cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else float("nan")
    return dict(n_obs=len(ret), years=years, sharpe=sharpe(ret, BARS_PER_YEAR),
               cagr_pct=cagr * 100, total_return_pct=total_ret * 100,
               maxDD_pct=max_drawdown(equity) * 100,
               skew=float(ret.skew()), ekurt=float(ret.kurtosis()))


def year_concentration(ret: pd.Series) -> tuple[float, float]:
    """top calendar-year log-return share of total log-return; NaN if total <= 0."""
    log_ret = np.log1p(ret.dropna())
    yr = log_ret.groupby(log_ret.index.year).sum()
    total = float(yr.sum())
    top = float(yr.max()) if len(yr) else float("nan")
    share = (top / total) if total > 0 else float("nan")
    return top, share


def equal_weight_basket(adjclose: pd.DataFrame, ranked: list[str], first_live: pd.Timestamp) -> pd.Series:
    """
    Equal-weight, buy-and-hold-from-first-live-date basket of the ranked
    universe's OWN instruments (not the excluded benchmark). Weights fixed
    at 1/n_available at `first_live`, no further rebalancing, no cost
    (matches the original study's own spy_buy_hold() convention).
    """
    px0 = adjclose.loc[first_live, ranked]
    available = px0.dropna().index.tolist()
    px = adjclose.loc[first_live:, available]
    rel = px / px.iloc[0]
    basket = rel.mean(axis=1)  # equal weight, no cost, no rebalance
    return basket.pct_change().dropna()


def run_universe(name: str, cfg: dict) -> tuple[pd.DataFrame, dict]:
    adjclose = pd.read_csv(cfg["panel_path"], index_col=0, parse_dates=True).sort_index()
    rows = []
    guards = []
    for n_months, top_k in GRID:
        we, to = build_weights(adjclose, n_months, top_k, universe=cfg["ranked"],
                               benchmark=cfg["benchmark"], defensive=cfg["defensive"])
        if we.empty:
            print(f"  [{name}] N={n_months} K={top_k}: NO executions produced — skipped.")
            continue
        sim = simulate(adjclose, we, to, cost_bps_per_side=cfg["cost_bps_per_side"], universe=cfg["ranked"])
        first_exec = we.index[0]
        guard_ok = look_ahead_guard(we, adjclose, n_months)
        guards.append(guard_ok)

        net_live = sim["net"][sim["net"].index >= first_exec]
        full = window_metrics(net_live)
        top_yr, top_share = year_concentration(net_live)

        bench_ret = adjclose[cfg["benchmark"]].pct_change()
        bench_live = window_metrics(bench_ret[bench_ret.index >= first_exec])

        basket_ret = equal_weight_basket(adjclose, cfg["ranked"], first_exec)
        basket_m = window_metrics(basket_ret)

        s0, s1 = cfg["stress_start"], cfg["stress_end"]
        stress_net = sim["net"][(sim["net"].index >= max(s0, first_exec)) & (sim["net"].index <= s1)]
        stress_m = window_metrics(stress_net)
        stress_bench = window_metrics(bench_ret[(bench_ret.index >= max(s0, first_exec)) & (bench_ret.index <= s1)])
        stress_basket_ret = basket_ret[(basket_ret.index >= max(s0, first_exec)) & (basket_ret.index <= s1)]
        stress_basket_m = window_metrics(stress_basket_ret)

        rows.append(dict(
            universe=name, N=n_months, K=top_k, first_exec=str(first_exec.date()),
            guard=guard_ok,
            n_obs=full["n_obs"], years=full["years"], sharpe=full["sharpe"],
            cagr_pct=full["cagr_pct"], total_return_pct=full["total_return_pct"],
            maxDD_pct=full["maxDD_pct"], skew=full["skew"], ekurt=full["ekurt"],
            top_year_share=top_share,
            bench_sharpe=bench_live["sharpe"], bench_cagr_pct=bench_live["cagr_pct"],
            bench_maxDD_pct=bench_live["maxDD_pct"],
            basket_sharpe=basket_m["sharpe"], basket_cagr_pct=basket_m["cagr_pct"],
            basket_maxDD_pct=basket_m["maxDD_pct"],
            beats_bench=full["sharpe"] > bench_live["sharpe"] if np.isfinite(full["sharpe"]) else False,
            beats_basket=full["sharpe"] > basket_m["sharpe"] if np.isfinite(full["sharpe"]) else False,
            stress_sharpe=stress_m["sharpe"], stress_cagr_pct=stress_m["cagr_pct"],
            stress_maxDD_pct=stress_m["maxDD_pct"], stress_n_obs=stress_m["n_obs"],
            stress_bench_sharpe=stress_bench["sharpe"], stress_basket_sharpe=stress_basket_m["sharpe"],
        ))
        print(f"  [{name}] N={n_months} K={top_k}: first_exec={first_exec.date()} guard={guard_ok} "
              f"Sharpe={full['sharpe']:+.3f} CAGR={full['cagr_pct']:.2f}% maxDD={full['maxDD_pct']:.1f}% "
              f"vs bench SR {bench_live['sharpe']:+.3f} vs basket SR {basket_m['sharpe']:+.3f}", flush=True)

    df = pd.DataFrame(rows)
    return df, dict(all_guards_pass=all(guards) if guards else False)


def main() -> None:
    all_rows = []
    for name, cfg in UNIVERSES.items():
        if not cfg["panel_path"].exists():
            print(f"[{name}] MISSING {cfg['panel_path'].name} — skipped.")
            continue
        print(f"\n=== UNIVERSE: {name} ===", flush=True)
        df, meta = run_universe(name, cfg)
        all_rows.append(df)

    combined = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(OUT_CSV, index=False)
    analyze(combined)


def analyze(df: pd.DataFrame) -> None:
    n_batch = len(df)
    cumulative = PRIOR_TRIALS + n_batch
    W = 150
    print("\n" + "=" * W)
    print("  MOMENTUM ROTATION — GENERALIZATION TEST: does the audited mechanism transfer to new universes?")
    print("  build_weights()/simulate() mechanism UNCHANGED. Same N/K grid, same causal lag, same corrected")
    print("  live-window methodology as the audited section-12.1 run.")
    print(f"  Configs THIS BATCH: {n_batch}  |  CUMULATIVE PROJECT TRIALS: {PRIOR_TRIALS} + {n_batch} = {cumulative}")
    print("=" * W)

    if df.empty:
        print("\n  NO configs produced. Investigate before reading anything in.")
        return

    for name in df["universe"].unique():
        sub = df[df["universe"] == name].copy()
        sr_batch = sub["sharpe"].fillna(0.0).to_numpy()
        e_struct = expected_max_sharpe(sr_batch)

        def _dsr(r):
            if not np.isfinite(r["sharpe"]) or r["n_obs"] < 4:
                return float("nan")
            return deflated_sharpe(sr_best=float(r["sharpe"]), sr_trials=sr_batch, n_obs=int(r["n_obs"]),
                                   ann_factor=BARS_PER_YEAR,
                                   skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
                                   excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0)["dsr"]
        sub["dsr"] = sub.apply(_dsr, axis=1)
        sub["not_concentrated"] = sub["top_year_share"].notna() & (sub["top_year_share"] <= CONC_BAR)
        sub["SURVIVOR"] = (sub["guard"] & (sub["sharpe"] > 0) & (sub["dsr"] > DSR_BAR)
                          & sub["not_concentrated"] & sub["beats_bench"] & sub["beats_basket"])

        print(f"\n  --- {name} --- (DSR structural pool = this universe's own {len(sr_batch)} a priori cells, "
              f"E[max SR] {e_struct[0]:+.3f})")
        print(f"  {'N':>3} {'K':>3} {'first_exec':>11} {'Sharpe':>8} {'DSR':>5} {'CAGR%':>7} {'maxDD%':>7} "
              f"{'top%':>5} {'benchSR':>8} {'basketSR':>9} {'bBench':>7} {'bBasket':>8} {'guard':>6}")
        print("  " + "-" * (W - 4))
        for _, r in sub.sort_values(["N", "K"]).iterrows():
            share = r["top_year_share"]
            print(f"  {int(r['N']):>3} {int(r['K']):>3} {r['first_exec']:>11} {r['sharpe']:>+8.3f} "
                  f"{r['dsr']:>5.2f} {r['cagr_pct']:>7.2f} {r['maxDD_pct']:>7.1f} "
                  + (f"{share * 100:>4.0f}%" if np.isfinite(share) else f"{'n/a':>5}")
                  + f" {r['bench_sharpe']:>+8.3f} {r['basket_sharpe']:>+9.3f} "
                  f"{'YES' if r['beats_bench'] else 'no':>7} {'YES' if r['beats_basket'] else 'no':>8} "
                  f"{'PASS' if r['guard'] else 'FAIL':>6}")

        cfg = UNIVERSES[name]
        print(f"\n  STRESS WINDOW ({cfg['stress_label']}):")
        print(f"  {'N':>3} {'K':>3} {'stress SR':>10} {'stress CAGR%':>13} {'stress maxDD%':>14} "
              f"{'bench SR':>9} {'basket SR':>10} {'n_obs':>6}")
        for _, r in sub.sort_values(["N", "K"]).iterrows():
            print(f"  {int(r['N']):>3} {int(r['K']):>3} {r['stress_sharpe']:>+10.3f} "
                  f"{r['stress_cagr_pct']:>13.2f} {r['stress_maxDD_pct']:>14.1f} "
                  f"{r['stress_bench_sharpe']:>+9.3f} {r['stress_basket_sharpe']:>+10.3f} "
                  f"{int(r['stress_n_obs']):>6}")

        n_surv = int(sub["SURVIVOR"].sum())
        print(f"\n  GATE TALLY ({name}): guard {int(sub['guard'].sum())}/{len(sub)} | "
              f"Sharpe>0 {int((sub['sharpe'] > 0).sum())}/{len(sub)} | "
              f"DSR>{DSR_BAR} {int((sub['dsr'] > DSR_BAR).sum())}/{len(sub)} | "
              f"not concentrated {int(sub['not_concentrated'].sum())}/{len(sub)} | "
              f"beats bench {int(sub['beats_bench'].sum())}/{len(sub)} | "
              f"beats basket {int(sub['beats_basket'].sum())}/{len(sub)} | "
              f"SURVIVORS {n_surv}/{len(sub)}")
        if n_surv:
            print(f"  *** {n_surv} SURVIVOR(S) in {name} — genuinely new evidence, verify before trusting. ***")
        else:
            print(f"  KILL in {name}: 0/{len(sub)} survivors.")

    print(f"\n  Cumulative project trials after this batch: {cumulative} ({PRIOR_TRIALS} prior + {n_batch} generalization cells)")
    print("  " + "=" * (W - 4))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
