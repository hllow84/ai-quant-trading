#!/usr/bin/env python3
"""
run_orb_pre2018.py — the OUT-OF-REGIME test of the Opening Range Breakout.

STATE_OF_PLAY section 7 rule 3: a candidate must clear the out-of-regime re-run
BEFORE anything else is believed. This is that run for ORB, built exactly the way
run_basket_pre2018.py and run_sneaky_pivot_pre2018.py were built — the two tests
that actually decided the last two verdicts in this project.

THE DESIGN RULE
---------------
This file contains NO strategy logic, NO cost model and NO scoring code. It
imports run_orb as a module and rebinds five module-level names — the data files,
the OOS split date, the output paths, the prior-trial bookkeeping and the banner
label — then calls its main(). Every object that decides a number (orb, score,
simulate_trades, slip_bps, analyze, the gates) is the SAME OBJECT the 2018-2025
run used, not a copy that could drift. If the strategy needs changing, change
strategies/orb.py and re-run BOTH windows.

WHAT DIFFERS, AND WHY (all forced, none chosen)
------------------------------------------------
1. **Window 2013-09-30 -> 2017-12-29.** That is the earliest date the Dukascopy
   index M1 archive supports with a real bid AND ask (STATE_OF_PLAY section 6).
   2008 and 2011 are unreachable; this window still contains the 2014 oil crash,
   the 2015 China Black Monday and 2016 Brexit.
2. **OOS split 2016-01-01, not 2023-01-01** — the same split the other two
   out-of-regime studies in this project use, so all three are read the same way.
3. **RTH-only source files.** The *_M1RTH_2013_2017_* files hold 13:00-21:00 UTC
   only, because that is all the pre-2018 archive contains. That is a real
   restriction for a 23-hour strategy and NO restriction at all for this one: ORB
   lives entirely inside 09:30-16:00 ET. scripts/verify_orb_sessions.py confirms
   from the data that the 09:30 ET bar is present on 98.5%/98.9% of sessions and
   the 15:59 ET boundary is reached on 96%.
   **Caveat, stated not hidden:** buy-and-hold is computed from daily bars
   aggregated over whatever each file holds, so the pre-2018 benchmark samples an
   RTH close while the in-regime file samples a 23-hour close. That shifts the
   BENCHMARK's sampling point, not the strategy's.
4. **Same 12 cells.** Both windows have M1 for NAS100 and US30, so unlike the
   Sneaky Pivot test (which lost gold) the grid is identical on both sides and
   the comparison is exactly like-for-like.

WHAT WOULD COUNT AS SURVIVING
-----------------------------
The bar is not "positive". The index basket posted Sharpe +1.04 in regime and
-0.28 out of it, with gross PF collapsing 1.363 -> 1.006 — its edge was gone
before costs. The Sneaky Pivot kept 14/16 cells gross-positive and still failed
on cost, concentration and buy-and-hold. So read this run in that order:

  * gross PF out of regime — is the raw effect a property of the strategy or of
    2018-2025? A collapse toward 1.00 is the basket's death, repeated.
  * net PF and cost_R% — the Sneaky Pivot's death: a real effect too small to
    pay for itself once stop distances shrink in a low-vol regime.
  * single-year concentration — the signature shared by BOTH previous failures.
  * vs buy-and-hold, in this window too.

Usage:  py -3.14 run_orb_pre2018.py
        py -3.14 run_orb_pre2018.py --analyze
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

import run_orb as ro

# ── the rebindings — this is the entire difference ───────────────────────────
PRE_INSTRUMENTS = {
    "NAS100": (_ROOT / "data" / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv", ro.COST_BPS),
    "US30":   (_ROOT / "data" / "US30_M1RTH_2013_2017_cfd_dukascopy.csv",   ro.COST_BPS),
}

ro.INSTRUMENTS = PRE_INSTRUMENTS
ro.OOS_SPLIT = pd.Timestamp("2016-01-01", tz="UTC")
ro.WINDOW_LABEL = "2013-2017 OUT OF REGIME"
ro.OUT_CSV = _ROOT / "results" / "orb_pre2018.csv"
ro.SCORED_CSV = _ROOT / "results" / "orb_scored_pre2018.csv"
ro.TRADES_CSV = _ROOT / "results" / "orb_trades_pre2018.csv"

# The 12 in-regime cells are now prior trials for the cumulative CONTRAST pool.
ro.PRIOR_TRIALS = 487
ro.PRIOR_CSVS = list(ro.PRIOR_CSVS) + ["orb.csv"]

IN_REGIME_CSV = _ROOT / "results" / "orb.csv"
KEYS = ["instrument", "or_minutes", "target"]


def compare() -> None:
    """In-regime vs out-of-regime, cell by cell. This is the actual verdict."""
    if not (IN_REGIME_CSV.exists() and ro.OUT_CSV.exists()):
        print("\n  (comparison skipped — need both result files)")
        return

    old = pd.read_csv(IN_REGIME_CSV)
    new = pd.read_csv(ro.OUT_CSV)
    old = old[old["instrument"].isin(PRE_INSTRUMENTS)]
    m = old.merge(new, on=KEYS, suffixes=("_in", "_out"))
    if m.empty:
        print("\n  (comparison skipped — no matching cells)")
        return

    W = 126
    print("\n" + "=" * W)
    print("  OUT-OF-REGIME COMPARISON — same code, same 12 cells, only the data window changes")
    print("  IN  = 2018-2025 (results/orb.csv)   OUT = 2013-09-30 -> 2017-12-29 (this run)")
    print("=" * W)
    print(f"  {'inst':>6} {'OR':>3} {'target':>6} "
          f"{'grPF in':>8} {'grPF out':>9} {'d':>7} | "
          f"{'netPF in':>9} {'netPF out':>10} | {'SR in':>7} {'SR out':>7} {'d':>7} | "
          f"{'costR% in':>10} {'out':>6} | {'n out':>6}")
    print("  " + "-" * (W - 4))
    for _, r in m.sort_values("sharpe_in", ascending=False).iterrows():
        print(f"  {r['instrument']:>6} {int(r['or_minutes']):>3} {r['target']:>6} "
              f"{r['gross_pf_in']:>8.3f} {r['gross_pf_out']:>9.3f} "
              f"{r['gross_pf_out'] - r['gross_pf_in']:>+7.3f} | "
              f"{r['net_pf_in']:>9.3f} {r['net_pf_out']:>10.3f} | "
              f"{r['sharpe_in']:>+7.2f} {r['sharpe_out']:>+7.2f} "
              f"{r['sharpe_out'] - r['sharpe_in']:>+7.2f} | "
              f"{r['cost_R_mean_in'] * 100:>9.1f}% {r['cost_R_mean_out'] * 100:>5.1f}% | "
              f"{int(r['n_trades_out']):>6}")
    print("=" * W)

    n = len(m)
    print(f"\n  gross PF > 1 :  {int((m['gross_pf_in'] > 1).sum())}/{n} in regime  ->  "
          f"{int((m['gross_pf_out'] > 1).sum())}/{n} out of regime")
    print(f"  net   PF > 1 :  {int((m['net_pf_in'] > 1).sum())}/{n}  ->  "
          f"{int((m['net_pf_out'] > 1).sum())}/{n}")
    print(f"  net Sharpe>0 :  {int((m['sharpe_in'] > 0).sum())}/{n}  ->  "
          f"{int((m['sharpe_out'] > 0).sum())}/{n}")
    print(f"  mean gross PF:  {m['gross_pf_in'].mean():.3f}  ->  {m['gross_pf_out'].mean():.3f}")
    print(f"  mean Sharpe  :  {m['sharpe_in'].mean():+.3f}  ->  {m['sharpe_out'].mean():+.3f}")
    print(f"  mean cost_R  :  {m['cost_R_mean_in'].mean() * 100:.1f}%  ->  "
          f"{m['cost_R_mean_out'].mean() * 100:.1f}%   "
          f"(median 1R: {m['risk_med_bps_in'].mean():.0f} bps -> "
          f"{m['risk_med_bps_out'].mean():.0f} bps)")

    best = m.loc[m["sharpe_in"].idxmax()]
    print(f"\n  IN-REGIME BEST CELL — {best['instrument']} OR{int(best['or_minutes'])} "
          f"tgt={best['target']}")
    print(f"    gross PF {best['gross_pf_in']:.3f} -> {best['gross_pf_out']:.3f}   "
          f"net PF {best['net_pf_in']:.3f} -> {best['net_pf_out']:.3f}   "
          f"Sharpe {best['sharpe_in']:+.2f} -> {best['sharpe_out']:+.2f}")

    # A cell only counts as holding up if it stays through BOTH windows.
    holds = m[(m["gross_pf_in"] > 1) & (m["gross_pf_out"] > 1)]
    net_holds = m[(m["net_pf_in"] > 1) & (m["net_pf_out"] > 1)
                  & (m["sharpe_in"] > 0) & (m["sharpe_out"] > 0)]
    print(f"\n  CELLS POSITIVE-GROSS IN BOTH WINDOWS : {len(holds)}/{n}")
    print(f"  CELLS NET-PROFITABLE IN BOTH WINDOWS : {len(net_holds)}/{n}"
          + ("" if net_holds.empty else "  -> " + ", ".join(
              f"{r['instrument']}/OR{int(r['or_minutes'])}/{r['target']}"
              for _, r in net_holds.iterrows())))

    print("\n  HOW TO READ THIS (write the verdict against these lines, not against a hope):")
    print("    * A gross PF that collapses toward 1.00 means the edge was 2018-2025, not the")
    print("      strategy — the exact failure that killed the index basket (1.363 -> 1.006).")
    print("    * Sharpe falling while gross PF holds is a COST/regime-vol story, not an edge")
    print("      story — that is what the Sneaky Pivot turned out to be.")
    print("    * A survivor must be net-profitable in BOTH windows, not merely gross-positive.")
    print("=" * W)


def main() -> None:
    missing = [p.name for _, (p, _) in PRE_INSTRUMENTS.items() if not p.exists()]
    if missing and "--analyze" not in sys.argv:
        print("MISSING pre-2018 data: " + ", ".join(missing))
        raise SystemExit(2)

    if "--analyze" in sys.argv:
        ro.analyze_only()
    else:
        ro.main()
    compare()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
