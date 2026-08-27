#!/usr/bin/env python3
"""
run_sweep_m1_pre2018.py — the OUT-OF-REGIME test of the M1 row.

STATE_OF_PLAY section 7 rule 3: a candidate must clear 2013-2017 BEFORE anything
else is believed. This is that run for the M1 sweep, built exactly the way
run_basket_pre2018.py, run_sneaky_pivot_pre2018.py and run_orb_pre2018.py were
built — the three tests that decided the last three verdicts in this project.

THE DESIGN RULE
---------------
This file contains NO strategy logic, NO cost model and NO scoring code. It
imports run_sweep_m1 as a module, rebinds a handful of module-level names — the
data files, the OOS split, the RTH switch, the output paths, the banner label —
and calls its main(). Every object that decides a number (the families, the
variant grid, score_config, simulate_trades, the gates, analyze) is the SAME
OBJECT the 2018-2025 run used, not a copy that could drift.

WHAT DIFFERS, AND WHY (all forced, none chosen)
------------------------------------------------
1. **Window 2013-09-30 -> 2017-12-29.** The earliest the Dukascopy index M1
   archive supports with a real bid AND ask (STATE_OF_PLAY sections 6 and 9.5).
   It contains the 2014 oil crash, the 2015 China Black Monday and 2016 Brexit.
2. **OOS split 2016-01-01, not 2023-01-01** — the same split the other three
   out-of-regime studies use, so all four are read the same way.
3. **Two instruments, not three.** XAUUSD has no pre-2018 M1 in the repo, so the
   grid is 2 x 5 x 3 = 30 cells rather than 45, and the comparison is restricted
   to the 30 index cells on both sides.
4. **RTH-only source files.** The *_M1RTH_2013_2017_* files hold [13:00, 21:00)
   UTC and nothing else — measured, 100% of bars in both files. For the
   session-agnostic sweep families that is a REAL restriction, not a cosmetic
   one: the in-regime files are 23-hour, so an unmatched comparison would be
   confounding session coverage with regime.

   **That is why this driver runs a MATCHED CONTROL first.** `--rth` re-runs the
   2018-2025 files restricted to the same [13:00, 21:00) UTC minutes, so the
   out-of-regime comparison is like-for-like on session as well as on code. The
   30 matched cells are a RE-SCORING of an already-counted grid on a data
   subset, exactly as STATE_OF_PLAY section 6 treated its matched 5-index
   window, and they are NOT double-counted in the cumulative trial total.

TRIAL ACCOUNTING (stated, because it is easy to get wrong)
-----------------------------------------------------------
    499  project total before this work            (STATE_OF_PLAY section 1)
   + 45  M1 in regime, 3 instruments               (run_sweep_m1.py)
   + 30  M1 out of regime, 2 instruments           (this file)
   = 574 cumulative
    (+30 RTH-matched control cells = re-scoring, NOT counted)

WHAT WOULD COUNT AS SURVIVING
-----------------------------
Read the comparison in this order, because it is the order the last three
candidates died in:

  * gross PF out of regime — is the raw effect a property of the strategy or of
    2018-2025? The index basket collapsed 1.363 -> 1.006; ORB inverted
    1.141 -> 0.960. A collapse toward or below 1.00 is that death repeated.
  * net PF and cost_R% — the Sneaky Pivot's death: a real effect too small to
    pay for itself once stop distances shrink in a low-vol regime. At M1 this is
    the mechanism most likely to dominate, and the in-regime run already
    measures cost_R far above the 20% band that killed M5.
  * single-year concentration — the signature shared by all three failures.
  * vs buy-and-hold, in this window too.

Usage:  py -3.14 run_sweep_m1_pre2018.py            (matched control + out of regime)
        py -3.14 run_sweep_m1_pre2018.py --analyze  (re-score both from CSV)
        py -3.14 run_sweep_m1_pre2018.py --skip-control
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

import run_sweep_m1 as rs

PRE_INSTRUMENTS = {
    "NAS100": (_ROOT / "data" / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv", rs.COST_BPS_INDEX),
    "US30":   (_ROOT / "data" / "US30_M1RTH_2013_2017_cfd_dukascopy.csv",   rs.COST_BPS_INDEX),
}

IN_REGIME_FULL = _ROOT / "results" / "sweep_m1.csv"
IN_REGIME_RTH = _ROOT / "results" / "sweep_m1_rth.csv"
OUT_OF_REGIME = _ROOT / "results" / "sweep_m1_pre2018.csv"

KEYS = ["instrument", "family", "variant"]


def run_matched_control() -> None:
    """The 2018-2025 files, restricted to the pre-2018 archive's own session."""
    rs.RTH_FILTER = True
    rs.INSTRUMENTS = {k: v for k, v in rs.INSTRUMENTS.items() if k != "XAUUSD"}
    rs.WINDOW_LABEL = "2018-2025 RTH-MATCHED CONTROL"
    rs.OOS_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
    rs.OUT_CSV = IN_REGIME_RTH
    rs.SCORED_CSV = _ROOT / "results" / "sweep_m1_rth_scored.csv"
    print("\n" + "#" * 100)
    print("#  MATCHED CONTROL — 2018-2025, restricted to [13:00,21:00) UTC")
    print("#  A RE-SCORING of an already-counted grid on a data subset. NOT new trials.")
    print("#" * 100, flush=True)
    rs.main()


