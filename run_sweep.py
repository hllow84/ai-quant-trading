#!/usr/bin/env python3
"""
run_sweep.py — Systematic, resumable sweep of the 5 strategy families across
5 execution timeframes (M5/M15/M30/H1/H4) on real XAUUSD spot.

Grid  : instruments x timeframes x families x stated variants.
        Only ONE instrument (XAUUSD) has qualifying real-spot-with-spread data
        (EURUSD/GBPUSD probes are empty / spread-less; yfinance XAUUSD is futures
        and banned). So the grid is 1 x 5 x 5 x 3 = 75 configs.

Rules enforced per config (from CLAUDE.md):
  - Signals + resolution on the SAME execution timeframe (strictly_after=True):
    the entry bar's own range is never re-used -> no look-ahead by construction.
  - Real cost model: REAL per-bar spread (round-turn) + $0.07/oz commission +
    news-hour slippage (the legacy gold $/oz model in ftmo_engine).
  - Look-ahead guard on EVERY config (held-position vs same/next-bar return corr).
  - 1% risk/trade, defined stop = 1R, stated fixed-R target, max-hold cap. NO tuning.

Resumable: each finished config is appended to results/sweep_progress.csv and a
per-config marker is dropped in results/markers/. A re-run skips any config whose
key already appears in the CSV.

After the full grid completes, run_sweep.py --analyze (auto-invoked when the grid
is complete) enforces the anti-overfitting checks:
  - true trial count = number of rows in the CSV,
  - Deflated Sharpe haircut using the FULL trial count,
  - out-of-sample split (fixed 2023-01-01 UTC cut) — edge must hold in BOTH halves,
  - FTMO Phase-1 pass rate,
and prints the ranked leaderboard + a plain keep/kill verdict.
"""

from __future__ import annotations

import sys
import csv
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_mid, resample_mid, load_daily_spot
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import (
    sharpe, max_drawdown, profit_factor, hit_rate, deflated_sharpe_ratio,
)
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns,
    build_position_series,
)
from research.ftmo_rules import rolling_pass_rate
from strategies.sweep_families import FAMILIES, TIMEFRAMES, TF_DELTA

BARS_PER_YEAR = 252            # P&L is aggregated to calendar-daily regardless of exec TF
OOS_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")   # fixed IS/OOS cut (no peeking)
MIN_OOS_TRADES = 20            # below this an OOS PF is too noisy to trust
INSTRUMENT = "XAUUSD"

CSV_PATH = _ROOT / "results" / "sweep_progress.csv"
MARKER_DIR = _ROOT / "results" / "markers"

CSV_FIELDS = [
    "instrument", "timeframe", "family", "variant", "params",
    "n_trades", "guard", "gross_pf", "net_pf", "sharpe", "skew", "ekurt",
    "max_dd", "gross_R_mean", "cost_R_mean", "net_R_mean", "risk_med",
    "n_targets", "n_stops", "n_time", "n_obs",
    "is_trades", "oos_trades", "is_pf", "oos_pf", "is_sharpe", "oos_sharpe",
    "ftmo_pass_rate", "ftmo_n_challenges",
]


# ── helpers ─────────────────────────────────────────────────────────────────────

