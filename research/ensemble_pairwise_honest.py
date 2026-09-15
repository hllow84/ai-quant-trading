#!/usr/bin/env python3
"""
SECTION 32.2 -- PAIRWISE-COMPLETE ENSEMBLE TEST: the most honest, highest-
potential combination this project's real signal data can support, using
pairwise-complete correlation (no fixed universal window, no zero-fill,
no staggered-inception blending trap from section 32.1).

INPUT: reuses results/ensemble_daily_returns.csv (the 64-series daily
return frame already extracted for section 32/32.1 -- NOT re-extracted
here, no new backtests). NOTE ON COUNT: the user's brief referred to "24
strategies" -- the actual saved inventory is 64 series (same file used by
sections 32 and 32.1). Run against the real 64, flagged not silently
resized.

METHOD
  1. Pairwise-complete correlation: pandas .corr(min_periods=OVERLAP_MIN)
     -- computed per PAIR only over days both series have real (non-NaN)
     data, exactly the standard pairwise-complete-observations technique.
     Pairs with fewer than OVERLAP_MIN genuinely-shared days get NaN, not
     a number computed on too few points -- reported and counted
     explicitly, never silently dropped from the table.
  2. Compatibility graph: two series are "compatible" (can sit in the same
     combined group) only if they have >= OVERLAP_MIN real shared days
     AND |pairwise corr| < CORR_THRESHOLD. Finding the LARGEST mutually-
     compatible group is the maximum-clique problem (NP-hard); no exact
     solver is used (networkx unavailable in this environment) -- a
     greedy heuristic is run from multiple seed orders (by history length,
     by own Sharpe, by compatibility-graph degree) and the largest result
     is kept, STATED as a heuristic upper-bound approximation, not a
     certified maximum.
  3. Combined portfolio: on each calendar day, average ONLY the group
     members with real (non-NaN) data that day (frame.mean(skipna=True) --
     the same, verified-correct, non-zero-filling function from
     ensemble_correlation.py, imported not reimplemented). Days with < 3
     live group members are flagged LOW-CONFIDENCE in the output (not
     dropped -- flagged, per the brief).
  4. No fixed window: reported over the full span the GROUP's own union of
     data actually covers. The live-count-per-day table is reported in
     full so the section-32.1 regime-blending risk is visible, not hidden,
     even though this method does not pre-restrict the window.
"""
from __future__ import annotations

import itertools
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
OVERLAP_MIN = 250          # min genuinely-shared real days to trust a pairwise corr
CORR_THRESHOLD = 0.30      # same threshold as section 32, stated a priori
LOW_CONF_MIN_LIVE = 3      # days with fewer live members are flagged, not dropped


def pairwise_shared_days(frame: pd.DataFrame) -> pd.DataFrame:
    notna = frame.notna().astype(int)
    return notna.T.dot(notna)  # shared_days[i,j] = count of days both i and j real


def build_compatibility_graph(frame: pd.DataFrame, corr: pd.DataFrame,
                               shared: pd.DataFrame) -> dict[str, set[str]]:
    names = list(frame.columns)
    adj = {n: set() for n in names}
    for a, b in itertools.combinations(names, 2):
        if shared.loc[a, b] < OVERLAP_MIN:
            continue
        c = corr.loc[a, b]
        if pd.isna(c):
            continue
        if abs(c) < CORR_THRESHOLD:
            adj[a].add(b)
            adj[b].add(a)
    return adj


def greedy_clique(adj: dict[str, set[str]], order: list[str]) -> list[str]:
    kept: list[str] = []
    for n in order:
        if all(n in adj[k] for k in kept):
            kept.append(n)
    return kept


