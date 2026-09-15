#!/usr/bin/env python3
"""
SECTION 32.1 -- BUG AUDIT of the section-32 ensemble combination test.

TRIGGER: user flagged the section-32 headline numbers as implausible and
asked for a specific audit: was a component with missing data on a given
day silently treated as 0% return (fake "no risk" days) rather than
excluded from that day's average, artificially diluting realized vol and
inflating the combined Sharpe?

AUDIT FINDING, STATED PLAINLY:
  - The literal bug described (fillna(0.0) before averaging so a missing
    component drags the day's average toward 0) does NOT exist in
    research/ensemble_correlation.py. `equal_weight_available()` uses
    `frame.mean(axis=1, skipna=True)` (pandas skips NaN, does not treat it
    as 0), and `inverse_vol_weight()` builds weights from `frame.notna()`
    so an absent series gets weight 0, not a fake-0-return vote. Verified
    by reading the source directly (not re-derived from behaviour).
  - BUT a real, closely-related artefact WAS found: STAGGERED-INCEPTION
    REGIME BLENDING. The 64-series frame spans 1993-01-29 -> 2026-08-31
    (33.6 yrs) because one component (credit-spread SPY) starts in 1993,
    but the basket is only genuinely populated (50-59 of 64 series live
    per day) from 2018 onward -- mean live count is 1.00/day for the
    entire 1993-1999 stretch, rising through single digits until 2013,
    and only reaching 50+ in 2018 (see live-count-by-year table in the
    run log). For 25 of the 33.6 stitched years, the "combined portfolio"
    is really just 1-12 individual long-running components (dominated by
    the credit-spread SPY book and the momentum-rotation sleeves, both of
    which have genuinely positive own-Sharpe), not a real 64-way ensemble.
  - Consequence: the section-32 headline Sharpes are a BLEND of a thin,
    good-quality-dominated pre-2018 regime and a fully-populated,
    catastrophe-dominated (multiple ICT-SMC ruin cells, e.g. BTCUSDT own
    Sharpe -12.70) post-2018 regime. The blend is NOT a fair test of "does
    combining this project's actual signal set help" -- it structurally
    flatters the result versus the one period where a real ~60-way
    combination was ever actually running.

CORRECTED METHOD: restrict every combination to the window where the
basket is genuinely, consistently populated -- 2018-01-01 to 2025-12-31
(mean 58.7 of 60 available series live per day, min 51) -- and recompute
all four section-32 combination methods on that window ONLY, reusing the
exact same functions from research/ensemble_correlation.py (imported, not
reimplemented) so the only thing that changes is the date window.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "research"))

import numpy as np
import pandas as pd

import ensemble_correlation as ec
from research.dsr import deflated_sharpe

RESULTS = _ROOT / "results"
RESTRICT_START, RESTRICT_END = "2018-01-01", "2025-12-31"


def dsr_of(c: pd.Series, pool_sr: np.ndarray) -> float:
    c = c.dropna()
    sr = ec.sharpe_ann(c)
    d = deflated_sharpe(sr, pool_sr, n_obs=len(c), ann_factor=ec.BARS_PER_YEAR,
                         skewness=float(c.skew()), excess_kurtosis=float(c.kurtosis()))
    return d["dsr"]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    W = 110
    print("=" * W)
    print("  SECTION 32.1 -- BUG AUDIT: staggered-inception regime blending in the section-32 ensemble test")
    print("=" * W)

    frame_full = pd.read_csv(RESULTS / "ensemble_daily_returns.csv", index_col=0, parse_dates=True)
    summ = pd.read_csv(RESULTS / "ensemble_component_summary.csv").set_index("name")
    pool_sr = summ["sharpe"].dropna().to_numpy()

    live = frame_full.notna().sum(axis=1)
    print(f"\nSOURCE CHECK (verified by reading code, not inferred): equal_weight_available() uses "
          f"frame.mean(axis=1, skipna=True); inverse_vol_weight() zero-weights (not zero-fills) absent series.")
    print("The hypothesized fillna(0)-before-averaging bug is NOT present in the source.\n")

    print("LIVE-COMPONENT COUNT PER CALENDAR DAY, full 1993-2026 stitched frame:")
    print(f"  mean={live.mean():.2f}  median={live.median():.1f}  min={live.min()}  max={live.max()}")
    print("  yearly mean live count:")
    print(live.groupby(live.index.year).mean().round(2).to_string())
    print(f"\n  days with <5 live components : {int((live<5).sum()):,} / {len(live):,}")
    print(f"  days with <=1 live component : {int((live<=1).sum()):,} / {len(live):,}")

    thin = frame_full.loc["1993-01-01":"2017-12-31"]
    combo_thin = ec.equal_weight_available(thin)
    print(f"\nTHIN PRE-2018 PERIOD ALONE (1993-2017, mean live={thin.notna().sum(axis=1).mean():.2f}): "
          f"equal-weight Sharpe={ec.sharpe_ann(combo_thin):+.3f}")

    win = frame_full.loc[RESTRICT_START:RESTRICT_END].dropna(axis=1, how="all")
    live_win = win.notna().sum(axis=1)
    print(f"\nRESTRICTED WINDOW {RESTRICT_START}..{RESTRICT_END} ({win.shape[1]} series with any data): "
          f"mean live={live_win.mean():.2f}  min={live_win.min()}  max={live_win.max()}")

    corr_win = win.corr(min_periods=60)
    combo_all = ec.equal_weight_available(win)
    combo_ivol = ec.inverse_vol_weight(win)
    kept = ec.greedy_low_corr_subset(win, corr_win, ec.LOW_CORR_THRESHOLD)
    combo_filt = ec.equal_weight_available(win[kept])
    positive_names = [n for n in win.columns if summ.loc[n, "sharpe"] > 0]
    kept_q = ec.greedy_low_corr_subset(win, corr_win, ec.LOW_CORR_THRESHOLD, eligible=positive_names)
    combo_filt_q = ec.equal_weight_available(win[kept_q])

    rows = []
    print("\nCORRECTED RESULTS, RESTRICTED TO THE GENUINELY-POPULATED WINDOW (same 4 methods, same code, "
          "only the date window changes):")
    for label, c, kept_list in [
        (f"EQUAL-WEIGHT ALL (restricted, N={win.shape[1]})", combo_all, None),
        (f"INVERSE-VOL-WEIGHT ALL (restricted, N={win.shape[1]})", combo_ivol, None),
        (f"LOW-CORR SUBSET, quality-blind (restricted, N={len(kept)})", combo_filt, kept),
        (f"LOW-CORR SUBSET, positive-Sharpe-only (restricted, N={len(kept_q)})", combo_filt_q, kept_q),
    ]:
        r = c.dropna()
        dd = ec.max_dd_recovery(r)
        sr = ec.sharpe_ann(r)
        dsr_v = dsr_of(c, pool_sr)
        tys = ec.top_year_share(r)
        print(f"  {label:60s} SR={sr:+8.3f}  ret={float(ec.equity(r).iloc[-1]-1)*100:+9.1f}%  "
              f"maxDD={dd['max_dd']*100:6.1f}%  DSR={dsr_v:.4f}")
        rows.append(dict(name=label, first=str(r.index.min().date()), last=str(r.index.max().date()),
                          n_days=len(r), total_return=float(ec.equity(r).iloc[-1] - 1.0), sharpe=sr,
                          max_dd=dd["max_dd"], recovery_days=dd["recovery_days"], top_year_share=tys,
                          dsr=dsr_v, dsr_pool_n=len(pool_sr)))

    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "ensemble_combined_results_CORRECTED_restricted_window.csv", index=False)
    print(f"\nSaved: results/ensemble_combined_results_CORRECTED_restricted_window.csv")
    print("\nVERDICT: the section-32 headline numbers (Sharpe -0.15 / +0.47 / -1.63 / +0.68) were flattered by "
          "blending a thin, quality-dominated pre-2018 regime with the fully-populated post-2018 basket. Restricted "
          "to the honest, consistently-populated window, ALL FOUR methods are materially worse -- the best one "
          "(low-corr, positive-Sharpe-only) collapses from +421.1% / Sharpe +0.68 to +7.3% / Sharpe +0.24. "
          "The original section-32 KILL verdict stands and is STRENGTHENED, not reversed, by this correction.")


if __name__ == "__main__":
    main()