def run_out_of_regime() -> None:
    rs.RTH_FILTER = False          # the pre-2018 files are ALREADY RTH-only
    rs.INSTRUMENTS = PRE_INSTRUMENTS
    rs.OOS_SPLIT = pd.Timestamp("2016-01-01", tz="UTC")
    rs.WINDOW_LABEL = "2013-2017 OUT OF REGIME"
    rs.OUT_CSV = OUT_OF_REGIME
    rs.SCORED_CSV = _ROOT / "results" / "sweep_m1_pre2018_scored.csv"
    # The 45 in-regime cells are now prior trials for the cumulative CONTRAST pool.
    rs.PRIOR_TRIALS = 544
    rs.PRIOR_CSVS = list(rs.PRIOR_CSVS) + ["sweep_m1.csv"]
    print("\n" + "#" * 100)
    print("#  OUT OF REGIME — 2013-09-30 -> 2017-12-29, the same 30 index cells")
    print("#" * 100, flush=True)
    rs.main()


def compare() -> None:
    """In-regime (RTH-matched) vs out-of-regime, cell by cell. The actual verdict."""
    base = IN_REGIME_RTH if IN_REGIME_RTH.exists() else IN_REGIME_FULL
    if not (base.exists() and OUT_OF_REGIME.exists()):
        print("\n  (comparison skipped — need both result files)")
        return
    matched = base == IN_REGIME_RTH

    old = pd.read_csv(base)
    new = pd.read_csv(OUT_OF_REGIME)
    old = old[old["instrument"].isin(PRE_INSTRUMENTS)]
    old["variant"] = old["variant"].astype(str)
    new["variant"] = new["variant"].astype(str)
    m = old.merge(new, on=KEYS, suffixes=("_in", "_out"))
    if m.empty:
        print("\n  (comparison skipped — no matching cells)")
        return

    W = 128
    print("\n" + "=" * W)
    print("  OUT-OF-REGIME COMPARISON — same code, same cells, only the data window changes")
    print(f"  IN  = 2018-2025 ({base.name}"
          + ("; RTH-MATCHED to [13:00,21:00) UTC so session coverage is not a confound)"
             if matched else "; FULL 23-hour session — NOT matched, read with care)"))
    print("  OUT = 2013-09-30 -> 2017-12-29 (RTH-only archive)")
    print("=" * W)
    print(f"  {'inst':>6} {'family':<9} {'v':>1} "
          f"{'grPF in':>8} {'grPF out':>9} {'d':>7} | "
          f"{'netPF in':>9} {'netPF out':>10} | {'SR in':>8} {'SR out':>8} | "
          f"{'costR% in':>10} {'out':>6} | {'n out':>7}")
    print("  " + "-" * (W - 4))
    for _, r in m.sort_values("gross_pf_in", ascending=False).iterrows():
        print(f"  {r['instrument']:>6} {r['family']:<9} {r['variant']:>1} "
              f"{r['gross_pf_in']:>8.3f} {r['gross_pf_out']:>9.3f} "
              f"{r['gross_pf_out'] - r['gross_pf_in']:>+7.3f} | "
              f"{r['net_pf_in']:>9.3f} {r['net_pf_out']:>10.3f} | "
              f"{r['sharpe_in']:>+8.2f} {r['sharpe_out']:>+8.2f} | "
              f"{r['cost_R_mean_in'] * 100:>9.1f}% {r['cost_R_mean_out'] * 100:>5.1f}% | "
              f"{int(r['n_trades_out']):>7,}")
    print("=" * W)

    n = len(m)
    print(f"\n  gross PF > 1 :  {int((m['gross_pf_in'] > 1).sum())}/{n} in regime  ->  "
          f"{int((m['gross_pf_out'] > 1).sum())}/{n} out of regime")
    print(f"  net   PF > 1 :  {int((m['net_pf_in'] > 1).sum())}/{n}  ->  "
          f"{int((m['net_pf_out'] > 1).sum())}/{n}")
    print(f"  net Sharpe>0 :  {int((m['sharpe_in'] > 0).sum())}/{n}  ->  "
          f"{int((m['sharpe_out'] > 0).sum())}/{n}")
    print(f"  mean gross PF:  {m['gross_pf_in'].mean():.4f}  ->  {m['gross_pf_out'].mean():.4f}")
    print(f"  mean net PF  :  {m['net_pf_in'].mean():.4f}  ->  {m['net_pf_out'].mean():.4f}")
    print(f"  mean Sharpe  :  {m['sharpe_in'].mean():+.3f}  ->  {m['sharpe_out'].mean():+.3f}")
    print(f"  mean cost_R  :  {m['cost_R_mean_in'].mean() * 100:.1f}%  ->  "
          f"{m['cost_R_mean_out'].mean() * 100:.1f}%   "
          f"(median 1R: {m['risk_med_bps_in'].mean():.1f} bps -> "
          f"{m['risk_med_bps_out'].mean():.1f} bps)")

    holds = m[(m["gross_pf_in"] > 1) & (m["gross_pf_out"] > 1)]
    net_holds = m[(m["net_pf_in"] > 1) & (m["net_pf_out"] > 1)
                  & (m["sharpe_in"] > 0) & (m["sharpe_out"] > 0)]
    print(f"\n  CELLS POSITIVE-GROSS IN BOTH WINDOWS : {len(holds)}/{n}"
          + ("" if holds.empty else "  -> " + ", ".join(
              f"{r['instrument']}/{r['family']}/v{r['variant']}" for _, r in holds.iterrows())))
    print(f"  CELLS NET-PROFITABLE IN BOTH WINDOWS : {len(net_holds)}/{n}"
          + ("" if net_holds.empty else "  -> " + ", ".join(
              f"{r['instrument']}/{r['family']}/v{r['variant']}" for _, r in net_holds.iterrows())))

    print("\n  WHERE THIS SITS AGAINST THE PROJECT'S OTHER OUT-OF-REGIME TESTS")
    print(f"  {'candidate':<34} {'mean gross PF in -> out':>26} {'cells holding':>16}")
    print("  " + "-" * 80)
    print(f"  {'Index trend basket (section 6)':<34} {'1.363 -> 1.006':>26} {'2/18':>16}")
    print(f"  {'Sneaky Pivot (section 9.4)':<34} {'1.321 -> 1.155':>26} {'14/16':>16}")
    print(f"  {'ORB @ cash open (section 10)':<34} {'1.141 -> 0.960':>26} {'2/12':>16}")
    swing = "%.3f -> %.3f" % (m["gross_pf_in"].mean(), m["gross_pf_out"].mean())
    print(f"  {'M1 sweep (this run)':<34} {swing:>26} {f'{len(holds)}/{n}':>16}")

    print("\n  HOW TO READ THIS (write the verdict against these lines, not against a hope):")
    print("    * gross PF collapsing toward 1.00 means the edge was 2018-2025, not the strategy.")
    print("    * Sharpe falling while gross PF holds is a COST/regime-vol story, not an edge story.")
    print("    * A survivor must be net-profitable in BOTH windows, not merely gross-positive.")
    print("    * At M1 specifically: if gross PF is ~1.00 in BOTH windows, the finding is not")
    print("      'the edge did not survive' — it is 'there was never a gross edge to survive'.")
    print("=" * W)


def main() -> None:
    analyze = "--analyze" in sys.argv
    if not analyze:
        missing = [p.name for _, (p, _) in PRE_INSTRUMENTS.items() if not p.exists()]
        if missing:
            print("MISSING pre-2018 M1 data: " + ", ".join(missing))
            raise SystemExit(2)
        if "--skip-control" not in sys.argv:
            run_matched_control()
        run_out_of_regime()
    compare()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
