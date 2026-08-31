#!/usr/bin/env python3
"""
run_regime_switch.py — regime-adaptive strategy selection on BTC/ETH, with
anti-whipsaw and anti-chasing safeguards DESIGNED IN (research/regime_switch.py):
  1. Rank by TRAILING SHARPE over a causal lookback (3mo and 6mo tested).
  2. HYSTERESIS: challenger must beat the incumbent by >0.3 trailing Sharpe.
  3. MINIMUM HOLD: decision dates are spaced exactly one lookback window
     apart — a switch literally cannot happen more often than once per
     window, by construction of the loop, not by a post-hoc check.
  4. CIRCUIT BREAKER: every candidate's trailing Sharpe < 0 -> go to CASH.
  5. Real switching cost (20bps, one Binance taker round-turn equivalent),
     charged only on an actual switch, reported SEPARATELY from each
     candidate's own internal per-trade cost.

CANDIDATES: the SAME 5 families as run_sweep_crypto.py (trend, breakout,
meanrev, momentum, macross), variant v0 of each (the first stated variant,
chosen a priori — same index for every family/instrument, never cherry-
picked from a result), on H4 — the crypto timeframe with the lowest cost_R
in section 13's sweep (7.6% mean), making it the only realistic base for a
real switching system (choosing M15, where section 13 found cost_R 37.5%,
would guarantee failure for a reason already known and unrelated to the
switching logic being tested here).

ANNUALISATION — a genuine correction vs section 13, stated plainly
-------------------------------------------------------------------
Crypto trades every calendar day, so the daily return series built here
(and in run_sweep_crypto.py) has a real, non-missing observation on all
365 days/year, not 252 trading days/year like every FX/index/equity series
in this repo. section 13 used BARS_PER_YEAR=252 (the repo-wide default,
inherited from the FX/index convention) on that 365-observation series,
which UNDERSTATES the correct annualisation factor and therefore
understates Sharpe magnitude by a factor of sqrt(252/365)=0.831x (true
Sharpe ~1.204x larger in magnitude, same sign). **This module uses the
correct factor, 365, throughout.** This does not flip section 13's
verdict — best crypto DSR there was ~0 (best cell Sharpe +0.56, corrected
~+0.67), nowhere near the 0.95 bar either way, and the SURVIVOR gates
besides raw Sharpe sign are unaffected by a constant rescaling — but it IS
a real inconsistency, flagged here rather than silently carried forward,
with a short correction note added to STATE_OF_PLAY.md section 13 (not a
full 90-cell re-run, out of this session's scope, verdict unaffected).

GRID: 2 instruments (BTCUSDT, ETHUSDT) x 2 lookbacks (3mo, 6mo) = 4 configs.

HONESTY GATES: causality (research/regime_switch.py::verify_causality, an
explicit assertion-based check, same pattern as
research/momentum_rotation.py's own look_ahead_guard — the meta-decision
here is not a continuous price signal, so it does not reuse
research/backtest.py::guard_look_ahead), cost-inclusive net returns with
switching cost reported separately, DSR against the cumulative project
pool (this batch's own 4-cell structural pool is the HEADLINE gate, same
convention as every other batch), per-year concentration, an internal
regime split (2018-21 vs 2022-25 — crypto has no genuine pre-2018 holdout,
same stated limitation as section 13), vs buy-and-hold BTC/ETH, AND vs the
single best static H4 config from section 13's own sweep.

Usage: python run_regime_switch.py
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
from research.regime_switch import build_family_returns, run_switching, verify_causality, CASH, FAMILY_NAMES
from run_sweep_crypto import CRYPTO_COST_BPS, INSTRUMENTS, load_bars

BARS_PER_YEAR_CRYPTO = 365  # see module docstring: crypto has a real obs every calendar day
HYSTERESIS = 0.3
CASH_FLOOR = 0.0
SWITCH_COST_BPS = 20.0
LOOKBACKS = [3, 6]
REGIME_SPLIT = pd.Timestamp("2022-01-01", tz="UTC")

PRIOR_TRIALS = 908  # STATE_OF_PLAY.md current cumulative
PRIOR_CSVS = [
    "sweep_progress.csv", "htf_breakout.csv", "sweep_indices.csv",
    "basket_configs.csv", "basket_configs_scored_pre2018.csv",
    "sneaky_pivot.csv", "sneaky_pivot_pre2018.csv", "orb.csv", "orb_pre2018.csv",
    "sweep_m1_scored.csv", "sweep_m1_rth_scored.csv",
    "sweep_crypto_scored.csv", "sweep_stocks_scored.csv", "sweep_stocks_pre2018_scored.csv",
]

OUT_CSV = _ROOT / "results" / "regime_switch.csv"
DECISIONS_CSV = _ROOT / "results" / "regime_switch_decisions.csv"


def sharpe_365(returns: pd.Series) -> float:
    if len(returns) < 2 or returns.std() == 0:
        return float("nan")
    return float(returns.mean() / returns.std() * np.sqrt(BARS_PER_YEAR_CRYPTO))


def year_concentration(returns: pd.Series) -> tuple[float, float, int, int]:
    yr = returns.index.year
    agg = returns.groupby(yr).sum()
    total = float(agg.sum())
    top = float(agg.max()) if len(agg) else float("nan")
    share = (top / total) if total > 0 else float("nan")
    return top, share, int(len(agg)), int((agg > 0).sum())


def buy_and_hold(m: pd.DataFrame) -> dict:
    daily_index = pd.date_range(m.index[0].normalize(), m.index[-1].normalize(), freq="D", tz="UTC")
    daily_close = m["mid_close"].resample("1D").last().reindex(daily_index).ffill()
    ret = daily_close.pct_change().dropna()
    entry_cost = float(m["spread"].iloc[0] / m["mid_close"].iloc[0])
    eq = (1 + ret).cumprod() * (1 - entry_cost)
    return dict(sharpe=sharpe_365(ret), max_dd=max_drawdown(eq), pf=profit_factor(ret))


def best_static_h4(instrument: str) -> dict | None:
    p = _ROOT / "results" / "sweep_crypto_scored.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    sub = df[(df["instrument"] == instrument) & (df["timeframe"] == "H4")]
    if sub.empty:
        return None
    best = sub.sort_values("sharpe", ascending=False).iloc[0]
    return dict(family=best["family"], variant=best["variant"], sharpe=float(best["sharpe"]),
                net_pf=float(best["net_pf"]), max_dd=float(best["max_dd"]), dsr=float(best["dsr"]))


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
    switch_cost_drag = n_switches * SWITCH_COST_BPS / 10_000.0  # total, in return-fraction units

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
        n_decisions=n_decisions, n_switches=n_switches,
        switch_freq_per_year=float(n_switches / max((composite.index[-1] - composite.index[0]).days / 365.25, 1e-9)),
        pct_time_cash=pct_time_cash, switch_cost_drag_total=switch_cost_drag,
        causal_ok=causal_ok,
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
        print(f"[{inst}] {len(m):,} H4 bars {m.index[0].date()} -> {m.index[-1].date()} "
              f"| B&H SR(365) {bh[inst]['sharpe']:+.2f} | best static H4: {statics[inst]}", flush=True)

        for lb in LOOKBACKS:
            res, dlog = run_one(inst, m, lb)
            rows.append(res)
            all_decisions.append(dlog)
            print(f"  {inst} lookback={lb}mo: SR={res['sharpe']:+.2f} PF={res['pf']:.3f} "
                  f"switches={res['n_switches']}/{res['n_decisions']} "
                  f"({res['switch_freq_per_year']:.2f}/yr) time_in_cash={res['pct_time_cash']:.1%} "
                  f"causal_ok={res['causal_ok']}", flush=True)

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    if all_decisions:
        pd.concat(all_decisions, ignore_index=True).to_csv(DECISIONS_CSV, index=False)

    analyze(df, bh, statics)


def analyze(df: pd.DataFrame, bh: dict, statics: dict) -> None:
    n_batch = len(df)
    cumulative = PRIOR_TRIALS + n_batch
    W = 140
    print("\n" + "=" * W)
    print("  REGIME-ADAPTIVE STRATEGY SELECTION — BTC/ETH, safeguarded switching (H4)")
    print("  Hysteresis 0.30, min-hold = 1 evaluation period (structural), circuit breaker floor 0.0,")
    print(f"  switch cost {SWITCH_COST_BPS:.0f}bps/switch. Ann. factor 365 (crypto: real obs every calendar day).")
    print(f"  Configs THIS BATCH: {n_batch}  |  CUMULATIVE PROJECT TRIALS: "
          f"{PRIOR_TRIALS} prior + {n_batch} = {cumulative}")
    print("=" * W)

    if df.empty:
        print("\n  NO configs produced. Investigate before reading anything in.")
        return

    sr_batch = df["sharpe"].fillna(0.0).to_numpy()
    e_struct = expected_max_sharpe(sr_batch)
    print(f"\n  DSR pool (HEADLINE) = STRUCTURAL: this batch's {len(sr_batch)} a priori cells "
          f"-> E[max SR] {e_struct[0]:+.3f} (mu {e_struct[2]:+.3f}, sd {e_struct[3]:.3f})")

    def _dsr(r):
        return deflated_sharpe(sr_best=float(r["sharpe"]), sr_trials=sr_batch, n_obs=int(r["n_obs"]),
                               ann_factor=BARS_PER_YEAR_CRYPTO,
                               skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
                               excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0)["dsr"]
    df = df.copy()
    df["dsr"] = df.apply(_dsr, axis=1)

    prior_vals = []
    for name in PRIOR_CSVS:
        p = _ROOT / "results" / name
        if p.exists():
            s = pd.to_numeric(pd.read_csv(p)["sharpe"], errors="coerce").dropna().to_numpy()
            prior_vals.append(s)
    pool_project = np.concatenate(prior_vals + [sr_batch]) if prior_vals else sr_batch
    e_cumul = expected_max_sharpe(pool_project)
    print(f"  DSR pool (CONTRAST) = project-cumulative {len(pool_project)} "
          f"-> E[max SR] {e_cumul[0]:+.3f}. NOT a gate — sigma-contaminated (research/dsr.py BUG 2).")

    print("\n  FULL COMPARISON TABLE")
    print(f"  {'inst':>7} {'LB':>4} {'SR':>7} {'DSR':>5} {'PF':>6} {'maxDD':>7} {'totRet':>8} "
          f"{'switches':>9} {'/yr':>5} {'%cash':>6} {'top%':>5} {'regA':>6} {'regB':>6} {'reg?':>5} {'causal':>6}")
    print("  " + "-" * (W - 4))
    for _, r in df.sort_values(["instrument", "lookback_months"]).iterrows():
        share = r["top_year_share"]
        print(f"  {r['instrument']:>7} {int(r['lookback_months']):>3}m {r['sharpe']:>+7.2f} "
              f"{r['dsr']:>5.2f} {r['pf']:>6.3f} {r['max_dd'] * 100:>6.1f}% {r['total_ret'] * 100:>7.1f}% "
              f"{int(r['n_switches']):>6}/{int(r['n_decisions']):>2} {r['switch_freq_per_year']:>4.2f} "
              f"{r['pct_time_cash'] * 100:>5.1f}% "
              + (f"{share * 100:>4.0f}%" if np.isfinite(share) else f"{'n/a':>5}")
              + f" {r['regime_a_sharpe']:>+6.2f} {r['regime_b_sharpe']:>+6.2f} "
              f"{'YES' if r['regime_holds'] else 'no':>5} {'YES' if r['causal_ok'] else 'FAIL':>6}")
    print("=" * W)

    print("\n  vs BUY-AND-HOLD and vs BEST STATIC H4 CONFIG (section 13):")
    for inst in df["instrument"].unique():
        sub = df[df["instrument"] == inst]
        best = sub.sort_values("sharpe", ascending=False).iloc[0]
        b = bh.get(inst, {})
        s = statics.get(inst)
        print(f"    {inst:>7}: adaptive best SR {best['sharpe']:+.2f} (lookback {int(best['lookback_months'])}mo)  "
              f"vs  B&H SR {b.get('sharpe', float('nan')):+.2f}  "
              f"vs  best static H4 ({s['family']} v{s['variant']}) SR {s['sharpe']:+.2f}"
              if s else f"    {inst:>7}: no static reference found")
        beat_bh = best["sharpe"] > b.get("sharpe", float("-inf"))
        beat_static = s is not None and best["sharpe"] > s["sharpe"]
        print(f"      -> beats buy-and-hold: {'YES' if beat_bh else 'no'}   "
              f"beats best static: {'YES' if beat_static else 'no'}")

    print("\n  SAFEGUARD CHECK — did hysteresis/min-hold actually keep switching LOW?")
    for _, r in df.sort_values(["instrument", "lookback_months"]).iterrows():
        print(f"    {r['instrument']} {int(r['lookback_months'])}mo: {int(r['n_switches'])} switches over "
              f"{int(r['n_decisions'])} decision points ({r['switch_freq_per_year']:.2f}/year), "
              f"{r['pct_time_cash'] * 100:.1f}% of days in cash via the circuit breaker.")

    n_causal_fail = int((~df["causal_ok"]).sum())
    print(f"\n  Causality check: {len(df) - n_causal_fail}/{len(df)} configs PASS "
          f"(independent re-derivation of every trailing-Sharpe window).")

    print(f"\n  Cumulative project trials after this batch: {cumulative} "
          f"({PRIOR_TRIALS} prior + {n_batch} regime-switch cells)")
    print("  " + "=" * (W - 4))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
