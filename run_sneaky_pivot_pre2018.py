#!/usr/bin/env python3
"""
run_sneaky_pivot_pre2018.py — the out-of-regime test of Strategy 2.

STATE_OF_PLAY §7 rule 3: a candidate must clear the out-of-regime re-run BEFORE
anything else is believed. This is that run for the 15-minute Sneaky Pivot, and
it is built the same way `run_basket_pre2018.py` was built for the index basket —
the test that actually killed the last lead.

THE DESIGN RULE, AND WHY IT LOOKS LIKE THIS
-------------------------------------------
This file contains NO strategy logic, NO cost model and NO scoring code. It
imports `run_sneaky_pivot` as a module and rebinds four module-level names —
the data files, the OOS split date, the output paths, and the banner label —
then calls its `main()`. Everything that decides a number (`sneaky_pivot`,
`score`, `simulate_trades`, `analyze`, the cost model, the gates) is the SAME
OBJECT the 2018-2025 run used, not a copy that could drift.

That matters more than it sounds. The whole value of an out-of-regime test is
that only the data window changes. A re-implementation that is 99% identical
proves nothing, because the 1% is exactly where a favourable difference would
hide. If you need to change the strategy, change `strategies/sneaky_pivot.py`
and re-run BOTH windows.

WHAT DIFFERS FROM THE IN-REGIME RUN, AND WHY (all forced, none chosen)
----------------------------------------------------------------------
1. **16 configs, not 24.** There is no pre-2018 M1 for spot gold in this repo,
   so XAUUSD drops out. The comparison below is therefore restricted to the 16
   index cells on both sides. Gold was a stated robustness instrument anyway,
   never a headline.
2. **OOS split 2016-01-01, not 2023-01-01.** Matches the split used by the
   pre-2018 basket test (~53/47 of the window), so the two out-of-regime studies
   in this project are read the same way.
3. **RTH-only source files.** `*_M1RTH_2013_2017_*` covers 13:00-21:00 UTC only,
   because that is all the pre-2018 Dukascopy archive holds. Verified 2026-08-21
   against the partial download: EST days reach 15:59 ET and EDT days reach
   16:00 ET, so the FULL 09:30-16:00 session is present in both halves of the
   year — median 370 (EST) / 390 (EDT) bars per session. The strategy restricts
   itself to RTH regardless, so the signal definition is identical in both
   windows. **Caveat:** buy-and-hold is computed from daily bars aggregated over
   whatever the file holds, so the pre-2018 benchmark samples RTH close vs the
   in-regime file's 23-hour close. That shifts the benchmark's sampling point,
   not the strategy's.
4. **DSR pool is this batch's own 16 cells**, computed by the inherited
   `analyze()` from the batch itself. The convention is unchanged: structural
   pool is the headline, the project-cumulative pool is contrast only
   (`research/dsr.py` BUG 2).

COSTS BITE HARDER OUT OF REGIME -- BUT NOT FOR THE REASON FIRST RECORDED
------------------------------------------------------------------------
An earlier note here, written from the PARTIAL download (2013-09 -> 2015-01),
said spreads were 2.5x wider out of regime (5.71 vs 2.31 bps) and put cost at
21-25% of 1R. The finished pull corrects both numbers:

    NAS100 median spread   2018-2025:  3.224 pts = 2.31 bps
                           2013-2017:  1.062 pts = 2.39 bps   <- essentially EQUAL

    cost as % of 1R        2018-2025:  5.8 - 6.8%
                           2013-2017:  15 - 17%               (~2.5x)

Spreads were wide in 2013-2014 and tightened through 2015-2017; the partial
window caught only the wide half. Over the full window spreads are the same as
in regime, so the cost gap is NOT a spread story -- it is a STOP-DISTANCE story.
1R is the sneaky candle's own range, and 2013-2017 was a low-volatility grind, so
stops are ~2.5x tighter in relative terms and an unchanged spread eats 2.5x more
of them. Same vice as STATE_OF_PLAY section 1, arrived at from the other side.

The consequence for reading this run is unchanged: net numbers are structurally
penalised out of regime, so the verdict rests on GROSS PF.

WHAT WOULD COUNT AS SURVIVING
-----------------------------
The bar is NOT "positive". The index basket posted Sharpe +1.04 in regime and
-0.28 out of it, with gross PF collapsing 1.363 -> 1.006. The question here is
whether the Sneaky Pivot's one genuinely novel property — gross PF > 1 in EVERY
cell — is a property of the strategy or of 2018-2025. So the headline number is
**how many of the 16 index cells keep gross PF > 1**, and the headline failure
mode is a gross-PF collapse toward 1.00, which would mean the edge was never
there before costs.

Usage:  py -3.14 run_sneaky_pivot_pre2018.py
        py -3.14 run_sneaky_pivot_pre2018.py --analyze   (re-score, no reload)
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import pandas as pd

import run_sneaky_pivot as rsp

# ── the four rebindings — this is the entire difference ──────────────────────
PRE_INSTRUMENTS = {
    "NAS100": (_ROOT / "data" / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv", rsp.COST_BPS),
    "US30":   (_ROOT / "data" / "US30_M1RTH_2013_2017_cfd_dukascopy.csv",   rsp.COST_BPS),
}

rsp.INSTRUMENTS = PRE_INSTRUMENTS
rsp.OOS_SPLIT = pd.Timestamp("2016-01-01", tz="UTC")
rsp.WINDOW_LABEL = "2013-2017 OUT OF REGIME"
rsp.OUT_CSV = _ROOT / "results" / "sneaky_pivot_pre2018.csv"
rsp.SCORED_CSV = _ROOT / "results" / "sneaky_pivot_scored_pre2018.csv"
rsp.TRADES_CSV = _ROOT / "results" / "sneaky_pivot_trades_pre2018.csv"

# The 24 in-regime cells are now prior trials for the cumulative CONTRAST pool.
rsp.PRIOR_TRIALS = 459
rsp.PRIOR_CSVS = list(rsp.PRIOR_CSVS) + ["sneaky_pivot.csv"]

IN_REGIME_CSV = _ROOT / "results" / "sneaky_pivot.csv"
KEYS = ["instrument", "target", "stop", "trigger"]


def compare() -> None:
    """In-regime vs out-of-regime, cell by cell. This is the actual verdict."""
    if not (IN_REGIME_CSV.exists() and rsp.OUT_CSV.exists()):
        print("\n  (comparison skipped — need both result files)")
        return

    old = pd.read_csv(IN_REGIME_CSV)
    new = pd.read_csv(rsp.OUT_CSV)
    old = old[old["instrument"].isin(PRE_INSTRUMENTS)]
    m = old.merge(new, on=KEYS, suffixes=("_in", "_out"))
    if m.empty:
        print("\n  (comparison skipped — no matching cells)")
        return

    W = 118
    print("\n" + "=" * W)
    print("  OUT-OF-REGIME COMPARISON — same code, same 16 index cells, only the data window changes")
    print("  IN  = 2018-2025 (results/sneaky_pivot.csv)   OUT = 2013-2017 (this run)")
    print("=" * W)
    print(f"  {'inst':>6} {'target':>6} {'stop':>6} {'trig':>7} "
          f"{'grPF in':>8} {'grPF out':>9} {'d':>7} | "
          f"{'netPF in':>9} {'netPF out':>10} | {'SR in':>7} {'SR out':>7} {'d':>7} | {'n out':>6}")
    print("  " + "-" * (W - 4))
    for _, r in m.sort_values("sharpe_in", ascending=False).iterrows():
        print(f"  {r['instrument']:>6} {r['target']:>6} {r['stop']:>6} {r['trigger']:>7} "
              f"{r['gross_pf_in']:>8.3f} {r['gross_pf_out']:>9.3f} "
              f"{r['gross_pf_out'] - r['gross_pf_in']:>+7.3f} | "
              f"{r['net_pf_in']:>9.3f} {r['net_pf_out']:>10.3f} | "
              f"{r['sharpe_in']:>+7.2f} {r['sharpe_out']:>+7.2f} "
              f"{r['sharpe_out'] - r['sharpe_in']:>+7.2f} | {int(r['n_trades_out']):>6}")
    print("=" * W)

    n = len(m)
    gross_in = int((m["gross_pf_in"] > 1).sum())
    gross_out = int((m["gross_pf_out"] > 1).sum())
    net_out = int((m["net_pf_out"] > 1).sum())
    sr_out = int((m["sharpe_out"] > 0).sum())
    print(f"\n  gross PF > 1 :  {gross_in}/{n} in regime  ->  {gross_out}/{n} out of regime")
    print(f"  net   PF > 1 :  {int((m['net_pf_in'] > 1).sum())}/{n}  ->  {net_out}/{n}")
    print(f"  net Sharpe>0 :  {int((m['sharpe_in'] > 0).sum())}/{n}  ->  {sr_out}/{n}")
    print(f"  mean gross PF:  {m['gross_pf_in'].mean():.3f}  ->  {m['gross_pf_out'].mean():.3f}")
    print(f"  mean Sharpe  :  {m['sharpe_in'].mean():+.3f}  ->  {m['sharpe_out'].mean():+.3f}")

    best = m.loc[m["sharpe_in"].idxmax()]
    print(f"\n  IN-REGIME BEST CELL — {best['instrument']} tgt={best['target']} "
          f"stop={best['stop']} trig={best['trigger']}")
    print(f"    gross PF {best['gross_pf_in']:.3f} -> {best['gross_pf_out']:.3f}   "
          f"net PF {best['net_pf_in']:.3f} -> {best['net_pf_out']:.3f}   "
          f"Sharpe {best['sharpe_in']:+.2f} -> {best['sharpe_out']:+.2f}")

    print("\n  HOW TO READ THIS (write the verdict against these lines, not against a hope):")
    print("    * The novel claim was gross PF > 1 in EVERY cell. If that holds out of regime,")
    print("      the edge is a property of the strategy. If gross PF collapses toward 1.00,")
    print("      it was 2018-2025 — the exact failure that killed the index basket (1.363 -> 1.006).")
    print("    * Sharpe falling while gross PF holds is a COST/regime-vol story, not an edge story.")
    print("    * Sign flips on the best cell matter more than the mean: the mean is dragged by")
    print("      cells nobody would trade.")
    print("=" * W)


def main() -> None:
    missing = [str(p.name) for _, (p, _) in PRE_INSTRUMENTS.items() if not p.exists()]
    if missing and "--analyze" not in sys.argv:
        print("MISSING pre-2018 data: " + ", ".join(missing))
        print("scripts/download_pre2018_m1.mjs must finish and pass its gate first.")
        raise SystemExit(2)

    if "--analyze" in sys.argv:
        rsp.analyze_only()
    else:
        rsp.main()
    compare()


if __name__ == "__main__":
    main()