def _coerce_utc(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tz is None else t.tz_convert("UTC")


def _load_done_keys() -> set:
    if not CSV_PATH.exists():
        return set()
    done = set()
    with CSV_PATH.open(newline="") as f:
        for row in csv.DictReader(f):
            done.add((row["instrument"], row["timeframe"], row["family"], row["variant"]))
    return done


def _append_row(row: dict) -> None:
    new = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
        f.flush()


def _split_metrics(trades: pd.DataFrame):
    """IS/OOS net PF + Sharpe on a fixed calendar cut."""
    exit_t = pd.to_datetime(trades["exit_time"], utc=True)
    is_m  = exit_t < OOS_SPLIT
    oos_m = ~is_m
    def _pf(mask):
        return profit_factor(trades.loc[mask, "net_R"]) if mask.any() else float("nan")
    def _sr(mask):
        # daily-aggregated Sharpe within the segment
        sub = trades.loc[mask]
        if sub.empty:
            return float("nan")
        d = sub.groupby(pd.to_datetime(sub["exit_time"], utc=True).dt.normalize())["ret_frac"].sum()
        return sharpe(d, BARS_PER_YEAR) if len(d) > 1 else float("nan")
    return (int(is_m.sum()), int(oos_m.sum()),
            _pf(is_m), _pf(oos_m), _sr(is_m), _sr(oos_m))


def score_config(m, family_fn, params, tf_key, daily_index, d0, d1) -> dict:
    tf_delta = TF_DELTA[tf_key]
    cands = family_fn(m, params, tf_delta)
    # coerce session_end (some builders emit tz-naive via numpy) to tz-aware UTC
    for tr in cands:
        tr["session_end"] = _coerce_utc(tr["session_end"])
        tr["entry_time"] = _coerce_utc(tr["entry_time"])

    raw = simulate_trades(m, cands, strictly_after=True)   # resolve on SAME TF
    trades = de_overlap(raw)
    n = len(trades)
    if n == 0:
        return dict(n_trades=0, guard="N/A")

    pos = build_position_series(trades, m.index)
    ret = m["mid_close"].pct_change()
    try:
        guard_look_ahead(pos, ret, threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"

    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    is_n, oos_n, is_pf, oos_pf, is_sr, oos_sr = _split_metrics(trades)
    ftmo = rolling_pass_rate(trades, d0, d1, phase=1, max_days=60)

    return dict(
        n_trades=n, guard=guard,
        gross_pf=profit_factor(trades["gross_R"]),
        net_pf=profit_factor(trades["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR),
        skew=float(daily_ret.skew()), ekurt=float(daily_ret.kurtosis()),
        max_dd=max_drawdown(equity),
        gross_R_mean=float(trades["gross_R"].mean()),
        cost_R_mean=float(trades["cost_R"].mean()),
        net_R_mean=float(trades["net_R"].mean()),
        risk_med=float(trades["risk_price"].median()),
        n_targets=int((trades["reason"] == "target").sum()),
        n_stops=int((trades["reason"] == "stop").sum()),
        n_time=int((trades["reason"] == "time").sum()),
        n_obs=int(len(daily_ret)),
        is_trades=is_n, oos_trades=oos_n,
        is_pf=is_pf, oos_pf=oos_pf, is_sharpe=is_sr, oos_sharpe=oos_sr,
        ftmo_pass_rate=ftmo["pass_rate"], ftmo_n_challenges=ftmo["n_challenges"],
    )


# ── sweep driver ─────────────────────────────────────────────────────────────────

def run_grid():
    MARKER_DIR.mkdir(parents=True, exist_ok=True)
    done = _load_done_keys()
    total = len(TIMEFRAMES) * sum(len(v[1]) for v in FAMILIES.values())
    print(f"Grid: {INSTRUMENT} x {len(TIMEFRAMES)} TF x {len(FAMILIES)} families "
          f"x variants = {total} configs. Already done: {len(done)}.", flush=True)

    print("Loading M1 mid (real spot) ...", flush=True)
    m1 = load_m1_mid()
    daily_index = load_daily_spot().index
    d0, d1 = daily_index[0], daily_index[-1]
    print(f"  M1 bars: {len(m1):,}  span {m1.index[0].date()} -> {m1.index[-1].date()}", flush=True)

    done_ct = len(done)
    for tf_key, tf_freq in TIMEFRAMES.items():
        # only resample once we actually need this TF (skip if all its configs done)
        tf_keys = [(INSTRUMENT, tf_key, fam, str(i))
                   for fam, (_, variants) in FAMILIES.items()
                   for i in range(len(variants))]
        if all(k in done for k in tf_keys):
            print(f"[{tf_key}] all configs already done — skip.", flush=True)
            continue
        print(f"[{tf_key}] resampling ({tf_freq}) ...", flush=True)
        m = resample_mid(m1, tf_freq)
        print(f"[{tf_key}] {len(m):,} bars.", flush=True)

        for fam, (fn, variants) in FAMILIES.items():
            for i, params in enumerate(variants):
                key = (INSTRUMENT, tf_key, fam, str(i))
                if key in done:
                    continue
                res = score_config(m, fn, params, tf_key, daily_index, d0, d1)
                row = dict(instrument=INSTRUMENT, timeframe=tf_key, family=fam,
                           variant=str(i), params=str(params))
                for fld in CSV_FIELDS:
                    if fld not in row:
                        row[fld] = res.get(fld, "")
                _append_row(row)
                (MARKER_DIR / f"{INSTRUMENT}_{tf_key}_{fam}_{i}.done").write_text("ok")
                done_ct += 1
                sr = res.get("sharpe", float("nan"))
                npf = res.get("net_pf", float("nan"))
                print(f"  [{done_ct}/{total}] {tf_key:>3} {fam:<9} v{i} "
                      f"n={res.get('n_trades',0):>5} netPF={npf if isinstance(npf,str) else f'{npf:.2f}':>5} "
                      f"SR={sr if isinstance(sr,str) else f'{sr:+.2f}':>6} guard={res.get('guard','?')[:4]}",
                      flush=True)

    print(f"\nGrid complete: {done_ct}/{total} configs in {CSV_PATH}", flush=True)


# ── analysis / anti-overfitting enforcement ─────────────────────────────────────

def analyze():
    if not CSV_PATH.exists():
        print("No sweep_progress.csv — run the grid first."); return
    df = pd.read_csv(CSV_PATH)
    n_trials = len(df)                                   # TRUE trial count
    traded = df[df["n_trades"].astype(float) > 0].copy()

    # numeric coercion
    for c in ["sharpe", "net_pf", "gross_pf", "max_dd", "skew", "ekurt", "n_obs",
              "is_pf", "oos_pf", "is_sharpe", "oos_sharpe", "oos_trades",
              "ftmo_pass_rate", "n_trades"]:
        traded[c] = pd.to_numeric(traded[c], errors="coerce")

    sr_trials = traded["sharpe"].fillna(0.0).to_numpy()

    def _dsr(row):
        if not np.isfinite(row["sharpe"]) or row["n_obs"] < 4:
            return np.nan
        prob, _ = deflated_sharpe_ratio(
            sr_best=float(row["sharpe"]), sr_trials=sr_trials, n_obs=int(row["n_obs"]),
            skewness=float(row["skew"]) if np.isfinite(row["skew"]) else 0.0,
            excess_kurtosis=float(row["ekurt"]) if np.isfinite(row["ekurt"]) else 0.0)
        return prob
    traded["dsr"] = traded.apply(_dsr, axis=1)

    # OOS holds: net-profitable in BOTH halves with a non-trivial OOS sample
    traded["oos_holds"] = ((traded["is_pf"] > 1.0) & (traded["oos_pf"] > 1.0)
                           & (traded["oos_trades"] >= MIN_OOS_TRADES)
                           & (traded["oos_sharpe"] > 0))

    DSR_BAR = 0.95     # P(true SR > E[max SR]) — standard survival threshold
    FTMO_BAR = 0.30    # clears if it would pass >=30% of monthly challenges
    traded["dsr_survives"] = traded["dsr"] > DSR_BAR
    traded["ftmo_clears"] = traded["ftmo_pass_rate"] >= FTMO_BAR
    traded["SURVIVOR"] = traded["dsr_survives"] & traded["oos_holds"] & traded["ftmo_clears"]

    lb = traded.sort_values("sharpe", ascending=False).head(15)

    print("\n" + "=" * 118)
    print(f"  SYSTEMATIC SWEEP — anti-overfitting enforcement")
    print(f"  Instrument: XAUUSD spot (only qualifying real-spread asset) | 2018-2025 UTC")
    print(f"  Cost: REAL per-bar spread (round-turn) + $0.07/oz commission + news slippage | 1% risk/trade | NO tuning")
    print(f"  TRUE TRIAL COUNT (DSR haircut N): {n_trials}   |   configs that traded: {len(traded)}")
    print(f"  Survival bars: DSR > {DSR_BAR}  AND  OOS holds (IS&OOS net PF>1, OOS SR>0, OOS trades>={MIN_OOS_TRADES})  AND  FTMO pass >= {FTMO_BAR:.0%}")
    print("=" * 118)
    hdr = (f"  {'#':>2} {'TF':>3} {'family':<9} {'v':>1} {'netPF':>5} {'grPF':>5} "
           f"{'Sharpe':>7} {'DSR':>5} {'maxDD':>6} {'trades':>6} {'FTMO%':>6} {'OOS?':>4}")
    print(hdr)
    print("  " + "-" * 114)
    for rank, (_, r) in enumerate(lb.iterrows(), 1):
        ftmo = r["ftmo_pass_rate"] * 100 if np.isfinite(r["ftmo_pass_rate"]) else float("nan")
        print(f"  {rank:>2} {r['timeframe']:>3} {r['family']:<9} {int(r['variant']):>1} "
              f"{r['net_pf']:>5.2f} {r['gross_pf']:>5.2f} {r['sharpe']:>+7.2f} "
              f"{r['dsr']:>5.2f} {r['max_dd']*100:>5.1f}% {int(r['n_trades']):>6} "
              f"{ftmo:>5.1f}% {'YES' if r['oos_holds'] else 'no':>4}")
    print("=" * 118)

    survivors = traded[traded["SURVIVOR"]]
    print("\n  VERDICT")
    print("  " + "-" * 60)
    if len(survivors) == 0:
        # explain WHY the top config fails
        top = lb.iloc[0]
        print("  NO config survived. Not a single one cleared all three gates.")
        print(f"  Best raw Sharpe: {top['family']} {top['timeframe']} v{int(top['variant'])} "
              f"SR={top['sharpe']:+.2f}, but:")
        print(f"    - DSR = {top['dsr']:.3f} (need > {DSR_BAR}) -> "
              f"{'PASS' if top['dsr']>DSR_BAR else 'FAIL: within the noise of '+str(n_trials)+' trials'}")
        print(f"    - OOS holds = {'YES' if top['oos_holds'] else 'NO'} "
              f"(IS PF {top['is_pf']:.2f} / OOS PF {top['oos_pf']:.2f}, OOS SR {top['oos_sharpe']:+.2f})")
        fp = top['ftmo_pass_rate']*100 if np.isfinite(top['ftmo_pass_rate']) else float('nan')
        print(f"    - FTMO pass = {fp:.1f}% (need >= {FTMO_BAR:.0%})")
        print("  This is a valid, honest NEGATIVE result: the price-only family sweep")
        print("  on XAUUSD produces no edge that survives the multiple-testing haircut,")
        print("  holds out-of-sample, AND clears the FTMO ruleset.")
    else:
        print(f"  {len(survivors)} config(s) SURVIVED all three gates:")
        for _, r in survivors.iterrows():
            print(f"    {r['family']} {r['timeframe']} v{int(r['variant'])}: "
                  f"SR {r['sharpe']:+.2f}, DSR {r['dsr']:.3f}, "
                  f"netPF {r['net_pf']:.2f}, OOS PF {r['oos_pf']:.2f}, "
                  f"FTMO {r['ftmo_pass_rate']*100:.1f}%")

    # summary stats
    print("\n  Sweep summary:")
    print(f"    configs with a positive net Sharpe : {(traded['sharpe']>0).sum()} / {len(traded)}")
    print(f"    configs with net PF > 1            : {(traded['net_pf']>1).sum()} / {len(traded)}")
    print(f"    configs passing look-ahead guard   : {(traded['guard']=='PASS').sum()} / {len(traded)}")
    print(f"    configs where OOS holds            : {traded['oos_holds'].sum()} / {len(traded)}")
    print(f"    configs clearing DSR haircut       : {traded['dsr_survives'].sum()} / {len(traded)}")

    # persist leaderboard
    out = _ROOT / "results" / "leaderboard.csv"
    lb.to_csv(out, index=False)
    print(f"\n  Leaderboard written -> {out}")
    return traded, lb, survivors, n_trials


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--analyze" in sys.argv:
        analyze()
    else:
        run_grid()
        analyze()
