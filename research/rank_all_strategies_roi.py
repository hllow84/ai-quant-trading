#!/usr/bin/env python3
"""
STATE_OF_PLAY section 35 -- ROI RANKING across every strategy this project
has a real, saved daily return series for, across three windows:
2022-01-01..latest, 2019-01-01..latest, and each series' own max/full
real range.

REPORTING ONLY -- no new backtests, no new trials. Reuses the 64-series
inventory (results/ensemble_daily_returns.csv, sections 32-32.2) plus the
3 series built or logged since then that were never folded into that file:
ORB gold RETEST (section 33), the tail-risk OTM-put hedge at 1%/2% alloc
(section 34.2), and the long/short momentum rotation N=6/N=12 (section
34.1, both LONG-ONLY and LONG-SHORT variants -- LONG-ONLY N=6/N=12 are
already redundant with "A|MomoRot US-sector widened 27-univ" in the 64-
series file at N=12 specifically; included anyway for completeness with a
note, not silently deduped).

RULE ENFORCED THROUGHOUT (per this session's own zero-fill lesson): no
window's ROI is computed by fabricating missing days. If a series does not
reach back to a window's start, or does not reach forward to "latest", its
real available date range is used and reported explicitly, not the nominal
window -- ranked separately from series with genuine full coverage.
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

RESULTS = _ROOT / "results"
WINDOWS = {
    "2022-2026": ("2022-01-01", None),
    "2019-2026": ("2019-01-01", None),
}


def roi_over_window(s: pd.Series, start: str | None, end: str | None) -> dict:
    s = s.dropna()
    if start is not None:
        s = s[s.index >= pd.Timestamp(start)]
    if end is not None:
        s = s[s.index <= pd.Timestamp(end)]
    if len(s) < 5:
        return dict(n_days=len(s), first=None, last=None, total_return=float("nan"))
    eq = (1.0 + s).cumprod()
    return dict(n_days=len(s), first=str(s.index.min().date()), last=str(s.index.max().date()),
                total_return=float(eq.iloc[-1] - 1.0))


def build_extra_series() -> dict[str, pd.Series]:
    """The 3 real strategies logged since section 32.2 that never went into
    ensemble_daily_returns.csv."""
    out = {}

    # ORB gold RETEST (section 33) -- reuse the exact extraction
    from research.four_candidates_beta_alpha_audit import build_orb_gold_retest
    orb_ret, _ = build_orb_gold_retest()
    out["ORB gold RETEST (XAUUSD RETEST OR30/1R, sec 33)"] = orb_ret

    # Tail-risk OTM put hedge, 1% and 2% (section 34.2)
    for pct in (1, 2):
        p = RESULTS / f"tail_hedge_otm_puts_daily_ret_alloc{pct}pct.csv"
        df = pd.read_csv(p, index_col=0, parse_dates=True)
        col = df.columns[0]
        out[f"Tail-hedge OTM SPY puts {pct}% alloc (sec 34.2)"] = ec.to_calendar_grid(df[col].dropna())

    # Long/short momentum rotation, N=6 and N=12, both variants (section 34.1)
    from research.momentum_rotation import SECTOR_ETFS, ASSET_ETFS, build_weights, simulate, BENCHMARK
    from research.momentum_rotation_long_short import build_weights_long_short
    NEW_TICKERS = ["DBC", "USO", "UNG", "SLV", "VGK", "INDA", "FXI", "MTUM", "VTV", "MDY"]
    EXPANDED_UNIVERSE = SECTOR_ETFS + ASSET_ETFS + NEW_TICKERS
    adjclose = pd.read_csv(_ROOT / "data" / "momentum_universe_expanded_adjclose.csv",
                            index_col=0, parse_dates=True).sort_index()
    for n_months in (6, 12):
        we_lo, to_lo = build_weights(adjclose, n_months, 5, universe=EXPANDED_UNIVERSE)
        sim_lo = simulate(adjclose, we_lo, to_lo, universe=EXPANDED_UNIVERSE)
        we_ls, to_ls = build_weights_long_short(adjclose, n_months, universe=EXPANDED_UNIVERSE)
        sim_ls = simulate(adjclose, we_ls, to_ls, universe=EXPANDED_UNIVERSE)
        first_exec = max(we_lo.index[0], we_ls.index[0])
        out[f"MomoRot LONG-ONLY N={n_months} (sec 34.1 re-run, live from {first_exec.date()})"] = \
            ec.to_calendar_grid(sim_lo["net"][sim_lo["net"].index >= first_exec].dropna())
        out[f"MomoRot LONG-SHORT N={n_months} (sec 34.1)"] = \
            ec.to_calendar_grid(sim_ls["net"][sim_ls["net"].index >= first_exec].dropna())

    return out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    W = 118
    print("=" * W)
    print("  SECTION 35 -- ROI RANKING: 2022-2026 / 2019-2026 / MAX PERIOD, every real strategy in the project")
    print("=" * W)

    frame = pd.read_csv(RESULTS / "ensemble_daily_returns.csv", index_col=0, parse_dates=True)
    all_series = {c: frame[c] for c in frame.columns}
    print(f"\nBase inventory (sections 32-32.2): {len(all_series)} series")

    extra = build_extra_series()
    print(f"Additional series (sections 33/34.1/34.2, not in the base file): {len(extra)}")
    all_series.update(extra)
    print(f"TOTAL: {len(all_series)} strategies with a real, saved daily return series\n")

    rows = []
    for name, s in all_series.items():
        s = s.dropna()
        r_max = roi_over_window(s, None, None)
        r_2019 = roi_over_window(s, "2019-01-01", None)
        r_2022 = roi_over_window(s, "2022-01-01", None)
        rows.append(dict(
            name=name,
            max_first=r_max["first"], max_last=r_max["last"], max_days=r_max["n_days"], max_roi=r_max["total_return"],
            w19_first=r_2019["first"], w19_last=r_2019["last"], w19_days=r_2019["n_days"], w19_roi=r_2019["total_return"],
            w22_first=r_2022["first"], w22_last=r_2022["last"], w22_days=r_2022["n_days"], w22_roi=r_2022["total_return"],
        ))
    tbl = pd.DataFrame(rows)
    tbl.to_csv(RESULTS / "roi_ranking_all_strategies.csv", index=False)

    def print_ranking(col_roi, col_first, col_last, col_days, min_start, label, require_full_start=True):
        sub = tbl.dropna(subset=[col_roi]).copy()
        if require_full_start and min_start is not None:
            sub["covers_full_window"] = pd.to_datetime(sub[col_first]) <= pd.Timestamp(min_start) + pd.Timedelta(days=5)
        else:
            sub["covers_full_window"] = True
        sub = sub.sort_values(col_roi, ascending=False)
        print(f"\n{'='*W}\n  RANKED BY ROI -- {label}\n{'='*W}")
        print(f"  {'rank':<5}{'strategy':<62}{'ROI':>10}  {'real range':<24}{'days':>6}  full-window?")
        for i, (_, r) in enumerate(sub.iterrows(), 1):
            flag = "YES" if r["covers_full_window"] else f"PARTIAL (from {r[col_first]})"
            print(f"  {i:<5}{r['name'][:60]:<62}{r[col_roi]*100:>9.1f}%  {r[col_first]}..{r[col_last]:<10}"
                  f"{int(r[col_days]):>6}  {flag}")
        return sub

    print_ranking("max_roi", "max_first", "max_last", "max_days", None, "MAX PERIOD (each strategy's own full real range)", require_full_start=False)
    print_ranking("w19_roi", "w19_first", "w19_last", "w19_days", "2019-01-01", "2019-01-01 .. latest available")
    print_ranking("w22_roi", "w22_first", "w22_last", "w22_days", "2022-01-01", "2022-01-01 .. latest available")

    print(f"\nSaved: results/roi_ranking_all_strategies.csv ({len(tbl)} strategies x 3 windows)")


if __name__ == "__main__":
    main()
