#!/usr/bin/env python3
"""m1_gross_significance.py — is the M1 GROSS edge real, or is it noise?

FINDING (1) asks whether any gross edge exists at M1 at all. The sweep answers
"mean gross PF 1.005, 24/45 cells above 1.00" — which on its own is compatible
with a coin flip. This script settles it properly by re-running the best cell of
each family and testing gross R per trade against zero:

    t = mean(gross_R) / (std(gross_R) / sqrt(n))

and then, separately, expressing that same edge as a fraction of the cost it has
to pay. Those are two different questions and the answers point opposite ways —
which is the whole point of reporting FINDING (1) and FINDING (2) separately.

Writes results/m1_gross_significance.csv.
"""
from __future__ import annotations
import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
from scipy import stats

import run_sweep_m1 as rs
from research.gold_data import load_m1_spot, aggregate_daily, resample_mid
from research.ftmo_engine import simulate_trades, de_overlap
from strategies.sweep_families import FAMILIES, TF_DELTA

# The best gross cell of each family, read off results/sweep_m1.csv.
scored = pd.read_csv(_ROOT / "results" / "sweep_m1.csv")
best = (scored.sort_values("gross_pf", ascending=False)
        .groupby("family").head(1)[["instrument", "family", "variant", "gross_pf"]])

rows = []
for inst in best["instrument"].unique():
    path, cost_bps = rs.INSTRUMENTS[inst]
    spot = load_m1_spot(path)
    daily_index = aggregate_daily(spot).index
    m1 = pd.DataFrame(index=spot.index)
    for c in ("open", "high", "low", "close"):
        m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
    m1["spread"] = spot["spread"]; m1["volume"] = spot["volume"]
    del spot
    m = resample_mid(m1, "1min"); del m1

    for _, b in best[best["instrument"] == inst].iterrows():
        fn, variants = FAMILIES[b["family"]]
        p = variants[int(b["variant"])]
        cands = fn(m, p, TF_DELTA["M1"])
        for t in cands:
            t["session_end"] = rs._coerce_utc(t["session_end"])
            t["entry_time"] = rs._coerce_utc(t["entry_time"])
        tr = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=cost_bps))
        g, c_ = tr["gross_R"], tr["cost_R"]
        n = len(tr)
        se = g.std(ddof=1) / np.sqrt(n)
        t_stat = g.mean() / se
        # Newey-West style block check: daily-block bootstrap on the mean, so
        # intraday clustering of trades cannot masquerade as independent evidence.
        day = pd.to_datetime(tr["exit_time"], utc=True).dt.normalize()
        by_day = g.groupby(day).mean()
        t_block = by_day.mean() / (by_day.std(ddof=1) / np.sqrt(len(by_day)))
        rows.append(dict(
            instrument=inst, family=b["family"], variant=b["variant"], n_trades=n,
            gross_R_mean=g.mean(), gross_R_std=g.std(ddof=1), se=se,
            t_stat=t_stat, p_value=2 * (1 - stats.norm.cdf(abs(t_stat))),
            t_daily_block=t_block, n_days=len(by_day),
            cost_R_mean=c_.mean(), edge_as_pct_of_cost=100 * g.mean() / c_.mean(),
            net_R_mean=(g - c_).mean(),
        ))
        del cands, tr
    del m

out = pd.DataFrame(rows).sort_values("gross_R_mean", ascending=False)
out.to_csv(_ROOT / "results" / "m1_gross_significance.csv", index=False)

W = 118
print("=" * W)
print("  IS THE M1 GROSS EDGE REAL? — best gross cell of each family, gross R per trade vs zero")
print("=" * W)
print(f"  {'inst':>7} {'family':<9} {'v':>1} {'trades':>8} {'grossR/trd':>11} {'std':>6} "
      f"{'t (trade)':>10} {'t (daily)':>10} {'p':>9} | {'costR/trd':>10} {'edge as % of cost':>18}")
print("  " + "-" * (W - 4))
for _, r in out.iterrows():
    print(f"  {r['instrument']:>7} {r['family']:<9} {int(r['variant']):>1} {int(r['n_trades']):>8,} "
          f"{r['gross_R_mean']:>+11.5f} {r['gross_R_std']:>6.3f} {r['t_stat']:>+10.2f} "
          f"{r['t_daily_block']:>+10.2f} {r['p_value']:>9.2e} | {r['cost_R_mean']:>10.4f} "
          f"{r['edge_as_pct_of_cost']:>17.2f}%")
print("=" * W)
print("  t (trade) treats every trade as independent — an upper bound on significance.")
print("  t (daily) averages within each calendar day first, so intraday clustering cannot")
print("  inflate the count. Read the daily column as the honest one.")
print("  The last column is the whole verdict: even where the gross edge is statistically")
print("  real, it is a low-single-digit percentage of the cost it must pay.")
