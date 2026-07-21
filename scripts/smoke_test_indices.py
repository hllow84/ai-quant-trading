"""Smoke-test the index pipeline on whatever years have landed so far.

Purpose: prove merge -> load -> resample -> sweep -> score works END TO END
before committing to the full 7-hour download, so a bug surfaces now and not
at the end.

IMPORTANT: writes to a SCRATCH csv, never results/sweep_indices.csv. The real
sweep file is resume-keyed, so partial-data rows written there would be treated
as done and silently skipped once the full history lands.

Run: python scripts/smoke_test_indices.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import pandas as pd

import run_sweep_indices as R
from research.gold_data import load_m1_mid, load_m1_spot, aggregate_daily, resample_mid
from strategies.sweep_families import FAMILIES, TIMEFRAMES

SCRATCH = Path(r"C:\Users\Harve\AppData\Local\Temp\claude\C--Claude-Code"
               r"\9198593f-74c9-4a4b-9089-ca2c530ab5b7\scratchpad\smoke_indices.csv")


def main():
    print("=" * 78)
    print("  INDEX PIPELINE SMOKE TEST (partial data — validity check only)")
    print("=" * 78)

    any_ok = False
    for inst, path in R.INSTRUMENTS.items():
        if not path.exists():
            print(f"\n[{inst}] merged file not present yet at {path.name} — skip.")
            continue
        any_ok = True
        m1 = load_m1_mid(path)
        daily_index = aggregate_daily(load_m1_spot(path)).index
        d0, d1 = daily_index[0], daily_index[-1]
        med_px = float(m1["mid_close"].median())
        med_sp = float(m1["spread"].median())
        print(f"\n[{inst}] M1 bars {len(m1):,} | {m1.index[0].date()} -> {m1.index[-1].date()}")
        print(f"[{inst}] median px {med_px:,.1f} | median spread {med_sp:.3f} pts "
              f"({1e4*med_sp/med_px:.2f} bps) | daily bars {len(daily_index)}")

        # one representative config per timeframe, one family — enough to prove wiring
        fam = "macross"
        fn, variants = FAMILIES[fam]
        for tf_key, tf_freq in TIMEFRAMES.items():
            m = resample_mid(m1, tf_freq)
            res = R.score_config(m, fn, variants[0], tf_key, daily_index, d0, d1)
            n = res.get("n_trades", 0)
            if n == 0:
                print(f"  {tf_key:>3} {fam:<8} bars={len(m):>7,}  NO TRADES  guard={res.get('guard')}")
                continue
            print(f"  {tf_key:>3} {fam:<8} bars={len(m):>7,} n={n:>5} "
                  f"grPF={res['gross_pf']:.2f} netPF={res['net_pf']:.2f} "
                  f"SR={res['sharpe']:+.2f} costR={res['cost_R_mean']*100:.2f}% "
                  f"medR={res['risk_med']:.1f}pts guard={res['guard'][:4]}")

        bh = R.buy_and_hold(path)
        print(f"[{inst}] buy-and-hold over this span: SR {bh['sharpe']:+.2f}, "
              f"MDD {bh['max_dd']*100:.1f}%, CAGR {bh['cagr']*100:.1f}%, {bh['n_days']} days")

    if not any_ok:
        print("\nNo merged index files yet — run scripts/merge_indices.py first.")
        return 1

    print("\n" + "=" * 78)
    print("  SMOKE TEST COMPLETE — wiring verified. Numbers here are PARTIAL-DATA")
    print("  and must NOT be reported as results.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    SCRATCH.parent.mkdir(parents=True, exist_ok=True)
    sys.exit(main())
