#!/usr/bin/env python3
"""
test_seasonality.py — PART B: is there a STATISTICALLY REAL, repeating
calendar-quarter pattern in which of the 5 sweep families performs best on
BTC/ETH? This is a genuinely different selection mechanism from section 15
(trailing recent performance) — "does family X reliably do better in Q4
historically," not "what recently worked."

METHOD, stated before any result is read
------------------------------------------
For each (instrument, family), each family's H4 daily net-return series
(research/regime_switch.py::build_family_returns, variant v0, UNCHANGED —
the exact same candidate systems as sections 13 and 15) is aggregated into
one number per (calendar year, calendar quarter): the SUM of daily net
returns realized in that quarter. Only COMPLETE quarters are used — a
quarter is included only if the underlying H4 data fully spans it (2026 Q3
is excluded: the data ends 2026-08-31, partway through Jul-Sep).

For each (instrument, family), a Kruskal-Wallis test (nonparametric
one-way ANOVA — chosen because per-quarter return sums are not assumed
Gaussian) is run across the 4 quarter groups (Q1, Q2, Q3, Q4), each
group containing ~8-9 independent year-observations. H0: the quarter a
return was realized in makes no difference to its distribution — i.e., NO
seasonal effect for that family on that instrument.

5 families x 2 instruments = 10 independent tests. Bonferroni correction
applied: alpha=0.05 -> corrected threshold p < 0.005. This is a real,
pre-stated test, not an eyeballed table — the correction is applied BEFORE
any p-value is read, exactly to prevent "look at 10 things, one is below
0.05 by chance" from being reported as a finding.

Only if a family/instrument pair clears the corrected threshold does this
script proceed to build a walk-forward seasonal selection rule (using ONLY
years strictly before the year being decided) and backtest it through the
same cost/switching mechanics as section 15. If NOTHING clears the
threshold, that is reported as the answer — a clean negative, not dressed
up as a near-miss.

Usage: python scripts/test_seasonality.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
from scipy import stats

from research.regime_switch import build_family_returns, FAMILY_NAMES
from run_sweep_crypto import CRYPTO_COST_BPS, INSTRUMENTS, load_bars

ALPHA = 0.05
N_TESTS = 10  # 5 families x 2 instruments
BONFERRONI_ALPHA = ALPHA / N_TESTS

RESULTS_CSV = _ROOT / "results" / "seasonality_test.csv"
QUARTER_MEANS_CSV = _ROOT / "results" / "seasonality_quarter_means.csv"


def complete_quarter_returns(returns: pd.Series) -> pd.DataFrame:
    """
    Returns a DataFrame indexed by (year, quarter) with column 'ret' = sum
    of daily returns in that quarter, restricted to quarters FULLY covered
    by `returns`'s own index span.
    """
    idx = returns.index
    data_start, data_end = idx[0], idx[-1]
    q = idx.to_series().dt.to_period("Q")
    grouped = returns.groupby(q).sum()

    rows = []
    for period, val in grouped.items():
        q_start = period.start_time.tz_localize("UTC")
        q_end = period.end_time.tz_localize("UTC")
        if q_start >= data_start and q_end <= data_end:
            rows.append(dict(year=period.year, quarter=period.quarter, ret=float(val)))
    return pd.DataFrame(rows)


def main() -> None:
    test_rows = []
    quarter_mean_rows = []
    all_family_returns = {}  # (inst) -> {fam: series}

    for inst, tf_paths in INSTRUMENTS.items():
        path = tf_paths["H4"]
        if not path.exists():
            print(f"[{inst}] MISSING {path.name} — skipped.", flush=True)
            continue
        print(f"[{inst}] loading H4, building family returns ...", flush=True)
        m = load_bars(path)
        fam_returns = build_family_returns(m, CRYPTO_COST_BPS, tf_key="H4", variant_index=0)
        all_family_returns[inst] = fam_returns

        for fam in FAMILY_NAMES:
            qr = complete_quarter_returns(fam_returns[fam])
            groups = [qr.loc[qr["quarter"] == q, "ret"].to_numpy() for q in (1, 2, 3, 4)]
            groups = [g for g in groups if len(g) >= 2]
            if len(groups) < 2:
                stat, p = float("nan"), float("nan")
            else:
                stat, p = stats.kruskal(*groups)
            sig = bool(np.isfinite(p) and p < BONFERRONI_ALPHA)
            test_rows.append(dict(instrument=inst, family=fam, n_complete_quarters=len(qr),
                                  kw_stat=stat, p_value=p, significant_bonferroni=sig))
            for q in (1, 2, 3, 4):
                sub = qr.loc[qr["quarter"] == q, "ret"]
                quarter_mean_rows.append(dict(instrument=inst, family=fam, quarter=q,
                                              n_years=len(sub), mean_ret=float(sub.mean()) if len(sub) else float("nan"),
                                              std_ret=float(sub.std()) if len(sub) > 1 else float("nan")))

    test_df = pd.DataFrame(test_rows)
    qmean_df = pd.DataFrame(quarter_mean_rows)
    RESULTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    test_df.to_csv(RESULTS_CSV, index=False)
    qmean_df.to_csv(QUARTER_MEANS_CSV, index=False)

    W = 100
    print("\n" + "=" * W)
    print("  PART B — SEASONALITY TEST: is there a real calendar-quarter pattern in family performance?")
    print(f"  Kruskal-Wallis per (instrument, family) across 4 quarter groups. "
          f"{N_TESTS} tests, Bonferroni alpha = {BONFERRONI_ALPHA:.4f}")
    print("=" * W)
    print(f"\n  {'inst':>7} {'family':<9} {'n_qtrs':>7} {'KW stat':>9} {'p-value':>9} {'sig (Bonf)':>11}")
    print("  " + "-" * (W - 4))
    for _, r in test_df.sort_values("p_value").iterrows():
        print(f"  {r['instrument']:>7} {r['family']:<9} {r['n_complete_quarters']:>7} "
              f"{r['kw_stat']:>9.3f} {r['p_value']:>9.4f} "
              f"{'YES ***' if r['significant_bonferroni'] else 'no':>11}")
    print("=" * W)

    n_sig = int(test_df["significant_bonferroni"].sum())
    min_p = test_df["p_value"].min()
    print(f"\n  RESULT: {n_sig}/{N_TESTS} (instrument, family) pairs clear the Bonferroni-corrected "
          f"threshold (p < {BONFERRONI_ALPHA:.4f}).")
    print(f"  Smallest raw p-value observed: {min_p:.4f} "
          f"({'still' if min_p >= BONFERRONI_ALPHA else ''} "
          f"{'ABOVE' if min_p >= BONFERRONI_ALPHA else 'below'} the corrected threshold, "
          f"{'below' if min_p < ALPHA else 'above'} the UNCORRECTED alpha=0.05).")

    if n_sig == 0:
        print("\n  CONCLUSION: NO statistically real seasonal pattern was found in this test.")
        print("  Per the task's explicit instruction, this is reported as a clean negative — NO seasonal")
        print("  selection rule is built or backtested, because there is nothing statistically real to")
        print("  base one on. Building a backtest on the smallest-p-value cell anyway would be exactly")
        print("  the 'eyeball a table and pick the best-looking cell' failure mode this test exists to")
        print("  prevent.")
        print(f"\n  This is still a real, counted finding — {N_TESTS} genuine a priori statistical tests")
        print("  were run and the answer is NO, not a suppressed or hidden negative.")
    else:
        sig_rows = test_df[test_df["significant_bonferroni"]]
        print(f"\n  CONCLUSION: {n_sig} pair(s) clear the corrected threshold — proceeding to build and")
        print("  backtest a walk-forward seasonal selection rule (scripts/run_seasonal_switching.py).")
        print(sig_rows.to_string(index=False))

    print("\n  Per-quarter mean return by family (for context on what the test above actually measured):")
    piv = qmean_df.pivot_table(index=["instrument", "family"], columns="quarter", values="mean_ret")
    print(piv.round(5).to_string())
    print("=" * W)

    print(f"\n  Files: {RESULTS_CSV.relative_to(_ROOT)}, {QUARTER_MEANS_CSV.relative_to(_ROOT)}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