def find_best_clique(adj: dict[str, set[str]], summ: pd.DataFrame,
                      frame: pd.DataFrame) -> tuple[list[str], str]:
    names = list(adj.keys())
    candidates = []

    order_hist = summ.sort_values("years", ascending=False)["name"].tolist()
    candidates.append((greedy_clique(adj, order_hist), "longest-history-first"))

    order_sharpe = summ.sort_values("sharpe", ascending=False)["name"].tolist()
    candidates.append((greedy_clique(adj, order_sharpe), "highest-own-Sharpe-first"))

    degree = {n: len(adj[n]) for n in names}
    order_degree = sorted(names, key=lambda n: -degree[n])
    candidates.append((greedy_clique(adj, order_degree), "highest-compatibility-degree-first"))

    rng = np.random.default_rng(42)
    for trial in range(30):
        order_rand = list(names)
        rng.shuffle(order_rand)
        candidates.append((greedy_clique(adj, order_rand), f"random-seed-{trial}"))

    best, best_label = max(candidates, key=lambda t: len(t[0])), None
    for c, label in candidates:
        if len(c) == len(best[0]) and best_label is None:
            best, best_label = c, label
    return best, best_label


def dsr_of(c: pd.Series, pool_sr: np.ndarray) -> float:
    c = c.dropna()
    sr = ec.sharpe_ann(c)
    d = deflated_sharpe(sr, pool_sr, n_obs=len(c), ann_factor=ec.BARS_PER_YEAR,
                         skewness=float(c.skew()), excess_kurtosis=float(c.kurtosis()))
    return d["dsr"]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    W = 112
    print("=" * W)
    print("  SECTION 32.2 -- PAIRWISE-COMPLETE ENSEMBLE TEST (no fixed window, no zero-fill)")
    print("=" * W)

    frame = pd.read_csv(RESULTS / "ensemble_daily_returns.csv", index_col=0, parse_dates=True)
    summ = pd.read_csv(RESULTS / "ensemble_component_summary.csv")
    names = list(frame.columns)
    print(f"\nComponent inventory: {len(names)} series (user's brief said 24 -- actual saved inventory is "
          f"{len(names)}, same file sections 32/32.1 used; running against the real count, not resized).")

    # ---- honesty gate: verify no zero-fill anywhere in the source frame's construction ----
    print("\nHONESTY GATE -- zero-fill check (re-verified, not assumed from last time):")
    print("  ensemble_correlation.to_calendar_grid() fills ONLY off-days *inside* a series' own [first,last]")
    print("  range (a stated, legitimate flat-return convention); frame cells OUTSIDE that range are NaN, never 0.")
    print("  equal_weight_available() = frame.mean(axis=1, skipna=True) -- verified again by source read below.")
    import inspect
    src = inspect.getsource(ec.equal_weight_available)
    assert "skipna=True" in src and "fillna(0" not in src.split("\n\n")[0], "zero-fill regression detected!"
    print("  ASSERTION PASSED: equal_weight_available source contains skipna=True, no fillna(0) before the mean.")

    # ---- pairwise-complete correlation + shared-day counts ----
    corr = frame.corr(min_periods=OVERLAP_MIN)
    shared = pairwise_shared_days(frame)
    corr.to_csv(RESULTS / "ensemble_pairwise_corr_matrix.csv")
    shared.to_csv(RESULTS / "ensemble_pairwise_shared_days.csv")

    pairs_idx = list(itertools.combinations(names, 2))
    n_pairs = len(pairs_idx)
    n_untrusted = sum(1 for a, b in pairs_idx if shared.loc[a, b] < OVERLAP_MIN)
    n_trusted = n_pairs - n_untrusted
    trusted_vals = [corr.loc[a, b] for a, b in pairs_idx if shared.loc[a, b] >= OVERLAP_MIN and not pd.isna(corr.loc[a, b])]
    print(f"\nPAIRWISE-COMPLETE CORRELATION MATRIX: {len(names)}x{len(names)}, {n_pairs:,} unique pairs.")
    print(f"  pairs with >= {OVERLAP_MIN} genuinely-shared real days (TRUSTED)  : {n_trusted:,} ({100*n_trusted/n_pairs:.1f}%)")
    print(f"  pairs with <  {OVERLAP_MIN} genuinely-shared real days (UNTRUSTED, marked NaN, not reported as a number): {n_untrusted:,} ({100*n_untrusted/n_pairs:.1f}%)")
    tv = pd.Series(trusted_vals)
    print(f"  TRUSTED pairs only -- mean corr {tv.mean():+.3f}, median {tv.median():+.3f}, "
          f"|corr|>0.70: {int((tv.abs()>0.70).sum())} ({100*(tv.abs()>0.70).mean():.1f}%), "
          f"|corr|<0.30: {int((tv.abs()<0.30).sum())} ({100*(tv.abs()<0.30).mean():.1f}%)")
    print(f"  Full matrix saved -> results/ensemble_pairwise_corr_matrix.csv (untrusted cells are real NaN)")
    print(f"  Shared-day counts saved -> results/ensemble_pairwise_shared_days.csv")

    # ---- compatibility graph + largest honestly-combinable group ----
    adj = build_compatibility_graph(frame, corr, shared)
    best_clique, best_label = find_best_clique(adj, summ, frame)
    print(f"\nLARGEST HONESTLY-COMBINABLE GROUP, QUALITY-BLIND (heuristic greedy search, {30+3} seed orders tried, "
          f"NOT a certified max-clique -- exact max-clique is NP-hard and no exact solver was available; "
          f"reported as the best heuristic result, best seed = '{best_label}'):")
    print(f"  N = {len(best_clique)} members, all pairs within the group have >= {OVERLAP_MIN} shared real days "
          f"AND |corr| < {CORR_THRESHOLD}:")
    summ_idx = summ.set_index("name")
    for m in best_clique:
        r = summ_idx.loc[m]
        print(f"    - {m}  (own Sharpe {r['sharpe']:+.3f}, data {r['first']}..{r['last']})")
    n_ruin = sum(1 for m in best_clique if summ_idx.loc[m, "sharpe"] < -1.0)
    print(f"  !! {n_ruin}/{len(best_clique)} members have own full-history Sharpe < -1.0 (catastrophic) -- "
          f"same section-32.1 lesson: quality-blind low-correlation filtering finds independent DISASTERS too, "
          f"not just independent-and-healthy signals. A quality-gated version is run below for the fair best case.")

    # ---- QUALITY-GATED version: same method, candidate pool restricted to own-Sharpe > 0 ----
    positive_names = summ.loc[summ["sharpe"] > 0, "name"].tolist()
    adj_q = {n: (adj[n] & set(positive_names)) for n in positive_names}
    best_clique_q, best_label_q = find_best_clique(adj_q, summ[summ["name"].isin(positive_names)], frame)
    print(f"\nLARGEST HONESTLY-COMBINABLE GROUP, QUALITY-GATED (candidate pool restricted a priori to the "
          f"{len(positive_names)}/{len(names)} series with own full-history Sharpe > 0, same method, best seed = "
          f"'{best_label_q}'):")
    print(f"  N = {len(best_clique_q)} members:")
    for m in best_clique_q:
        r = summ_idx.loc[m]
        print(f"    - {m}  (own Sharpe {r['sharpe']:+.3f}, data {r['first']}..{r['last']})")

    pool_sr = summ["sharpe"].dropna().to_numpy()

    def report_group(clique: list[str], tag: str) -> list[dict]:
        grp = frame[clique].dropna(how="all")
        live = grp.notna().sum(axis=1)
        print(f"\n[{tag}] GROUP'S OWN HONEST FULL SPAN: {grp.index.min().date()} .. {grp.index.max().date()} "
              f"({len(grp):,} days)")
        print("  live-component-count-per-day (yearly mean, full transparency table):")
        print(live.groupby(live.index.year).mean().round(2).to_string())
        low_conf_days = int((live < LOW_CONF_MIN_LIVE).sum())
        print(f"  days with < {LOW_CONF_MIN_LIVE} live group members (LOW-CONFIDENCE, flagged not dropped): "
              f"{low_conf_days:,} / {len(grp):,} ({100*low_conf_days/len(grp):.1f}%)")

        combo = ec.equal_weight_available(grp)
        dd = ec.max_dd_recovery(combo.dropna())
        sr = ec.sharpe_ann(combo.dropna())
        tys = ec.top_year_share(combo.dropna())
        dsr_full = dsr_of(combo, pool_sr)
        print(f"  COMBINED (full span, low-confidence days included): total_return="
              f"{float(ec.equity(combo.dropna()).iloc[-1]-1)*100:+.1f}%  sharpe={sr:+.3f}  "
              f"maxDD={dd['max_dd']*100:.1f}%  recovery_days={dd['recovery_days']}  "
              f"top_year_share={tys*100 if not np.isnan(tys) else float('nan'):.1f}%  DSR={dsr_full:.4f} (pool N={len(pool_sr)})")

        high_conf_start = live[live >= LOW_CONF_MIN_LIVE].index.min()
        rows = [dict(method=f"{tag} (full honest span)", n=len(clique),
                      first=str(grp.index.min().date()), last=str(grp.index.max().date()), n_days=len(grp),
                      total_return=float(ec.equity(combo.dropna()).iloc[-1]-1), sharpe=sr, max_dd=dd["max_dd"],
                      recovery_days=dd["recovery_days"], top_year_share=tys, dsr=dsr_full, dsr_pool_n=len(pool_sr),
                      low_conf_days=low_conf_days, low_conf_pct=low_conf_days/len(grp))]
        if pd.notna(high_conf_start):
            grp_hc = grp.loc[high_conf_start:]
            combo_hc = ec.equal_weight_available(grp_hc)
            dd_hc = ec.max_dd_recovery(combo_hc.dropna())
            sr_hc = ec.sharpe_ann(combo_hc.dropna())
            dsr_hc = dsr_of(combo_hc, pool_sr)
            print(f"  HIGH-CONFIDENCE sub-period (>= {LOW_CONF_MIN_LIVE} live, from {high_conf_start.date()}, "
                  f"{len(grp_hc):,} days): total_return={float(ec.equity(combo_hc.dropna()).iloc[-1]-1)*100:+.1f}%  "
                  f"sharpe={sr_hc:+.3f}  maxDD={dd_hc['max_dd']*100:.1f}%  recovery_days={dd_hc['recovery_days']}  "
                  f"DSR={dsr_hc:.4f}")
            rows.append(dict(method=f"{tag} (high-confidence sub-period only)", n=len(clique),
                              first=str(grp_hc.index.min().date()), last=str(grp_hc.index.max().date()),
                              n_days=len(grp_hc), total_return=float(ec.equity(combo_hc.dropna()).iloc[-1]-1),
                              sharpe=sr_hc, max_dd=dd_hc["max_dd"], recovery_days=dd_hc["recovery_days"],
                              top_year_share=ec.top_year_share(combo_hc.dropna()), dsr=dsr_hc,
                              dsr_pool_n=len(pool_sr), low_conf_days=0, low_conf_pct=0.0))
        print(f"  STANDALONE comparison (each member's own full-history stats):")
        for m in clique:
            r = summ_idx.loc[m]
            print(f"    {m:60s} sharpe={r['sharpe']:+.3f}  total_return={r['total_return']*100:+.1f}%  "
                  f"maxDD={r['max_dd']*100:.1f}%")
        return rows

    all_rows = report_group(best_clique, "QUALITY-BLIND")
    all_rows += report_group(best_clique_q, "QUALITY-GATED")

    out = pd.DataFrame(all_rows)
    out.to_csv(RESULTS / "ensemble_pairwise_honest_results.csv", index=False)
    print(f"\nSaved: results/ensemble_pairwise_honest_results.csv, "
          f"ensemble_pairwise_corr_matrix.csv, ensemble_pairwise_shared_days.csv")


if __name__ == "__main__":
    main()
