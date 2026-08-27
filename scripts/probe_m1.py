#!/usr/bin/env python3
"""probe_m1.py — pre-flight checks for the M1 row of the timeframe sweep.

Answers four things BEFORE the sweep is written, so no assumption is carried
into the run untested:

 1. Is resample_mid(m1, "1min") identical to shifting the native index +1min?
    (If yes, M1 can use the SAME code path as M5-H4 without building a 4.2M-row
    intermediate frame.)
 2. How many M1 bars per year does each file actually hold? This is the number
    the Sharpe-annualisation question turns on.
 3. What is the median spread in bps at M1, per instrument?
 4. How long does one config take at M1, and how many trades does it fire?
"""
from __future__ import annotations

import sys, time
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_mid, load_m1_spot, aggregate_daily, resample_mid
from research.ftmo_engine import simulate_trades, de_overlap
from strategies.sweep_families import FAMILIES, TF_DELTA

FILES = {
    "XAUUSD": _ROOT / "data" / "XAUUSD_M1_2018_2025_spot_dukascopy.csv",
    "NAS100": _ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv",
    "US30":   _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",
    "NAS100_pre": _ROOT / "data" / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv",
    "US30_pre":   _ROOT / "data" / "US30_M1RTH_2013_2017_cfd_dukascopy.csv",
}
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)


def main():
    for name, path in FILES.items():
        if not path.exists():
            print(f"[{name}] MISSING {path.name}")
            continue
        t0 = time.time()
        m1 = load_m1_mid(path)
        print(f"\n[{name}] {len(m1):,} M1 bars  {m1.index[0]} -> {m1.index[-1]}  "
              f"(load {time.time()-t0:.1f}s)")

        # ── 1. resample equivalence, checked on a real slice ──────────────────
        sl = m1.iloc[:200_000]
        rs = resample_mid(sl, "1min")
        shifted = sl.copy()
        shifted.index = shifted.index + pd.Timedelta(minutes=1)
        common = rs.index.intersection(shifted.index)
        cols = ["mid_open", "mid_high", "mid_low", "mid_close", "spread"]
        same_len = (len(rs) == len(shifted))
        eq = np.allclose(rs.loc[common, cols].to_numpy(),
                         shifted.loc[common, cols].to_numpy(), equal_nan=True)
        print(f"  resample_mid('1min') == index+1min ? len_match={same_len} "
              f"values_match={eq}  (rs {len(rs):,} vs shift {len(shifted):,})")

        # ── 2. bars per year (the annualisation number) ───────────────────────
        by_year = m1.groupby(m1.index.year).size()
        full = by_year.iloc[1:-1] if len(by_year) > 2 else by_year
        print(f"  bars/year: min {by_year.min():,} max {by_year.max():,} "
              f"mean(full yrs) {full.mean():,.0f}")
        print(f"    {dict(by_year)}")

        # ── 3. spread in bps ──────────────────────────────────────────────────
        med_sp = float(m1['spread'].median()); med_px = float(m1['mid_close'].median())
        print(f"  median spread {med_sp:.4f} px on median price {med_px:,.1f} "
              f"= {1e4*med_sp/med_px:.2f} bps round-turn")

        # ── 4. cost of one config at M1 ───────────────────────────────────────
        if name.endswith("_pre"):
            continue
        m = resample_mid(m1, "1min")
        for fam in ("momentum", "macross"):
            fn, variants = FAMILIES[fam]
            p = variants[0]
            t0 = time.time()
            cands = fn(m, p, TF_DELTA["M5"].__class__(minutes=1))
            t_sig = time.time() - t0
            t0 = time.time()
            tr = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=COST_BPS))
            t_sim = time.time() - t0
            print(f"  {fam:<9} v0: cands {len(cands):,} -> trades {len(tr):,} "
                  f"| signal {t_sig:.1f}s sim {t_sim:.1f}s "
                  f"| cost_R {tr['cost_R'].mean()*100:.1f}% grossPF "
                  f"{(tr.loc[tr.gross_R>0,'gross_R'].sum()/abs(tr.loc[tr.gross_R<0,'gross_R'].sum())):.3f}")
        del m
        del m1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
