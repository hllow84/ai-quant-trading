#!/usr/bin/env python3
"""
XAUUSD RETEST OR30 exit-management study -- STATE_OF_PLAY sec 10.7.

Entry logic is COMPLETELY UNCHANGED from sec 10.5/10.6 (RETEST, OR30, ET
session, real cost model) -- only the EXIT rule varies:

  1R           baseline (sec 10.5/10.6) -- fixed target at 1R, stop = OR width.
  2R           fixed target at 2R, same stop (already scored in sec 10.5).
  3R           fixed target at 3R, same stop. NEW.
  breakeven    no fixed target; once price moves 1R in favor, stop moves to
               entry (flat) and never moves again -- rides to the (possibly
               breakeven) stop or session close. NEW.
  trailing     no fixed target; once price moves 1R in favor, a trailing stop
               activates at 0.5R behind the running favorable extreme and only
               ever tightens -- rides to the trailing stop or session close.
               NEW.

Because entry timing does not depend on the target/exit rule (strategies/orb.py
`orb()` decides entry_time, side, entry_mid, stop purely from the break+retest
logic; `target` only sets where the FIXED-target modes exit), all five variants
share the SAME 465 in-regime / 89 out-of-regime (2017) entries -- confirmed
below by an explicit entry-time-set equality assertion, not assumed.

1R and 2R in-regime reproduce results/orb_entry_filters_scored.csv exactly
(reproduction-checked) -- NOT new trials. 3R (both windows), breakeven (both
windows) and trailing (both windows) are NEW backtests: 3R adds a target value
never tried before; breakeven/trailing use research/orb_dynamic_stop.py, a
bar-by-bar resolver written for this task because research/ftmo_engine.
simulate_trades can only express a FIXED stop+target (vectorized searchsorted),
not one that moves mid-trade. 8 new cells total (3R x2 windows + breakeven x2 +
trailing x2), STATE_OF_PLAY trial count 1033 -> 1041.

HONESTY GATES reported per variant: look-ahead guard (statistical, on the
resolved position series), real cost-inclusive net R (sec 10.7's own Part 1
cost audit against FTMO's published conditions), per-year concentration
(top-year share of net R, in-regime), out-of-regime performance (2017 slice --
flagged, one bull year, not a regime test, per sec 10.6), vs buy-and-hold
XAUUSD. Deflated Sharpe is printed as REFERENCE ONLY (explicitly not a
survival gate per this task's brief) against this batch's own 5-cell
structural pool.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe
from research.ftmo_engine import (
    simulate_trades, de_overlap, RISK_PER_TRADE,
    build_daily_returns, equity_from_returns, build_position_series,
)
from research.orb_dynamic_stop import resolve_dynamic_stop_trades
from strategies.orb import orb, ET
from research.report_retest_or30_1r_all4_compounded import (
    mid_frame, compound, bh, period_trades, START_CAP, PERIODS,
)

D = _ROOT / "data"
SCORED = _ROOT / "results" / "orb_entry_filters_scored.csv"
BARS_PER_YEAR = 252
ET_SESSION = dict(session_tz=ET, open_min=9 * 60 + 30, close_min=16 * 60, min_sess_bars=300)
PRIOR_TRIALS = 1033   # STATE_OF_PLAY sec 1, after sec 10.6

IN_FILE = D / "XAUUSD_M1_2018_2025_spot_dukascopy.csv"
OUT_FILE = D / "XAUUSD_M1_2017_spot_dukascopy.csv"

VARIANTS = ["1R", "2R", "3R", "breakeven", "trailing"]


def reproduction_check_target(tr: pd.DataFrame, target: str, window: str) -> bool:
    """Target-aware reproduction check (the imported helper hardcodes target=='1R',
    which would silently mis-validate the 2R cell against the wrong CSV row)."""
    row = pd.read_csv(SCORED).query(
        f"instrument=='XAUUSD' and or_minutes==30 and target=='{target}' "
        f"and variant=='RETEST' and window=='{window}'"
    )
    if row.empty:
        return False
    row = row.iloc[0]
    assert len(tr) == int(row["n_trades"]), (target, window, len(tr), row["n_trades"])
    assert abs(tr["net_R"].sum() - row["net_R_total"]) < 1e-6, \
        (target, window, tr["net_R"].sum(), row["net_R_total"])
    print(f"    repro OK vs orb_entry_filters_scored.csv [{target}/{window}]: "
          f"{len(tr)} trades, net_R total {tr['net_R'].sum():.6f}")
    return True


def build_variant_trades(m: pd.DataFrame, variant: str) -> pd.DataFrame:
    if variant in ("1R", "2R", "3R"):
        params = dict(or_minutes=30, target=variant, stop_mode="or_range")
        cands = orb(m, params, retest=True, retest_tol_frac=0.10, **ET_SESSION)
        tr = de_overlap(simulate_trades(m, cands, strictly_after=False, cost_bps=None, slip_bps_fn=None))
    else:
        params = dict(or_minutes=30, target="close", stop_mode="or_range")
        cands = orb(m, params, retest=True, retest_tol_frac=0.10, **ET_SESSION)
        tr = de_overlap(resolve_dynamic_stop_trades(m, cands, mode=variant, trail_frac=0.5,
                                                     cost_bps=None, slip_bps_fn=None))
    tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True)
    tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True)
    return tr.sort_values("exit_time").reset_index(drop=True)


def gate_stats(m: pd.DataFrame, tr: pd.DataFrame, daily_index) -> dict:
    if tr.empty:
        return dict(guard="N/A", gross_pf=np.nan, net_pf=np.nan, sharpe=np.nan, max_dd=np.nan,
                    top_year_share=np.nan, n_obs=0, skew=0.0, ekurt=0.0)
    pos = build_position_series(tr, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"
    daily_ret = build_daily_returns(tr, daily_index)
    equity = equity_from_returns(daily_ret)
    yr = tr["exit_time"].dt.year
    agg = tr.groupby(yr)["net_R"].sum()
    tot = float(agg.sum())
    top_share = (float(agg.max()) / tot) if tot > 0 else float("nan")
    return dict(
        guard=guard, gross_pf=profit_factor(tr["gross_R"]), net_pf=profit_factor(tr["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR), max_dd=max_drawdown(equity),
        top_year_share=top_share, n_obs=int(len(daily_ret)),
        skew=float(daily_ret.skew()) if len(daily_ret) > 2 else 0.0,
        ekurt=float(daily_ret.kurtosis()) if len(daily_ret) > 3 else 0.0,
    )


def reason_breakdown(tr: pd.DataFrame) -> str:
    if tr.empty:
        return "no trades"
    n = len(tr)
    parts = []
    for reason in ["target", "2R", "3R", "stop", "breakeven", "trail", "time"]:
        sub = tr[tr["reason"] == reason]
        if len(sub):
            parts.append(f"{reason}={len(sub)}({100*len(sub)/n:.0f}%,avgR={sub['net_R'].mean():+.3f})")
    return " | ".join(parts)


def main():
    print("=" * 130)
    print("  PART 2 -- XAUUSD RETEST OR30 exit-management study (sec 10.7)")
    print("=" * 130)

    m_in, spot_in = mid_frame(IN_FILE)
    di_in = aggregate_daily(spot_in).index
    m_out, spot_out = mid_frame(OUT_FILE)
    di_out = aggregate_daily(spot_out).index
    print(f"  IN  window: {IN_FILE.name}  {m_in.index[0].date()} -> {m_in.index[-1].date()}  ({len(m_in):,} bars)")
    print(f"  OUT window: {OUT_FILE.name}  {m_out.index[0].date()} -> {m_out.index[-1].date()}  ({len(m_out):,} bars)")

    results = {}   # variant -> dict(window -> (trades, gates, is_new))
    entry_sets = {"in": None, "out": None}
    for variant in VARIANTS:
        results[variant] = {}
        for wk, m, di in [("in", m_in, di_in), ("out", m_out, di_out)]:
            tr = build_variant_trades(m, variant)
            # entry-time-set equality check: same entries across all 5 variants
            ents = frozenset(tr["entry_time"])
            if entry_sets[wk] is None:
                entry_sets[wk] = ents
            else:
                assert ents == entry_sets[wk], (variant, wk, "entry set differs from other variants!")
            is_new = True
            if variant in ("1R", "2R") and wk == "in":
                is_new = not reproduction_check_target(tr, variant, "in")
            g = gate_stats(m, tr, di)
            results[variant][wk] = (tr, g, is_new)
            tag = "reused/repro-checked" if not is_new else "NEW BACKTEST"
            print(f"  [{variant:<10} {wk:>3}] n={len(tr):>3}  guard={g['guard']:<5}  "
                  f"grossPF={g['gross_pf']:.3f}  netPF={g['net_pf']:.3f}  SR={g['sharpe']:+.2f}  "
                  f"maxDD={g['max_dd']*100:.1f}%  topYr={g['top_year_share']*100:.0f}%  ({tag})")
            print(f"      exits: {reason_breakdown(tr)}")
    print(f"\n  entry-set equality across all 5 variants: IN {len(entry_sets['in'])} entries, "
          f"OUT {len(entry_sets['out'])} entries -- CONFIRMED identical for every variant\n")

    # ---- new-trial accounting ----
    new_cells = []
    for variant in VARIANTS:
        for wk in ("in", "out"):
            if results[variant][wk][2]:
                new_cells.append(f"{variant}/{wk}")
    n_new = len(new_cells)
    print(f"  NEW BACKTESTS this run: {n_new}  ({', '.join(new_cells)})")
    print(f"  CUMULATIVE PROJECT TRIALS: {PRIOR_TRIALS} + {n_new} = {PRIOR_TRIALS + n_new}\n")

    # ---- DSR, reference only, this batch's own in-regime 5-cell pool ----
    pool = np.array([results[v]["in"][1]["sharpe"] for v in VARIANTS if np.isfinite(results[v]["in"][1]["sharpe"])])
    e = expected_max_sharpe(pool)
    print(f"  DSR REFERENCE ONLY (not a gate) -- structural pool = this batch's 5 in-regime cells, "
          f"E[max SR] {e[0]:+.3f} (mu {e[2]:+.3f}, sd {e[3]:.3f}):")
    for variant in VARIANTS:
        g = results[variant]["in"][1]
        if not np.isfinite(g["sharpe"]) or g["n_obs"] < 4:
            print(f"    {variant:<10} DSR n/a")
            continue
        d = deflated_sharpe(sr_best=float(g["sharpe"]), sr_trials=pool, n_obs=int(g["n_obs"]),
                            skewness=g["skew"], excess_kurtosis=g["ekurt"])["dsr"]
        print(f"    {variant:<10} SR {g['sharpe']:+.2f}  DSR {d:.3f}")
    print()

    # ---- compounding table, uniform 3-period layout, every variant ----
    W = 128
    print("=" * W)
    print("  COMPOUNDING -- 1% risk/trade from $100,000, XAUUSD RETEST OR30, vs buy-and-hold XAUUSD")
    print("=" * W)
    print(f"  {'variant':<10} {'period':<26} {'strategy end $':>15} {'strategy %':>11} "
          f"{'trades':>7} {'B&H end $':>12} {'B&H %':>9} {'beats B&H?':>11}")
    print("  " + "-" * (W - 4))
    summary_rows = []
    for variant in VARIANTS:
        tr_in = results[variant]["in"][0]
        tr_out = results[variant]["out"][0]
        for plabel, a, b in PERIODS:
            if plabel == "OUT-OF-REGIME":
                seg, mbh = period_trades(tr_out, a, b), m_out
            else:
                seg, mbh = period_trades(tr_in, a, b), m_in
            end_eq = compound(seg["net_R"])
            eq_bh, p0, p1, d0, d1 = bh(mbh, a, b)
            beats = end_eq > eq_bh
            print(f"  {variant:<10} {plabel:<26} {end_eq:>15,.0f} {end_eq/START_CAP-1:>+10.1%} "
                  f"{len(seg):>7} {eq_bh:>12,.0f} {eq_bh/START_CAP-1:>+8.1%} {('YES' if beats else 'no'):>11}")
            summary_rows.append(dict(variant=variant, period=plabel, strategy_end=end_eq,
                                     n_trades=len(seg), bh_end=eq_bh, beats_bh=beats))
    print("=" * W)

    out_csv = _ROOT / "results" / "orb_exit_variants_xauusd_summary.csv"
    pd.DataFrame(summary_rows).to_csv(out_csv, index=False)
    print(f"\n  results -> {out_csv}")

    # ---- verdict ----
    print("\n  VERDICT:")
    baseline_full = compound(period_trades(results["1R"]["in"][0], "2018-01-01", "2025-12-31")["net_R"])
    print(f"  1R baseline, FULL 2018-2025: ${baseline_full:,.0f}")
    beat_baseline = [r for r in summary_rows if r["period"] == "FULL" and r["variant"] != "1R" and r["strategy_end"] > baseline_full]
    print(f"  Variants beating the 1R baseline on FULL 2018-2025 dollars: "
          f"{[r['variant'] for r in beat_baseline] if beat_baseline else 'NONE'}")
    print(f"  Variants beating buy-and-hold on FULL 2018-2025: "
          f"{[r['variant'] for r in summary_rows if r['period']=='FULL' and r['beats_bh']] or 'NONE'}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
