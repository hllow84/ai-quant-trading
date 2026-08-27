#!/usr/bin/env python3
"""smoke_test_m1.py — exercise the WHOLE run_sweep_m1 pipeline on a small slice.

Two families, one instrument, a truncated date window: enough to prove that
score_config -> analyze -> CSV -> --analyze all work end to end before the real
run is launched detached. Writes to results/_smoke_* so nothing real is touched.
"""
from __future__ import annotations
import sys
from pathlib import Path
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import pandas as pd
import run_sweep_m1 as rs
from strategies.sweep_families import FAMILIES

rs.FAMILIES = {k: (fn, v[:1]) for k, (fn, v) in FAMILIES.items() if k in ("macross", "meanrev")}
rs.INSTRUMENTS = {"NAS100": rs.INSTRUMENTS["NAS100"]}
rs.OUT_CSV = _ROOT / "results" / "_smoke_m1.csv"
rs.SCORED_CSV = _ROOT / "results" / "_smoke_m1_scored.csv"
rs.WINDOW_LABEL = "SMOKE TEST"

_orig = rs.load_m1_spot
def _truncated(path):
    df = _orig(path)
    return df.loc["2024-01-01":"2024-06-30"]
rs.load_m1_spot = _truncated

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
rs.main()
print("\n\n########## RE-SCORE FROM CSV (--analyze path) ##########")
rs.analyze_only()
