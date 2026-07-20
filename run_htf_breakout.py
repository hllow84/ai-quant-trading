#!/usr/bin/env python3
"""
run_htf_breakout.py — HTF-trend-gated swing-level breakout (continuation).

Grid (SMALL and stated, breadth not depth):
    3 trading timeframes (M5, M15, M30)
  x 2 R targets          (1.5R, 2.0R)
  x 2 trading-TF pivot N (3, 5)
  = 12 configs THIS BATCH.

Anti-overfitting: this family is adjacent to the breakout-retest family that
already died in the 75-config sweep, so the DSR haircut is applied against the
CUMULATIVE trial count (75 prior + 12 here = 87), NOT against this batch alone.
Any config clearing the haircut is then re-checked on a fixed IS/OOS split.

Same harness as run_sweep.py: real per-bar spread (round-turn) + $0.07/oz
commission + news-hour slippage, 1% risk/trade, look-ahead guard on every
config, daily-aggregated Sharpe (252/yr), FTMO Phase-1 rolling monthly starts.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_mid, resample_mid, load_daily_spot
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor, deflated_sharpe_ratio
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns,
    build_position_series,
)
from research.ftmo_rules import rolling_pass_rate
from strategies.htf_swing_breakout import (
    htf_swing_breakout, h1_trend, TIMEFRAMES, TF_DELTA, PIVOT_N, R_TARGETS,
)

BARS_PER_YEAR = 252
OOS_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")   # same fixed cut as the sweep
MIN_OOS_TRADES = 20
PRIOR_TRIALS = 75                                   # the completed 5x5x3 sweep
DSR_BAR = 0.95
FTMO_BAR = 0.30
BH_SHARPE = 1.194                                   # buy-and-hold gold benchmark

OUT_CSV = _ROOT / "results" / "htf_breakout.csv"


def _coerce(ts):
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tz is None else t.tz_convert("UTC")


def _split(trades):
    exit_t = pd.to_datetime(trades["exit_time"], utc=True)
    is_m, oos_m = exit_t < OOS_SPLIT, exit_t >= OOS_SPLIT
    def pf(mask):
        return profit_factor(trades.loc[mask, "net_R"]) if mask.any() else float("nan")
    def sr(mask):
        sub = trades.loc[mask]
        if sub.empty:
            return float("nan")
        d = sub.groupby(pd.to_datetime(sub["exit_time"], utc=True).dt.normalize())["ret_frac"].sum()
        return sharpe(d, BARS_PER_YEAR) if len(d) > 1 else float("nan")
    return int(is_m.sum()), int(oos_m.sum()), pf(is_m), pf(oos_m), sr(is_m), sr(oos_m)


def score(m, params, tf_key, trend, daily_index, d0, d1) -> dict:
    cands = htf_swing_breakout(m, params, TF_DELTA[tf_key], trend)
    for tr in cands:
        tr["session_end"] = _coerce(tr["session_end"])
        tr["entry_time"] = _coerce(tr["entry_time"])

    trades = de_overlap(simulate_trades(m, cands, strictly_after=True))
    if trades.empty:
        return dict(n_trades=0, guard="N/A")

    pos = build_position_series(trades, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"

    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    is_n, oos_n, is_pf, oos_pf, is_sr, oos_sr = _split(trades)
    ftmo = rolling_pass_rate(trades, d0, d1, phase=1, max_days=60)

    return dict(
        n_trades=len(trades), guard=guard, n_cands=len(cands),
        gross_pf=profit_factor(trades["gross_R"]),
        net_pf=profit_factor(trades["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR),
        skew=float(daily_ret.skew()), ekurt=float(daily_ret.kurtosis()),
        max_dd=max_drawdown(equity),
        gross_R_mean=float(trades["gross_R"].mean()),
        cost_R_mean=float(trades["cost_R"].mean()),
        net_R_mean=float(trades["net_R"].mean()),
        win_rate=float((trades["net_R"] > 0).mean()),
        risk_med=float(trades["risk_price"].median()),
        n_targets=int((trades["reason"] == "target").sum()),
        n_stops=int((trades["reason"] == "stop").sum()),
        n_time=int((trades["reason"] == "time").sum()),
        n_obs=int(len(daily_ret)),
        is_trades=is_n, oos_trades=oos_n,
        is_pf=is_pf, oos_pf=oos_pf, is_sharpe=is_sr, oos_sharpe=oos_sr,
        ftmo_pass_rate=ftmo["pass_rate"], ftmo_n_challenges=ftmo["n_challenges"],
    )


def main():
    print("Loading M1 mid (real Dukascopy XAUUSD spot, UTC) ...", flush=True)
    m1 = load_m1_mid()
    daily_index = load_daily_spot().index
    d0, d1 = daily_index[0], daily_index[-1]
    print(f"  M1 bars {len(m1):,}  {m1.index[0].date()} -> {m1.index[-1].date()}", flush=True)

    h1 = resample_mid(m1, "1h")
    trend = h1_trend(h1)
    frac = trend.value_counts(normalize=True)
    print(f"  H1 bars {len(h1):,} | trend state: up {frac.get(1.0,0):.1%} "
          f"down {frac.get(-1.0,0):.1%} flat {frac.get(0.0,0):.1%}", flush=True)

    rows = []
    n_cfg = len(TIMEFRAMES) * len(R_TARGETS) * len(PIVOT_N)
    i = 0
    for tf_key, freq in TIMEFRAMES.items():
        print(f"[{tf_key}] resampling ...", flush=True)
        m = resample_mid(m1, freq)
        print(f"[{tf_key}] {len(m):,} bars", flush=True)
        for N in PIVOT_N:
            for R in R_TARGETS:
                i += 1
                p = dict(N=N, R=R)
                res = score(m, p, tf_key, trend, daily_index, d0, d1)
                rows.append(dict(timeframe=tf_key, pivot_N=N, R=R, **res))
                print(f"  [{i}/{n_cfg}] {tf_key:>3} N={N} R={R} "
                      f"n={res.get('n_trades',0):>5} "
                      f"grPF={res.get('gross_pf',float('nan')):.2f} "
                      f"netPF={res.get('net_pf',float('nan')):.2f} "
                      f"SR={res.get('sharpe',float('nan')):+.2f} "
                      f"guard={res.get('guard','?')[:4]}", flush=True)

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    analyze(df, n_cfg)


def analyze(df: pd.DataFrame, n_cfg: int):
    traded = df[df["n_trades"] > 0].copy()
    cumulative = PRIOR_TRIALS + n_cfg

    # DSR trial universe = this batch's Sharpes PLUS the prior sweep's, so the
    # haircut reflects everything that has been tried on this dataset.
    sr_batch = traded["sharpe"].fillna(0.0).to_numpy()
    prior_csv = _ROOT / "results" / "sweep_progress.csv"
    if prior_csv.exists():
        prior = pd.to_numeric(pd.read_csv(prior_csv)["sharpe"], errors="coerce").fillna(0.0).to_numpy()
        sr_all = np.concatenate([prior, sr_batch])
        prior_note = f"{len(prior)} prior Sharpes loaded from sweep_progress.csv"
    else:
        sr_all = sr_batch
        prior_note = "prior sweep CSV missing — batch-only trial set (WEAKER haircut)"

    def _dsr(r):
        if not np.isfinite(r["sharpe"]) or r["n_obs"] < 4:
            return np.nan
        prob, _ = deflated_sharpe_ratio(
            sr_best=float(r["sharpe"]), sr_trials=sr_all, n_obs=int(r["n_obs"]),
            skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
            excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0)
        return prob
    traded["dsr"] = traded.apply(_dsr, axis=1)
    traded["oos_holds"] = ((traded["is_pf"] > 1.0) & (traded["oos_pf"] > 1.0)
                           & (traded["oos_trades"] >= MIN_OOS_TRADES)
                           & (traded["oos_sharpe"] > 0))
    traded["dsr_survives"] = traded["dsr"] > DSR_BAR
    traded["ftmo_clears"] = traded["ftmo_pass_rate"] >= FTMO_BAR
    traded["SURVIVOR"] = traded["dsr_survives"] & traded["oos_holds"] & traded["ftmo_clears"]

    W = 112
    print("\n" + "=" * W)
    print("  HTF-TREND-GATED SWING BREAKOUT (CONTINUATION) — XAUUSD real spot, 2018-2025 UTC")
    print("  Cost: real per-bar spread (round-turn) + $0.07/oz commission + news-hour slippage | 1% risk/trade | NO tuning")
    print(f"  Configs THIS BATCH: {n_cfg}   |   CUMULATIVE TRIAL COUNT (DSR N): {PRIOR_TRIALS} prior + {n_cfg} = {cumulative}")
    print(f"  DSR trial universe: {prior_note} + {len(sr_batch)} this batch = {len(sr_all)}")
    print(f"  Gates: DSR > {DSR_BAR} AND OOS holds (IS&OOS netPF>1, OOS SR>0, OOS trades>={MIN_OOS_TRADES}) AND FTMO P1 >= {FTMO_BAR:.0%}")
    print("=" * W)
    print(f"  {'TF':>3} {'N':>2} {'R':>4} {'grPF':>5} {'netPF':>5} {'Sharpe':>7} {'DSR':>5} "
          f"{'maxDD':>6} {'trades':>6} {'win%':>5} {'FTMO%':>6} {'OOS?':>4} {'guard':>5}")
    print("  " + "-" * (W - 4))
    for _, r in traded.sort_values("sharpe", ascending=False).iterrows():
        ftmo = r["ftmo_pass_rate"] * 100 if np.isfinite(r["ftmo_pass_rate"]) else float("nan")
        print(f"  {r['timeframe']:>3} {int(r['pivot_N']):>2} {r['R']:>4.1f} "
              f"{r['gross_pf']:>5.2f} {r['net_pf']:>5.2f} {r['sharpe']:>+7.2f} "
              f"{r['dsr']:>5.2f} {r['max_dd']*100:>5.1f}% {int(r['n_trades']):>6} "
              f"{r['win_rate']*100:>4.1f}% {ftmo:>5.1f}% {'YES' if r['oos_holds'] else 'no':>4} "
              f"{r['guard'][:5]:>5}")
    print("=" * W)

    print("\n  GROSS vs NET R DECOMPOSITION (is there an edge BEFORE costs?)")
    print(f"  {'TF':>3} {'N':>2} {'R':>4} {'grossR/trd':>11} {'costR/trd':>10} {'netR/trd':>9} {'medR $/oz':>10} {'cost as %R':>11}")
    print("  " + "-" * 66)
    for _, r in traded.sort_values(["timeframe", "pivot_N", "R"]).iterrows():
        print(f"  {r['timeframe']:>3} {int(r['pivot_N']):>2} {r['R']:>4.1f} "
              f"{r['gross_R_mean']:>+11.4f} {r['cost_R_mean']:>10.4f} {r['net_R_mean']:>+9.4f} "
              f"{r['risk_med']:>10.2f} {r['cost_R_mean']*100:>10.1f}%")

    survivors = traded[traded["SURVIVOR"]]
    best = traded.sort_values("sharpe", ascending=False).iloc[0]

    print("\n  VERDICT")
    print("  " + "-" * 70)
    if len(survivors):
        print(f"  {len(survivors)} config(s) SURVIVED all three gates:")
        for _, r in survivors.iterrows():
            print(f"    {r['timeframe']} N={int(r['pivot_N'])} R={r['R']}: SR {r['sharpe']:+.2f}, "
                  f"DSR {r['dsr']:.3f}, netPF {r['net_pf']:.2f}, "
                  f"IS PF {r['is_pf']:.2f} / OOS PF {r['oos_pf']:.2f}, FTMO {r['ftmo_pass_rate']*100:.1f}%")
    else:
        print("  NO config survived. Zero cleared DSR + OOS + FTMO.")
        print(f"  Best raw net Sharpe: {best['timeframe']} N={int(best['pivot_N'])} R={best['R']} "
              f"-> SR {best['sharpe']:+.2f}, netPF {best['net_pf']:.2f}")
        print(f"    - DSR {best['dsr']:.3f} (need > {DSR_BAR}) -> "
              f"{'PASS' if best['dsr'] > DSR_BAR else f'FAIL: inside the noise of {cumulative} cumulative trials'}")
        print(f"    - OOS holds: {'YES' if best['oos_holds'] else 'NO'} "
              f"(IS PF {best['is_pf']:.2f} / OOS PF {best['oos_pf']:.2f}, OOS SR {best['oos_sharpe']:+.2f}, "
              f"OOS trades {int(best['oos_trades'])})")
        fp = best['ftmo_pass_rate'] * 100 if np.isfinite(best['ftmo_pass_rate']) else float('nan')
        print(f"    - FTMO P1 pass {fp:.1f}% (need >= {FTMO_BAR:.0%})")

    print(f"\n  vs BUY-AND-HOLD GOLD (Sharpe {BH_SHARPE:.2f}, MDD 20.4%, CAGR 20.7%):")
    print(f"    best strategy net Sharpe {best['sharpe']:+.2f} -> "
          f"{'BEATS' if best['sharpe'] > BH_SHARPE else 'LOSES TO'} buy-and-hold "
          f"(gap {best['sharpe'] - BH_SHARPE:+.2f})")

    print("\n  Batch summary:")
    print(f"    positive net Sharpe : {(traded['sharpe'] > 0).sum()} / {len(traded)}")
    print(f"    net PF > 1          : {(traded['net_pf'] > 1).sum()} / {len(traded)}")
    print(f"    gross PF > 1        : {(traded['gross_pf'] > 1).sum()} / {len(traded)}")
    print(f"    look-ahead guard    : {(traded['guard'] == 'PASS').sum()} / {len(traded)} PASS")
    print(f"    OOS holds           : {traded['oos_holds'].sum()} / {len(traded)}")
    print(f"    clears DSR haircut  : {traded['dsr_survives'].sum()} / {len(traded)}")
    print(f"\n  Results -> {OUT_CSV}")

    traded.to_csv(_ROOT / "results" / "htf_breakout_scored.csv", index=False)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
