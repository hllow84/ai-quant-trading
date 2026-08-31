#!/usr/bin/env python3
"""
run_regime_switch_longlb.py — PART A of the section-15 follow-up: does
switching frequency drop toward something sane as the lookback lengthens?

Reuses research/regime_switch.py's engine (build_family_returns,
run_switching, verify_causality) COMPLETELY UNCHANGED — this file only adds
two new points to the lookback_months axis (12, 24), it does not touch any
safeguard logic (hysteresis margin 0.3, circuit breaker floor 0.0, switch
cost 20bps — all identical to section 15).

NEW TRIALS THIS BATCH: 2 instruments x 2 lookbacks (12mo, 24mo) = 4 configs.
The existing lookback=3/6 results (results/regime_switch.csv, section 15)
are LOADED, not re-run, and shown alongside for the full 4-lookback
comparison table the task asks for — they are NOT double-counted.

Usage: python run_regime_switch_longlb.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.dsr import deflated_sharpe, expected_max_sharpe
from research.metrics import max_drawdown, profit_factor
from research.regime_switch import build_family_returns, run_switching, verify_causality, CASH
from run_sweep_crypto import CRYPTO_COST_BPS, INSTRUMENTS, load_bars
from run_regime_switch import (
    BARS_PER_YEAR_CRYPTO, HYSTERESIS, CASH_FLOOR, SWITCH_COST_BPS, REGIME_SPLIT,
    sharpe_365, year_concentration, buy_and_hold, best_static_h4,
)

NEW_LOOKBACKS = [12, 24]
PRIOR_TRIALS = 912  # STATE_OF_PLAY.md current cumulative, before this batch
PRIOR_CSVS = [
    "sweep_progress.csv", "htf_breakout.csv", "sweep_indices.csv",
    "basket_configs.csv", "basket_configs_scored_pre2018.csv",
    "sneaky_pivot.csv", "sneaky_pivot_pre2018.csv", "orb.csv", "orb_pre2018.csv",
    "sweep_m1_scored.csv", "sweep_m1_rth_scored.csv",
    "sweep_crypto_scored.csv", "sweep_stocks_scored.csv", "sweep_stocks_pre2018_scored.csv",
    "regime_switch.csv",
]

OLD_CSV = _ROOT / "results" / "regime_switch.csv"
OUT_CSV = _ROOT / "results" / "regime_switch_longlb.csv"
DECISIONS_CSV = _ROOT / "results" / "regime_switch_longlb_decisions.csv"
COMBINED_CSV = _ROOT / "results" / "regime_switch_all_lookbacks.csv"


def run_one(instrument: str, m: pd.DataFrame, lookback: int) -> tuple[dict, pd.DataFrame]:
    fam_returns = build_family_returns(m, CRYPTO_COST_BPS, tf_key="H4", variant_index=0)
    composite, decision_log, active_by_day = run_switching(
        fam_returns, lookback_months=lookback, hysteresis=HYSTERESIS,
        cash_floor=CASH_FLOOR, switch_cost_bps=SWITCH_COST_BPS,
    )
    causal_ok = verify_causality(decision_log, fam_returns, lookback)

    n_switches = int((decision_log["new_active"] != decision_log["incumbent"]).sum())
    n_decisions = len(decision_log)
    pct_time_cash = float((active_by_day == CASH).mean())
    switch_rate = float(n_switches / n_decisions) if n_decisions else float("nan")

    is_m = composite.index < REGIME_SPLIT
    oos_m = composite.index >= REGIME_SPLIT
    regime_a_sharpe = sharpe_365(composite[is_m])
    regime_b_sharpe = sharpe_365(composite[oos_m])
    regime_holds = bool(np.isfinite(regime_a_sharpe) and np.isfinite(regime_b_sharpe)
                        and regime_a_sharpe > 0 and regime_b_sharpe > 0)

    top_R, top_share, n_years, n_pos_years = year_concentration(composite)
    eq = (1 + composite).cumprod()

    res = dict(
        instrument=instrument, lookback_months=lookback,
        n_decisions=n_decisions, n_switches=n_switches, switch_rate=switch_rate,
        switch_freq_per_year=float(n_switches / max((composite.index[-1] - composite.index[0]).days / 365.25, 1e-9)),
        pct_time_cash=pct_time_cash, causal_ok=causal_ok,
        sharpe=sharpe_365(composite), pf=profit_factor(composite), max_dd=max_drawdown(eq),
        total_ret=float(eq.iloc[-1] - 1.0), n_obs=int(len(composite)),
        skew=float(composite.skew()), ekurt=float(composite.kurtosis()),
        top_year_R=top_R, top_year_share=top_share, n_years=n_years, n_pos_years=n_pos_years,
        regime_a_sharpe=regime_a_sharpe, regime_b_sharpe=regime_b_sharpe, regime_holds=regime_holds,
    )
    decision_log = decision_log.copy()
    decision_log["instrument"] = instrument
    decision_log["lookback_months"] = lookback
    return res, decision_log


def _dsr_row(r, pool, ann_factor=BARS_PER_YEAR_CRYPTO):
    if not np.isfinite(r["sharpe"]) or r["n_obs"] < 4:
        return float("nan")
    return deflated_sharpe(sr_best=float(r["sharpe"]), sr_trials=pool, n_obs=int(r["n_obs"]),
                           ann_factor=ann_factor,
                           skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
                           excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0)["dsr"]


def main() -> None:
    rows, all_decisions, bh, statics = [], [], {}, {}
    for inst, tf_paths in INSTRUMENTS.items():
        path = tf_paths["H4"]
        if not path.exists():
            print(f"[{inst}] MISSING {path.name} — skipped.", flush=True)
            continue
        print(f"\n[{inst}] loading H4 ...", flush=True)
        m = load_bars(path)
        bh[inst] = buy_and_hold(m)
        statics[inst] = best_static_h4(inst)

        for lb in NEW_LOOKBACKS:
            res, dlog = run_one(inst, m, lb)
            rows.append(res)
            all_decisions.append(dlog)
            print(f"  {inst} lookback={lb}mo: SR={res['sharpe']:+.2f} PF={res['pf']:.3f} "
                  f"switches={res['n_switches']}/{res['n_decisions']} "
                  f"({res['switch_rate']:.0%} of decisions, {res['switch_freq_per_year']:.2f}/yr) "
                  f"time_in_cash={res['pct_time_cash']:.1%} causal_ok={res['causal_ok']}", flush=True)

    new_df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    new_df.to_csv(OUT_CSV, index=False)
    if all_decisions:
        pd.concat(all_decisions, ignore_index=True).to_csv(DECISIONS_CSV, index=False)

    # ── DSR for the NEW cells only, against their own a priori structural pool
    sr_new = new_df["sharpe"].fillna(0.0).to_numpy()
    e_struct = expected_max_sharpe(sr_new)
    new_df["dsr"] = new_df.apply(lambda r: _dsr_row(r, sr_new), axis=1)

    # ── load the OLD (3/6mo) cells, NOT re-run, recompute their DSR from
    # their own saved sharpe/skew/ekurt/n_obs against THEIR OWN original
    # 4-cell pool (unchanged from section 15 — this reproduces, not re-derives).
    old_df = pd.read_csv(OLD_CSV)
    sr_old = old_df["sharpe"].fillna(0.0).to_numpy()
    old_df["dsr"] = old_df.apply(lambda r: _dsr_row(r, sr_old), axis=1)

    combined = pd.concat([old_df, new_df], ignore_index=True, sort=False)
    combined.to_csv(COMBINED_CSV, index=False)

    n_batch = len(new_df)
    cumulative = PRIOR_TRIALS + n_batch

    W = 148
    print("\n" + "=" * W)
    print("  PART A — LOOKBACK EXPANSION: does switching frequency drop as the window lengthens?")
    print("  Engine (research/regime_switch.py) UNCHANGED: hysteresis 0.30, circuit breaker floor 0.0, "
          "switch cost 20bps.")
    print(f"  NEW configs this batch: {n_batch} (12mo, 24mo x 2 instruments). "
          f"3mo/6mo cells LOADED from section 15, not re-run.")
    print(f"  CUMULATIVE PROJECT TRIALS: {PRIOR_TRIALS} prior + {n_batch} = {cumulative}")
    print("=" * W)

    print(f"\n  {'inst':>7} {'LB':>4} {'SR':>7} {'DSR':>5} {'PF':>6} {'maxDD':>7} {'totRet':>8} "
          f"{'switches':>9} {'switch%':>8} {'/yr':>5} {'%cash':>6} {'regA':>6} {'regB':>6} {'reg?':>5}")
    print("  " + "-" * (W - 4))
    for _, r in combined.sort_values(["instrument", "lookback_months"]).iterrows():
        print(f"  {r['instrument']:>7} {int(r['lookback_months']):>3}m {r['sharpe']:>+7.2f} "
              f"{r['dsr']:>5.2f} {r['pf']:>6.3f} {r['max_dd'] * 100:>6.1f}% {r['total_ret'] * 100:>7.1f}% "
              f"{int(r['n_switches']):>6}/{int(r['n_decisions']):>2} "
              f"{r['n_switches'] / r['n_decisions'] * 100 if r['n_decisions'] else float('nan'):>7.1f}% "
              f"{r['switch_freq_per_year']:>4.2f} {r['pct_time_cash'] * 100:>5.1f}% "
              f"{r['regime_a_sharpe']:>+6.2f} {r['regime_b_sharpe']:>+6.2f} "
              f"{'YES' if r['regime_holds'] else 'no':>5}")
    print("=" * W)

    print("\n  SWITCHING FREQUENCY BY LOOKBACK — the key diagnostic")
    for lb in sorted(combined["lookback_months"].unique()):
        sub = combined[combined["lookback_months"] == lb]
        rate = (sub["n_switches"].sum() / sub["n_decisions"].sum()) if sub["n_decisions"].sum() else float("nan")
        print(f"    {int(lb):>3}mo lookback: {rate:.1%} of decision points triggered a switch "
              f"(pooled across {sub['instrument'].nunique()} instruments, "
              f"{int(sub['n_decisions'].sum())} total decisions)")

    print("\n  vs BUY-AND-HOLD and vs BEST STATIC H4 CONFIG (section 13):")
    for inst in combined["instrument"].unique():
        sub = combined[combined["instrument"] == inst]
        best = sub.sort_values("sharpe", ascending=False).iloc[0]
        b = bh.get(inst, {})
        s = statics.get(inst)
        print(f"    {inst:>7}: best-of-4-lookbacks SR {best['sharpe']:+.2f} "
              f"(lookback {int(best['lookback_months'])}mo)  vs  B&H SR {b.get('sharpe', float('nan')):+.2f}  "
              f"vs  best static H4 ({s['family']} v{s['variant']}) SR {s['sharpe']:+.2f}" if s else "")
        if s:
            print(f"      -> beats buy-and-hold: {'YES' if best['sharpe'] > b.get('sharpe', float('-inf')) else 'no'}   "
                  f"beats best static: {'YES' if best['sharpe'] > s['sharpe'] else 'no'}")

    print(f"\n  Cumulative project trials after this batch: {cumulative} "
          f"({PRIOR_TRIALS} prior + {n_batch} new lookback cells)")
    print("  " + "=" * (W - 4))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
