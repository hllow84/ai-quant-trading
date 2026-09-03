#!/usr/bin/env python3
"""
momentum_rotation_frequency.py -- REBALANCE-FREQUENCY sweep for the
cross-sectional momentum rotation (STATE_OF_PLAY sec 12 / 12.1 / 12.3).

QUESTION (settled here with real data, not inferred): which rebalancing
frequency produces the HIGHEST ACTUAL HISTORICAL COMPOUNDED RETURN for the
audited momentum rotation -- full period, and in the 2000-2009 stress window?

WHAT IS HELD FIXED (the audited mechanism, byte-identical across all 5 freqs):
  - N = 12-month trailing-return ranking lookback
  - K = 5 equal-weighted holdings
  - 200-day causal SMA market filter on SPY (risk-off -> 100% IEF)
  - base 17-instrument universe (SECTOR_ETFS + ASSET_ETFS), SPY benchmark-only
  - causal execution lag: signal at close(t), trade at close(t+1), first live
    return close(t+2)/close(t+1)-1  (research.momentum_rotation.build_weights)
  - look-ahead guard (research.momentum_rotation.look_ahead_guard)

WHAT CHANGES: only the cadence at which a new allocation decision is made,
via build_weights(signal_freq=..., rebalance_step=...):
    weekly     = signal_freq="W", rebalance_step=1
    bi-weekly  = signal_freq="W", rebalance_step=2
    monthly    = signal_freq="M", rebalance_step=1   (existing baseline, reused)
    bi-monthly = signal_freq="M", rebalance_step=2   (existing, audit 8, reused)
    quarterly  = signal_freq="M", rebalance_step=3   (NEW)

COSTS scale with ACTUAL turnover, NOT a flat per-frequency assumption. The
per-side transaction cost is the SAME 3 bps/side (2 bps spread + 1 bp
commission-equivalent, research.momentum_rotation.COST_BPS_PER_SIDE) that
sec 12 used -- it is a property of the instrument/order, not the calendar.
research.momentum_rotation.simulate() charges cost_bps * turnover at every
rebalance, so a higher-frequency schedule pays that cost MORE OFTEN and its
total cost-as-%-of-gross rises automatically. Verified in the output table.

METHODOLOGY = the audit-1-corrected (STATE_OF_PLAY sec 12.1) live-window
approach: every metric is computed from each config's own first execution
date onward (no zero-padded pre-trading history), and SPY buy-and-hold is
sliced to the IDENTICAL window for every comparison. Two windows are
reported per frequency:
  - OWN live window   : first_exec(freq) .. panel end     -- for the honest
    per-frequency vs-SPY comparison (each freq crosses its lookback+SMA
    threshold on a slightly different date).
  - COMMON window     : max(first_exec over all 5 freqs) .. panel end -- an
    apples-to-apples head-to-head so the 5 frequencies are ranked over
    exactly the same dates.
  - STRESS window     : 2000-01-01 .. 2009-12-31 (sits inside every freq's
    live window, so no padding issue).

HONESTY GATES (all reported; DSR is REFERENCE ONLY, not a survival gate, per
the task brief): look-ahead guard, cost-inclusive net returns with real
frequency-scaled costs, Deflated Sharpe vs the 5-frequency a priori pool,
per-year concentration (top-year share of net log return), out-of-regime
(2000-2009) performance, and vs buy-and-hold SPY over the identical period.

TRIALS: weekly, bi-weekly, quarterly are 3 genuinely new frequencies x
2 windows (full + stress) = 6 new trials. Monthly and bi-monthly are reused
(monthly is part of the sec-12 8-cell batch already counted; bi-monthly was
run as a one-shot robustness check in audit 8 and is folded in here without
re-running). Cumulative project trial count 1043 -> 1049.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.metrics import sharpe, max_drawdown
from research.dsr import deflated_sharpe, expected_max_sharpe
from research.momentum_rotation import (
    UNIVERSE, BENCHMARK, build_weights, simulate, look_ahead_guard,
    COST_BPS_PER_SIDE,
)

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)

BARS_PER_YEAR = 252
N_MONTHS = 12
TOP_K = 5
STRESS_START = pd.Timestamp("2000-01-01")
STRESS_END = pd.Timestamp("2009-12-31")
PRIOR_TRIALS = 1043

FREQS = [
    ("weekly",     dict(signal_freq="W", rebalance_step=1), "NEW"),
    ("bi-weekly",  dict(signal_freq="W", rebalance_step=2), "NEW"),
    ("monthly",    dict(signal_freq="M", rebalance_step=1), "reused (sec 12 baseline)"),
    ("bi-monthly", dict(signal_freq="M", rebalance_step=2), "reused (audit 8)"),
    ("quarterly",  dict(signal_freq="M", rebalance_step=3), "NEW"),
]


def load_panel() -> pd.DataFrame:
    return pd.read_csv(DATA / "momentum_universe_adjclose.csv", index_col=0, parse_dates=True).sort_index()


def window_metrics(ret: pd.Series) -> dict:
    ret = ret.dropna()
    equity = (1 + ret).cumprod()
    years = len(ret) / BARS_PER_YEAR
    total_ret = float(equity.iloc[-1] / equity.iloc[0] - 1.0)
    cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else float("nan")
    log_ret = np.log1p(ret)
    yearly = log_ret.groupby(ret.index.year).sum()
    total_log = float(yearly.sum())
    top_year_share = float(yearly.abs().max() / abs(total_log)) if total_log != 0 else float("nan")
    return dict(
        n_obs=len(ret), years=years,
        vol_ann_pct=float(ret.std(ddof=1) * np.sqrt(BARS_PER_YEAR) * 100),
        sharpe=float(sharpe(ret, BARS_PER_YEAR)),
        cagr_pct=float(cagr * 100), total_return_pct=total_ret * 100,
        maxDD_pct=float(max_drawdown(equity) * 100),
        top_year=int(yearly.abs().idxmax()) if len(yearly) else -1,
        top_year_share_pct=top_year_share * 100,
    )


def cost_pct_of_gross(gross_ret: pd.Series, net_ret: pd.Series) -> float:
    g = (1 + gross_ret.dropna()).prod() - 1.0
    n = (1 + net_ret.dropna()).prod() - 1.0
    return float((1 - n / g) * 100) if g not in (0.0,) and np.isfinite(g) else float("nan")


def spy_window(adjclose: pd.DataFrame, start, end) -> dict:
    px = adjclose[BENCHMARK]
    if start is not None:
        px = px[px.index >= start]
    if end is not None:
        px = px[px.index <= end]
    return window_metrics(px.pct_change().dropna())


def main():
    adjclose = load_panel()
    spy_ret_all = adjclose[BENCHMARK].pct_change().dropna()
    print("=" * 120)
    print(f"  REBALANCE-FREQUENCY SWEEP  --  momentum rotation, N={N_MONTHS} / K={TOP_K} / 200d SMA filter / "
          f"base {len(UNIVERSE)}-instrument universe")
    print(f"  cost model: {COST_BPS_PER_SIDE:.1f} bps/side (SAME every frequency) applied to ACTUAL turnover "
          f"at each rebalance -> total cost scales with cadence")
    print(f"  panel: {adjclose.index[0].date()} -> {adjclose.index[-1].date()}  ({len(adjclose):,} daily rows)")
    print("=" * 120)

    # ---- build every frequency once over the full panel ----
    built = {}
    for name, kw, tag in FREQS:
        we, to = build_weights(adjclose, N_MONTHS, TOP_K, **kw)
        guard = look_ahead_guard(we, adjclose, N_MONTHS)
        sim = simulate(adjclose, we, to, cost_bps_per_side=COST_BPS_PER_SIDE)
        built[name] = dict(we=we, to=to, sim=sim, guard=guard, first_exec=we.index[0], tag=tag, kw=kw)
        print(f"  {name:11s} [{tag:24s}] rebalances={len(we):4d}  first_exec={we.index[0].date()}  "
              f"guard={'PASS' if guard else 'FAIL'}  mean_turnover/rebal={float(to.mean()):.3f}  "
              f"total_turnover={float(to.sum()):.1f}")

    common_start = max(b["first_exec"] for b in built.values())
    print(f"\n  COMMON head-to-head window starts {common_start.date()} "
          f"(= latest first_exec across the 5 frequencies)\n")

    rows = []
    for name, kw, tag in FREQS:
        b = built[name]
        sim = b["sim"]
        gross, net = sim["gross"], sim["net"]

        own = window_metrics(net[net.index >= b["first_exec"]])
        own_gross = gross[gross.index >= b["first_exec"]]
        own["cost_pct_of_gross"] = cost_pct_of_gross(own_gross, net[net.index >= b["first_exec"]])
        spy_own = spy_window(adjclose, b["first_exec"], None)

        com = window_metrics(net[net.index >= common_start])
        com_gross = gross[gross.index >= common_start]
        com["cost_pct_of_gross"] = cost_pct_of_gross(com_gross, net[net.index >= common_start])
        spy_com = spy_window(adjclose, common_start, None)

        st_mask = (net.index >= STRESS_START) & (net.index <= STRESS_END)
        stress = window_metrics(net[st_mask])
        stress["cost_pct_of_gross"] = cost_pct_of_gross(gross[(gross.index >= STRESS_START) & (gross.index <= STRESS_END)],
                                                        net[st_mask])
        spy_stress = spy_window(adjclose, STRESS_START, STRESS_END)

        rows.append(dict(
            frequency=name, tag=tag, n_rebalances=len(b["we"]),
            first_exec=str(b["first_exec"].date()), guard="PASS" if b["guard"] else "FAIL",
            total_turnover=float(b["to"].sum()),
            # OWN live window
            own_net_cagr_pct=own["cagr_pct"], own_net_sharpe=own["sharpe"],
            own_maxDD_pct=own["maxDD_pct"], own_cost_pct_of_gross=own["cost_pct_of_gross"],
            own_total_return_pct=own["total_return_pct"], own_top_year_share_pct=own["top_year_share_pct"],
            own_vs_spy_cagr_pp=own["cagr_pct"] - spy_own["cagr_pct"],
            own_vs_spy_sharpe=own["sharpe"] - spy_own["sharpe"],
            own_beats_spy_totret=own["total_return_pct"] > spy_own["total_return_pct"],
            own_spy_cagr_pct=spy_own["cagr_pct"], own_spy_total_return_pct=spy_own["total_return_pct"],
            # COMMON window (head-to-head ranking)
            com_net_cagr_pct=com["cagr_pct"], com_net_sharpe=com["sharpe"], com_maxDD_pct=com["maxDD_pct"],
            com_cost_pct_of_gross=com["cost_pct_of_gross"], com_total_return_pct=com["total_return_pct"],
            com_vs_spy_cagr_pp=com["cagr_pct"] - spy_com["cagr_pct"],
            com_beats_spy_totret=com["total_return_pct"] > spy_com["total_return_pct"],
            # STRESS
            stress_net_cagr_pct=stress["cagr_pct"], stress_net_sharpe=stress["sharpe"],
            stress_maxDD_pct=stress["maxDD_pct"], stress_cost_pct_of_gross=stress["cost_pct_of_gross"],
            stress_total_return_pct=stress["total_return_pct"],
            stress_vs_spy_cagr_pp=stress["cagr_pct"] - spy_stress["cagr_pct"],
            stress_beats_spy_totret=stress["total_return_pct"] > spy_stress["total_return_pct"],
            _n_obs_own=own["n_obs"], _n_obs_stress=stress["n_obs"],
        ))

    df = pd.DataFrame(rows)

    # ---- DSR, REFERENCE ONLY: pool = the 5 frequencies' own net Sharpes ----
    for wtag, col, nobs_col in [("COMMON full", "com_net_sharpe", "_n_obs_own"),
                                ("STRESS", "stress_net_sharpe", "_n_obs_stress")]:
        pool = df[col].to_numpy(dtype=float)
        emax, Npool, mu, sd = expected_max_sharpe(pool)
        dsr_vals = []
        for _, r in df.iterrows():
            d = deflated_sharpe(float(r[col]), pool, n_obs=int(r[nobs_col]), ann_factor=BARS_PER_YEAR)["dsr"]
            dsr_vals.append(d)
        df[f"dsr_{wtag.split()[0].lower()}"] = dsr_vals
        print(f"  DSR REFERENCE ONLY [{wtag}]  pool=5 freqs  E[max SR]={emax:+.3f} (mu {mu:+.3f}, sd {sd:.3f})  "
              f"-> DSR " + ", ".join(f"{n}={v:.3f}" for n, v in zip(df['frequency'], dsr_vals)))

    df.to_csv(RESULTS / "momentum_rotation_frequency_summary.csv", index=False)

    spy_com = spy_window(adjclose, common_start, None)
    spy_stress = spy_window(adjclose, STRESS_START, STRESS_END)

    # ================= THE ONE TABLE =================
    W = 120
    print("\n\n" + "#" * W)
    print(f"  FREQUENCY x (net CAGR, net Sharpe, maxDD, cost % of gross, out-of-regime, vs buy-and-hold SPY)")
    print(f"  COMMON head-to-head window: {common_start.date()} -> {adjclose.index[-1].date()}   "
          f"|   STRESS: 2000-01-01 -> 2009-12-31")
    print("#" * W)
    hdr = (f"  {'frequency':<11} {'reb':>5} {'netCAGR':>8} {'netSR':>7} {'maxDD':>7} {'cost%gr':>8} "
           f"{'totRet%':>10} | {'strCAGR':>8} {'strSR':>7} {'strTot%':>9} {'strMDD':>7} | {'vsSPY(f)':>9} {'vsSPY(s)':>9}")
    print(hdr)
    print("  " + "-" * (W - 2))
    for _, r in df.iterrows():
        print(f"  {r['frequency']:<11} {r['n_rebalances']:>5d} {r['com_net_cagr_pct']:>7.2f}% "
              f"{r['com_net_sharpe']:>7.3f} {r['com_maxDD_pct']:>6.1f}% {r['com_cost_pct_of_gross']:>7.2f}% "
              f"{r['com_total_return_pct']:>9.1f}% | {r['stress_net_cagr_pct']:>7.2f}% {r['stress_net_sharpe']:>7.3f} "
              f"{r['stress_total_return_pct']:>8.1f}% {r['stress_maxDD_pct']:>6.1f}% | "
              f"{r['com_vs_spy_cagr_pp']:>+8.2f} {r['stress_vs_spy_cagr_pp']:>+8.2f}")
    print("  " + "-" * (W - 2))
    print(f"  {'SPY B&H':<11} {'':>5} {spy_com['cagr_pct']:>7.2f}% {spy_com['sharpe']:>7.3f} "
          f"{spy_com['maxDD_pct']:>6.1f}% {'--':>7} {spy_com['total_return_pct']:>9.1f}% | "
          f"{spy_stress['cagr_pct']:>7.2f}% {spy_stress['sharpe']:>7.3f} {spy_stress['total_return_pct']:>8.1f}% "
          f"{spy_stress['maxDD_pct']:>6.1f}% |")

    # per-frequency OWN-window vs-SPY (the honest per-freq comparison)
    print("\n  Per-frequency OWN live window (each freq vs SPY over its own identical dates):")
    print(f"  {'frequency':<11} {'from':>12} {'netCAGR':>8} {'SPY CAGR':>9} {'vs pp':>7} {'netSR':>7} "
          f"{'SPY SR':>7} {'totRet%':>10} {'SPY tot%':>10} {'beats?':>7}")
    for _, r in df.iterrows():
        print(f"  {r['frequency']:<11} {r['first_exec']:>12} {r['own_net_cagr_pct']:>7.2f}% "
              f"{r['own_spy_cagr_pct']:>8.2f}% {r['own_vs_spy_cagr_pp']:>+6.2f} {r['own_net_sharpe']:>7.3f} "
              f"{r['own_net_sharpe'] - r['own_vs_spy_sharpe']:>7.3f} {r['own_total_return_pct']:>9.1f}% "
              f"{r['own_spy_total_return_pct']:>9.1f}% {str(bool(r['own_beats_spy_totret'])):>7}")

    # ================= RANKINGS =================
    print("\n\n" + "=" * W)
    print("  RANKING BY ACTUAL COMPOUNDED HISTORICAL RETURN")
    print("=" * W)
    full_rank = df.sort_values("com_total_return_pct", ascending=False)
    print(f"\n  FULL PERIOD (common window {common_start.date()} -> {adjclose.index[-1].date()}), "
          f"ranked by total compounded NET return:")
    for i, (_, r) in enumerate(full_rank.iterrows(), 1):
        print(f"   {i}. {r['frequency']:<11} {r['com_total_return_pct']:>10.1f}%   "
              f"(net CAGR {r['com_net_cagr_pct']:.2f}%, net SR {r['com_net_sharpe']:.3f}, "
              f"maxDD {r['com_maxDD_pct']:.1f}%, cost {r['com_cost_pct_of_gross']:.2f}% of gross)")
    print(f"      SPY buy-and-hold over the same window: {spy_com['total_return_pct']:.1f}% "
          f"(CAGR {spy_com['cagr_pct']:.2f}%, SR {spy_com['sharpe']:.3f})")

    stress_rank = df.sort_values("stress_total_return_pct", ascending=False)
    print(f"\n  STRESS WINDOW (2000-01-01 -> 2009-12-31), ranked by total compounded NET return:")
    for i, (_, r) in enumerate(stress_rank.iterrows(), 1):
        print(f"   {i}. {r['frequency']:<11} {r['stress_total_return_pct']:>10.1f}%   "
              f"(net CAGR {r['stress_net_cagr_pct']:.2f}%, net SR {r['stress_net_sharpe']:.3f}, "
              f"maxDD {r['stress_maxDD_pct']:.1f}%, cost {r['stress_cost_pct_of_gross']:.2f}% of gross)")
    print(f"      SPY buy-and-hold over the same window: {spy_stress['total_return_pct']:.1f}% "
          f"(CAGR {spy_stress['cagr_pct']:.2f}%, SR {spy_stress['sharpe']:.3f})")

    win_full = full_rank.iloc[0]["frequency"]
    win_stress = stress_rank.iloc[0]["frequency"]
    print("\n" + "=" * W)
    print("  PLAIN ANSWER")
    print("=" * W)
    print(f"  Highest actual compounded return, FULL PERIOD  : {win_full.upper()}")
    print(f"  Highest actual compounded return, STRESS WINDOW: {win_stress.upper()}")
    print(f"  Does the answer change between the calm full period and the 2000-2009 crash window? "
          f"{'YES' if win_full != win_stress else 'NO'}")
    print(f"\n  NEW trials this run: 3 frequencies (weekly, bi-weekly, quarterly) x 2 windows = 6")
    print(f"  CUMULATIVE PROJECT TRIALS: {PRIOR_TRIALS} + 6 = {PRIOR_TRIALS + 6}")
    print(f"\n  saved -> {RESULTS / 'momentum_rotation_frequency_summary.csv'}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
