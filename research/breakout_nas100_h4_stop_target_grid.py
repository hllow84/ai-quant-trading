"""
breakout_nas100_h4_stop_target_grid.py — NAS100 H4 breakout-retest: joint
lookback (N) x stop (k_atr) x target (R) x hold (H) grid, direct extension
of §45's method (research/breakout_us30_h4_stop_target_grid.py) to the
second instrument in the breakout family with a genuinely positive
baseline Sharpe.

BASELINE (results/sweep_indices_scored.csv, 2026-07-21 sweep): NAS100 H4
breakout_retest variant 1 (N=50, k_atr=1.0, R=2.0, H=48): grossPF 1.156,
netPF 1.104, Sharpe +0.102, maxDD 15.2%, 347 trades — the only genuinely
positive NAS100 breakout cell across all 5 timeframes tested for this
instrument (H1/M30/M15/M5 all net Sharpe <= -0.05, confirmed by re-reading
sweep_indices_scored.csv directly). Weaker than US30 H4's own baseline
(+0.400, §45) but real (net PF > 1) and never independently swept — same
justification as §45. Uses N=50/H=48 geometry (not US30's N=20/H=24),
following §43's precedent that different instruments in the same family
can have different starting geometries.

MECHANISM: identical a priori reasoning as §45 (N trades level-significance
vs frequency, k_atr trades noise-absorption vs loss size, R is genuinely
open for this signal type) — not re-derived here.

METHOD: reuses research/breakout_us30_h4_stop_target_grid.py's score()/
run_cell() unchanged, only the data path and grid center differ.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import pandas as pd

from research.gold_data import load_m1_spot, load_m1_mid, resample_mid, aggregate_daily
from research.breakout_us30_h4_stop_target_grid import score, run_cell, BARS_PER_YEAR
from research.dsr import deflated_sharpe

RESULTS = _ROOT / "results"
DATA = _ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv"
PRIOR_TRIALS = 1523


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    m1 = load_m1_mid(DATA)
    daily_index = aggregate_daily(load_m1_spot(DATA)).index
    m = resample_mid(m1, "4h")
    print(f"NAS100 H4 bars: {len(m):,}, {m.index[0]} -> {m.index[-1]}\n")

    rows = []

    print("=== Grid 1: N x k_atr x R, H=48 fixed (baseline geometry) ===\n")
    for N in (30, 50, 70):
        for k_atr in (0.75, 1.0, 1.5):
            for R in (1.5, 2.0, 3.0):
                is_baseline = (N == 50 and k_atr == 1.0 and R == 2.0)
                label = f"N{N}_katr{k_atr}_R{R}" + (" [BASELINE, repro-only]" if is_baseline else "")
                run_cell(m, daily_index, N, k_atr, R, 48, label, rows, is_baseline)

    print("Grid 1 best (excl. baseline): N70/k_atr1.0/R2.0, Sharpe=+0.366 "
          "-- hits the N grid edge (70 is the highest N tested)\n")

    print("=== Extension: follow the N/k_atr/R/H gradient past the grid-1 edge ===\n")
    extension_cells = [
        # round 1: is N=70 a real edge or an artifact? push N further, probe
        # k_atr/R around the grid-1 best
        (90, 1.0, 2.0, 48), (110, 1.0, 2.0, 48), (70, 0.5, 2.0, 48),
        (70, 1.0, 1.75, 48), (70, 1.0, 2.5, 48), (90, 0.75, 2.0, 48), (90, 1.25, 2.0, 48),
        # round 2: N=70 confirmed as a real interior peak (N90/N110 both
        # worse); R=1.75 beat R=2.0 -- fine-tune R and k_atr around the new
        # peak, and check N/H sensitivity there
        (70, 1.0, 1.6, 48), (70, 1.0, 1.65, 48), (70, 1.0, 1.9, 48),
        (70, 0.85, 1.75, 48), (70, 1.15, 1.75, 48), (60, 1.0, 1.75, 48), (80, 1.0, 1.75, 48),
        (70, 1.0, 1.75, 36), (70, 1.0, 1.75, 60),
        # round 3: H=60 beat H=48 -- sweep H further at the confirmed
        # N=70/k_atr=1.0/R=1.75 peak
        (70, 1.0, 1.75, 72), (70, 1.0, 1.75, 84), (70, 1.0, 1.75, 90),
        (70, 1.0, 1.75, 96), (70, 1.0, 1.75, 120),
    ]
    for N, k_atr, R, H in extension_cells:
        label = f"EXT_N{N}_katr{k_atr}_R{R}_H{H}"
        run_cell(m, daily_index, N, k_atr, R, H, label, rows)

    df = pd.DataFrame(rows)
    out = RESULTS / "breakout_nas100_h4_stop_target_grid.csv"
    df.to_csv(out, index=False)
    print(f"Saved {out}")

    new_rows = df[~df["is_baseline"]]
    sharpes = new_rows["sharpe"].tolist()
    print(f"\n=== Deflated Sharpe (local grid+extension pool, N={len(sharpes)}) ===")
    for _, r in new_rows.sort_values("sharpe", ascending=False).head(10).iterrows():
        d = deflated_sharpe(r["sharpe"], sharpes, n_obs=r["n_trades"], ann_factor=BARS_PER_YEAR)
        print(f"  {r['label']}: Sharpe={r['sharpe']:+.3f}  DSR={d['dsr']:.4f}  pool_n={d['pool_n']}")

    print(f"\nTrial count: {len(new_rows)} new. Cumulative N={PRIOR_TRIALS} -> {PRIOR_TRIALS + len(new_rows)}")


if __name__ == "__main__":
    main()
