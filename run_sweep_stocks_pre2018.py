#!/usr/bin/env python3
"""
run_sweep_stocks_pre2018.py — the OUT-OF-REGIME test of the individual-
stocks sweep. STATE_OF_PLAY section 7 rule 3: a candidate must clear a real
held-out window BEFORE anything from run_sweep_stocks.py is believed.

THE DESIGN RULE — same as every other out-of-regime driver in this repo
(run_sweep_m1_pre2018.py, run_orb_pre2018.py, run_sneaky_pivot_pre2018.py,
run_basket_pre2018.py): this file contains NO strategy logic, NO cost model
and NO scoring code. It imports run_sweep_stocks as a module, rebinds a
handful of module-level names (the window, the OOS split, the output paths,
the banner label, PRIOR_TRIALS), and calls its main(). Every object that
decides a number is the SAME OBJECT the 2018-2025 run used.

WHAT DIFFERS, AND WHY (forced by data depth, not chosen)
------------------------------------------------------------
Window 2010-01-01 -> 2017-12-31. All 6 tickers have clean daily data back to
2010 (scripts/download_us_stocks.py), so unlike crypto (data starts
2017-08), individual stocks get the SAME kind of genuine multi-year holdout
FX/indices got, not a re-sliced regime split. This window contains the 2011
US-downgrade selloff, the 2015-16 China/oil growth scare, and 2018's own
Q4 selloff is deliberately excluded from THIS window (it belongs to the
in-regime file) — same convention section 9.3 used with 2013-2017.
OOS split: 2016-01-01, matching every other out-of-regime driver's own
internal split convention.

TRIAL ACCOUNTING (stated explicitly)
--------------------------------------
    728  project total before this file        (638 prior + 90 crypto)
   + 90  stocks in regime, 6 tickers            (run_sweep_stocks.py)
   + 90  stocks out of regime, 6 tickers        (this file)
   = 908 cumulative

Usage:  python run_sweep_stocks_pre2018.py            (out-of-regime run + comparison)
        python run_sweep_stocks_pre2018.py --analyze  (re-score from CSV)
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import pandas as pd

import run_sweep_stocks as rss

IN_REGIME = _ROOT / "results" / "sweep_stocks.csv"
OUT_OF_REGIME = _ROOT / "results" / "sweep_stocks_pre2018.csv"
KEYS = ["instrument", "family", "variant"]


def run_out_of_regime() -> None:
    rss.WINDOW_START = pd.Timestamp("2010-01-01", tz="UTC")
    rss.WINDOW_END = pd.Timestamp("2017-12-31", tz="UTC")
    rss.OOS_SPLIT = pd.Timestamp("2016-01-01", tz="UTC")
    rss.WINDOW_LABEL = "2010-2017 OUT OF REGIME"
    rss.OUT_CSV = OUT_OF_REGIME
    rss.SCORED_CSV = _ROOT / "results" / "sweep_stocks_pre2018_scored.csv"
    rss.PRIOR_TRIALS = 818  # 728 + 90 in-regime stocks cells now prior
    rss.PRIOR_CSVS = list(rss.PRIOR_CSVS) + ["sweep_stocks_scored.csv"]
    print("\n" + "#" * 100)
    print("#  OUT OF REGIME — 2010-01-01 -> 2017-12-31, the same 6 tickers, 90 cells")
    print("#" * 100, flush=True)
    rss.main()


def compare() -> None:
    if not (IN_REGIME.exists() and OUT_OF_REGIME.exists()):
        print("\n  (comparison skipped — need both result files)")
        return
    old = pd.read_csv(IN_REGIME)
    new = pd.read_csv(OUT_OF_REGIME)
    old["variant"] = old["variant"].astype(str)
    new["variant"] = new["variant"].astype(str)
    m = old.merge(new, on=KEYS, suffixes=("_in", "_out"))
    if m.empty:
        print("\n  (comparison skipped — no matching cells)")
        return

    W = 128
    print("\n" + "=" * W)
    print("  OUT-OF-REGIME COMPARISON — same code, same cells, only the data window changes")
    print("  IN  = 2018-2025    OUT = 2010-2017")
    print("=" * W)
    print(f"  {'inst':>5} {'family':<9} {'v':>1} "
          f"{'grPF in':>8} {'grPF out':>9} {'d':>7} | "
          f"{'netPF in':>9} {'netPF out':>10} | {'SR in':>8} {'SR out':>8} | "
          f"{'costR% in':>10} {'out':>6} | {'n out':>7}")
    print("  " + "-" * (W - 4))
    for _, r in m.sort_values("gross_pf_in", ascending=False).iterrows():
        print(f"  {r['instrument']:>5} {r['family']:<9} {r['variant']:>1} "
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
          f"{m['cost_R_mean_out'].mean() * 100:.1f}%")

    holds = m[(m["gross_pf_in"] > 1) & (m["gross_pf_out"] > 1)]
    net_holds = m[(m["net_pf_in"] > 1) & (m["net_pf_out"] > 1)
                  & (m["sharpe_in"] > 0) & (m["sharpe_out"] > 0)]
    print(f"\n  CELLS POSITIVE-GROSS IN BOTH WINDOWS : {len(holds)}/{n}"
          + ("" if holds.empty else "  -> " + ", ".join(
              f"{r['instrument']}/{r['family']}/v{r['variant']}" for _, r in holds.iterrows())))
    print(f"  CELLS NET-PROFITABLE IN BOTH WINDOWS : {len(net_holds)}/{n}"
          + ("" if net_holds.empty else "  -> " + ", ".join(
              f"{r['instrument']}/{r['family']}/v{r['variant']}" for _, r in net_holds.iterrows())))
    print("=" * W)


def main() -> None:
    if "--analyze" not in sys.argv:
        run_out_of_regime()
    compare()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
