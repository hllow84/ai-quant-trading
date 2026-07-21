#!/usr/bin/env python3
"""
recompute_dsr.py — JOB 1: recompute DSR for the prior index run with a WORKING gate.

Reruns nothing. Takes results/sweep_indices_scored.csv as-is and recomputes the
haircut under a corrected DSR (research/dsr.py), so we can see whether the H4
trend/macross edge is actually significant once the discriminator works.

Reports four specifications side by side, so the effect of each fix is visible
rather than asserted:

  (0) OLD          — broken SE + contaminated 237-trial pool   [what we had]
  (1) FIX SE ONLY  — corrected annualised SE, same 237 pool
  (2) STRUCTURAL   — corrected SE + a priori pool (swing TF x trend families)
                     <- the headline gate
  (3) FLOOR        — corrected SE + Sharpe >= -1.0 pool
                     <- sensitivity only; selects on outcome, biased toward passing

The structural pool is stated BEFORE looking at which spec lets anything pass:
timeframes H1+H4, families trend+macross+momentum. Rationale: the search that
produced the lead was for a swing trend-following system. M5/M15/M30 were known
cost-dominated from the gold work before this batch ran, and meanrev/breakout
are not trend families. That is the set we were genuinely selecting from.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

from research.dsr import deflated_sharpe, expected_max_sharpe, floor_pool, structural_pool

RESULTS = _ROOT / "results"
DSR_BAR = 0.95

# Stated a priori — see module docstring.
STRUCT_TF = ["H1", "H4"]
STRUCT_FAM = ["trend", "macross", "momentum"]
FLOOR = -1.0


def old_dsr(sr, n_obs, skew, ekurt, pool):
    """Reproduce the OLD (broken) calculation exactly, for contrast."""
    e_max, N, _, _ = expected_max_sharpe(pool)
    sr_pp = sr / np.sqrt(max(n_obs, 1))
    var = (1 + (1 - skew * sr_pp + (ekurt / 4) * sr_pp ** 2)) / max(n_obs, 1)
    return float(stats.norm.cdf((sr - e_max) / np.sqrt(max(var, 1e-12)))), e_max


def main():
    idx = pd.read_csv(RESULTS / "sweep_indices_scored.csv")
    prior = pd.concat([
        pd.read_csv(RESULTS / "sweep_progress.csv")["sharpe"],
        pd.read_csv(RESULTS / "htf_breakout.csv")["sharpe"],
    ])
    prior_sr = pd.to_numeric(prior, errors="coerce").dropna().to_numpy()
    full_pool = np.concatenate([prior_sr, idx["sharpe"].fillna(0.0).to_numpy()])

    struct = structural_pool(idx, STRUCT_TF, STRUCT_FAM)
    flr = floor_pool(full_pool, FLOOR)

    W = 116
    print("=" * W)
    print("  JOB 1 — DSR GATE REPAIR")
    print("=" * W)
    print("\n  TWO independent defects were found, not one:\n")
    print("  BUG 1  Units inconsistency in the standard error.")
    print("         Numerator was annualised Sharpe; denominator was the PER-PERIOD SE.")
    print("         SE came out ~10.8x too small, so DSR was a step function at E[max SR]:")
    print("         0.0000 below it, 1.0000 above, nothing in between. That is why every")
    print("         study in this repo reported DSR of exactly 0 or exactly 1.")
    print("         Fixed: all quantities annualised; Mertens (2002) variance restored.")
    print("\n  BUG 2  Contaminated deflation pool.")
    print("         E[max SR] scales with the pool STD. The 237-trial pool included M5")
    print("         configs down to Sharpe -14.6, structurally doomed by cost-to-risk.")
    print("         The haircut was being set by how badly the WORST configs failed.")
    print("         Fixed: pool stated explicitly (structural, a priori).")

    print("\n" + "-" * W)
    print("  DEFLATION POOLS")
    print("-" * W)
    for name, pool, note in [
        ("full 237 (old)", full_pool, "every config ever run - contaminated"),
        (f"structural", struct, f"TF {STRUCT_TF} x families {STRUCT_FAM}, a priori"),
        (f"floor >= {FLOOR}", flr, "selects on OUTCOME - sensitivity only"),
    ]:
        e_max, N, mu, sd = expected_max_sharpe(pool)
        print(f"  {name:<16} N={N:>4}  mean={mu:>+7.3f}  std={sd:>6.3f}  ->  E[max SR]={e_max:>+7.3f}   ({note})")

    print(f"\n  Cumulative trial count remains 237 (75 sweep + 12 HTF + 150 index).")
    print(f"  The pool is which trials DEFLATE the winner, not how many were run.")

    # ── recompute for the prior top index configs ──
    top = idx.sort_values("sharpe", ascending=False).head(15).copy()

    print("\n" + "=" * W)
    print(f"  RECOMPUTED DSR — TOP 15 INDEX CONFIGS FROM THE PRIOR RUN   (bar: DSR > {DSR_BAR})")
    print("=" * W)
    print(f"  {'inst':>6} {'TF':>3} {'family':<9} {'v':>1} {'Sharpe':>7} {'nobs':>5} "
          f"{'(0)OLD':>7} {'(1)SEfix':>8} {'(2)STRUCT':>9} {'(3)FLOOR':>8}  {'z_struct':>8} {'verdict':>9}")
    print("  " + "-" * (W - 4))

    rows = []
    for _, r in top.iterrows():
        sr, n = float(r["sharpe"]), int(r["n_obs"])
        sk, ek = float(r["skew"]), float(r["ekurt"])
        d_old, _ = old_dsr(sr, n, sk, ek, full_pool)
        d_se = deflated_sharpe(sr, full_pool, n, skewness=sk, excess_kurtosis=ek)
        d_st = deflated_sharpe(sr, struct, n, skewness=sk, excess_kurtosis=ek)
        d_fl = deflated_sharpe(sr, flr, n, skewness=sk, excess_kurtosis=ek)
        verdict = "PASS" if d_st["dsr"] > DSR_BAR else "fail"
        print(f"  {r['instrument']:>6} {r['timeframe']:>3} {r['family']:<9} {int(r['variant']):>1} "
              f"{sr:>+7.2f} {n:>5} {d_old:>7.4f} {d_se['dsr']:>8.4f} {d_st['dsr']:>9.4f} "
              f"{d_fl['dsr']:>8.4f}  {d_st['z']:>+8.2f} {verdict:>9}")
        rows.append(dict(instrument=r["instrument"], timeframe=r["timeframe"],
                         family=r["family"], variant=r["variant"], sharpe=sr, n_obs=n,
                         dsr_old=d_old, dsr_se_fixed=d_se["dsr"],
                         dsr_structural=d_st["dsr"], dsr_floor=d_fl["dsr"],
                         z_structural=d_st["z"], e_max_structural=d_st["e_max_sr"],
                         se_ann=d_st["se_ann"]))

    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "dsr_recomputed.csv", index=False)

    n_pass = int((out["dsr_structural"] > DSR_BAR).sum())
    best = out.iloc[0]
    st_e_max = best["e_max_structural"]

    print("=" * W)
    print("\n  IS THE H4 EDGE SIGNIFICANT ONCE THE GATE WORKS?")
    print("  " + "-" * (W - 4))
    print(f"  Configs clearing DSR > {DSR_BAR} under the structural pool: {n_pass} / 15")
    print(f"  Best config: {best['instrument']} {best['timeframe']} {best['family']} "
          f"v{int(best['variant'])}, Sharpe {best['sharpe']:+.2f}")
    print(f"    structural E[max SR] = {st_e_max:+.3f}   annualised SE = {best['se_ann']:.3f}")
    print(f"    z = ({best['sharpe']:+.2f} - {st_e_max:+.2f}) / {best['se_ann']:.3f} = {best['z_structural']:+.2f}"
          f"   ->  DSR = {best['dsr_structural']:.4f}")
    if n_pass == 0:
        print(f"\n  NO config clears the corrected gate. The edge is NOT statistically")
        print(f"  significant once multiple testing is accounted for properly.")
        print(f"  Note this is now a REAL measurement, not the saturated 0.0000 from before:")
        print(f"  the fixed DSR spreads across the range instead of collapsing to 0/1.")
    else:
        print(f"\n  {n_pass} config(s) clear the corrected structural gate — these are")
        print(f"  genuine candidates and must still pass OOS + benchmark tests.")
    print("=" * W)
    print(f"\n  Written -> {RESULTS / 'dsr_recomputed.csv'}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
