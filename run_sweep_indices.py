#!/usr/bin/env python3
"""
run_sweep_indices.py — The 5-family sweep re-run on US index CFDs.

THESIS UNDER TEST
-----------------
Every gold strategy died because the stop distance was small relative to costs
(cost_R was 20-60% of risk). Indices move far more relative to their spread, so
cost_R should be much lower. If the "no edge" result was a gold-COST artifact,
the same families should look materially better here. If the families are still
flat once costs are cheap, the earlier kills were about SIGNAL, not cost.

GRID (stated, small, no tuning)
-------------------------------
    2 instruments (NAS100, US30)
  x 5 timeframes  (M5, M15, M30, H1, H4)
  x 5 families    (trend, breakout, meanrev, momentum, macross)
  x 3 stated variants each
  = 150 configs THIS BATCH.

Cumulative trial count = 87 prior (75 sweep + 12 HTF breakout) + 150 = 237.
DSR is deflated against the CUMULATIVE Sharpe universe, not this batch alone.

COST MODEL (index-appropriate, stated, deliberately conservative)
-----------------------------------------------------------------
Uses the engine's instrument-agnostic bps-of-price model:
  spread     : REAL per-bar bid/ask spread from the data (round-turn). Not assumed.
  commission : 0.35 bps of notional, round-turn. This MATCHES THE RELATIVE
               COMMISSION BURDEN OF GOLD ($0.07/oz on ~$2,000 = 0.35 bps) and is
               deliberately conservative: FTMO and most raw-spread CFD brokers
               charge ZERO commission on index CFDs (cost sits in the spread).
               At NAS100 ~15,000 this is ~0.53 index points round-turn;
               at US30 ~33,000 it is ~1.16 points.
  slippage   : 0.15 bps per side normal, 0.50 bps per side in news windows —
               again the same RELATIVE burden as gold ($0.03 / $0.10 per side).
  news windows: the engine default (07:00-08:00 and 12:30-14:30 UTC). 12:30-14:30
               covers US data (13:30) and the cash open (14:30), which is the
               relevant window for US indices. 07:00-08:00 is retained unchanged
               rather than re-tuned per instrument — it only ever widens cost,
               so keeping it is the conservative choice and adds no free parameter.

Everything else is identical to run_sweep.py: same families, same variants, same
strictly_after=True resolution (no look-ahead by construction), look-ahead guard
on every config, 1% risk/trade, daily-aggregated Sharpe (252/yr), FTMO Phase-1
rolling monthly challenge starts, fixed 2023-01-01 IS/OOS cut.

Resumable: finished configs append to results/sweep_indices.csv with per-config
markers in results/markers_idx/.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import (
    load_m1_spot, load_m1_mid, resample_mid, aggregate_daily,
)
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor, deflated_sharpe_ratio
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns,
    build_position_series,
)
from research.ftmo_rules import rolling_pass_rate
from strategies.sweep_families import FAMILIES, TIMEFRAMES, TF_DELTA

BARS_PER_YEAR = 252
OOS_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
MIN_OOS_TRADES = 20
DSR_BAR = 0.95
FTMO_BAR = 0.30

# 75-config family sweep + 12-config HTF-gated breakout batch, both on XAUUSD.
PRIOR_TRIALS = 87
PRIOR_CSVS = ["sweep_progress.csv", "htf_breakout.csv"]

# Index-appropriate cost model — see module docstring for the justification.
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)

INSTRUMENTS = {
    "NAS100": _ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv",
    "US30":   _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",
}

CSV_PATH = _ROOT / "results" / "sweep_indices.csv"
MARKER_DIR = _ROOT / "results" / "markers_idx"

CSV_FIELDS = [
    "instrument", "timeframe", "family", "variant", "params",
    "n_trades", "guard", "gross_pf", "net_pf", "sharpe", "skew", "ekurt",
    "max_dd", "gross_R_mean", "cost_R_mean", "net_R_mean", "risk_med", "win_rate",
    "n_targets", "n_stops", "n_time", "n_obs",
    "is_trades", "oos_trades", "is_pf", "oos_pf", "is_sharpe", "oos_sharpe",
    "ftmo_pass_rate", "ftmo_n_challenges",
]


def _coerce_utc(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tz is None else t.tz_convert("UTC")


def _load_done_keys() -> set:
    if not CSV_PATH.exists():
        return set()
    with CSV_PATH.open(newline="") as f:
        return {(r["instrument"], r["timeframe"], r["family"], r["variant"])
                for r in csv.DictReader(f)}


def _append_row(row: dict) -> None:
    new = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
        f.flush()


def _split_metrics(trades: pd.DataFrame):
    exit_t = pd.to_datetime(trades["exit_time"], utc=True)
    is_m = exit_t < OOS_SPLIT
    oos_m = ~is_m

    def _pf(mask):
        return profit_factor(trades.loc[mask, "net_R"]) if mask.any() else float("nan")

    def _sr(mask):
        sub = trades.loc[mask]
        if sub.empty:
            return float("nan")
        d = sub.groupby(pd.to_datetime(sub["exit_time"], utc=True).dt.normalize())["ret_frac"].sum()
        return sharpe(d, BARS_PER_YEAR) if len(d) > 1 else float("nan")

    return (int(is_m.sum()), int(oos_m.sum()),
            _pf(is_m), _pf(oos_m), _sr(is_m), _sr(oos_m))


def score_config(m, family_fn, params, tf_key, daily_index, d0, d1) -> dict:
    cands = family_fn(m, params, TF_DELTA[tf_key])
    for tr in cands:
        tr["session_end"] = _coerce_utc(tr["session_end"])
        tr["entry_time"] = _coerce_utc(tr["entry_time"])

    trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=COST_BPS))
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
    is_n, oos_n, is_pf, oos_pf, is_sr, oos_sr = _split_metrics(trades)
    ftmo = rolling_pass_rate(trades, d0, d1, phase=1, max_days=60)

    return dict(
        n_trades=len(trades), guard=guard,
        gross_pf=profit_factor(trades["gross_R"]),
        net_pf=profit_factor(trades["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR),
        skew=float(daily_ret.skew()), ekurt=float(daily_ret.kurtosis()),
        max_dd=max_drawdown(equity),
        gross_R_mean=float(trades["gross_R"].mean()),
        cost_R_mean=float(trades["cost_R"].mean()),
        net_R_mean=float(trades["net_R"].mean()),
        risk_med=float(trades["risk_price"].median()),
        win_rate=float((trades["net_R"] > 0).mean()),
        n_targets=int((trades["reason"] == "target").sum()),
        n_stops=int((trades["reason"] == "stop").sum()),
        n_time=int((trades["reason"] == "time").sum()),
        n_obs=int(len(daily_ret)),
        is_trades=is_n, oos_trades=oos_n,
        is_pf=is_pf, oos_pf=oos_pf, is_sharpe=is_sr, oos_sharpe=oos_sr,
        ftmo_pass_rate=ftmo["pass_rate"], ftmo_n_challenges=ftmo["n_challenges"],
    )


def buy_and_hold(path: Path) -> dict:
    """Daily buy-and-hold benchmark on the same file, mid prices, spread crossed once."""
    daily = aggregate_daily(load_m1_spot(path))
    px = daily["mid_close"]
    ret = px.pct_change().dropna()
    entry_cost = float(daily["spread_close"].iloc[0] / px.iloc[0])
    eq = (1 + ret).cumprod() * (1 - entry_cost)
    yrs = (px.index[-1] - px.index[0]).days / 365.25
    return dict(sharpe=sharpe(ret, BARS_PER_YEAR),
                max_dd=max_drawdown(eq),
                cagr=float(eq.iloc[-1] ** (1 / yrs) - 1),
                n_days=len(ret))


def run_grid():
    MARKER_DIR.mkdir(parents=True, exist_ok=True)
    done = _load_done_keys()
    per_inst = len(TIMEFRAMES) * sum(len(v[1]) for v in FAMILIES.values())
    total = per_inst * len(INSTRUMENTS)
    print(f"Grid: {len(INSTRUMENTS)} instruments x {len(TIMEFRAMES)} TF x "
          f"{len(FAMILIES)} families x 3 variants = {total} configs. "
          f"Already done: {len(done)}.", flush=True)

    done_ct = len(done)
    for inst, path in INSTRUMENTS.items():
        if not path.exists():
            print(f"[{inst}] DATA MISSING at {path} — skipping instrument.", flush=True)
            continue
        print(f"\n[{inst}] loading M1 mid ...", flush=True)
        m1 = load_m1_mid(path)
        daily_index = aggregate_daily(load_m1_spot(path)).index
        d0, d1 = daily_index[0], daily_index[-1]
        med_px = float(m1["mid_close"].median())
        med_sp = float(m1["spread"].median())
        print(f"[{inst}] M1 bars {len(m1):,} | {m1.index[0].date()} -> {m1.index[-1].date()} "
              f"| median px {med_px:,.1f} | median spread {med_sp:.3f} pts "
              f"({1e4*med_sp/med_px:.2f} bps)", flush=True)

        for tf_key, tf_freq in TIMEFRAMES.items():
            tf_keys = [(inst, tf_key, fam, str(i))
                       for fam, (_, variants) in FAMILIES.items()
                       for i in range(len(variants))]
            if all(k in done for k in tf_keys):
                print(f"[{inst}/{tf_key}] all done — skip.", flush=True)
                continue
            m = resample_mid(m1, tf_freq)
            print(f"[{inst}/{tf_key}] {len(m):,} bars.", flush=True)

            for fam, (fn, variants) in FAMILIES.items():
                for i, params in enumerate(variants):
                    key = (inst, tf_key, fam, str(i))
                    if key in done:
                        continue
                    res = score_config(m, fn, params, tf_key, daily_index, d0, d1)
                    row = dict(instrument=inst, timeframe=tf_key, family=fam,
                               variant=str(i), params=str(params))
                    for fld in CSV_FIELDS:
                        row.setdefault(fld, res.get(fld, ""))
                    _append_row(row)
                    (MARKER_DIR / f"{inst}_{tf_key}_{fam}_{i}.done").write_text("ok")
                    done_ct += 1
                    sr = res.get("sharpe", float("nan"))
                    cr = res.get("cost_R_mean", float("nan"))
                    print(f"  [{done_ct}/{total}] {inst:>6} {tf_key:>3} {fam:<9} v{i} "
                          f"n={res.get('n_trades',0):>5} "
                          f"netPF={res.get('net_pf',float('nan')):.2f} "
                          f"SR={sr:+.2f} costR={cr*100:.1f}% "
                          f"guard={res.get('guard','?')[:4]}", flush=True)

    print(f"\nGrid complete: {done_ct}/{total} in {CSV_PATH}", flush=True)


def _prior_sharpes() -> tuple[np.ndarray, str]:
    vals, notes = [], []
    for name in PRIOR_CSVS:
        p = _ROOT / "results" / name
        if p.exists():
            s = pd.to_numeric(pd.read_csv(p)["sharpe"], errors="coerce").dropna().to_numpy()
            vals.append(s)
            notes.append(f"{name}:{len(s)}")
        else:
            notes.append(f"{name}:MISSING")
    arr = np.concatenate(vals) if vals else np.array([])
    return arr, ", ".join(notes)


def analyze():
    if not CSV_PATH.exists():
        print("No sweep_indices.csv — run the grid first.")
        return
    df = pd.read_csv(CSV_PATH)
    n_batch = len(df)
    cumulative = PRIOR_TRIALS + n_batch

    traded = df[pd.to_numeric(df["n_trades"], errors="coerce").fillna(0) > 0].copy()
    for c in ["sharpe", "net_pf", "gross_pf", "max_dd", "skew", "ekurt", "n_obs",
              "is_pf", "oos_pf", "is_sharpe", "oos_sharpe", "oos_trades",
              "ftmo_pass_rate", "n_trades", "cost_R_mean", "gross_R_mean",
              "net_R_mean", "risk_med", "win_rate"]:
        traded[c] = pd.to_numeric(traded[c], errors="coerce")

    prior_sr, prior_note = _prior_sharpes()
    sr_all = np.concatenate([prior_sr, traded["sharpe"].fillna(0.0).to_numpy()])

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

    W = 128
    print("\n" + "=" * W)
    print("  US INDEX CFD SWEEP (NAS100 + US30) — real Dukascopy spread, 2018-2025 UTC")
    print(f"  Cost: REAL per-bar spread + {COST_BPS['commission']} bps commission (round-turn) + "
          f"{COST_BPS['slip_normal']}/{COST_BPS['slip_news']} bps per-side slippage | 1% risk/trade | NO tuning")
    print(f"  Configs THIS BATCH: {n_batch}  |  CUMULATIVE TRIAL COUNT (DSR N): "
          f"{PRIOR_TRIALS} prior + {n_batch} = {cumulative}")
    print(f"  DSR trial universe: prior [{prior_note}] + {len(traded)} traded here = {len(sr_all)} Sharpes")
    print(f"  Gates: DSR > {DSR_BAR} AND OOS holds (IS&OOS netPF>1, OOS SR>0, OOS trades>={MIN_OOS_TRADES}) AND FTMO P1 >= {FTMO_BAR:.0%}")
    print("=" * W)

    lb = traded.sort_values("sharpe", ascending=False).head(15)
    print(f"  TOP 15 BY NET SHARPE")
    print(f"  {'#':>2} {'inst':>6} {'TF':>3} {'family':<9} {'v':>1} {'grPF':>5} {'netPF':>5} "
          f"{'Sharpe':>7} {'DSR':>5} {'maxDD':>6} {'trades':>6} {'costR%':>7} {'FTMO%':>6} {'OOS?':>4} {'guard':>5}")
    print("  " + "-" * (W - 4))
    for rank, (_, r) in enumerate(lb.iterrows(), 1):
        ftmo = r["ftmo_pass_rate"] * 100 if np.isfinite(r["ftmo_pass_rate"]) else float("nan")
        print(f"  {rank:>2} {r['instrument']:>6} {r['timeframe']:>3} {r['family']:<9} {int(r['variant']):>1} "
              f"{r['gross_pf']:>5.2f} {r['net_pf']:>5.2f} {r['sharpe']:>+7.2f} {r['dsr']:>5.2f} "
              f"{r['max_dd']*100:>5.1f}% {int(r['n_trades']):>6} {r['cost_R_mean']*100:>6.1f}% "
              f"{ftmo:>5.1f}% {'YES' if r['oos_holds'] else 'no':>4} {str(r['guard'])[:5]:>5}")
    print("=" * W)

    # ── the core thesis test: cost_R by instrument x timeframe ──
    print("\n  COST-TO-RISK BY TIMEFRAME (the thesis test) — cost_R as % of 1R")
    print(f"  {'inst':>6} {'TF':>3} {'medR (pts)':>11} {'costR%':>8} {'grossR/trd':>11} {'netR/trd':>10} {'grPF':>5} {'netPF':>6}")
    print("  " + "-" * 70)
    piv = (traded.groupby(["instrument", "timeframe"])
           .agg(risk_med=("risk_med", "median"), cost_R=("cost_R_mean", "mean"),
                gR=("gross_R_mean", "mean"), nR=("net_R_mean", "mean"),
                gpf=("gross_pf", "mean"), npf=("net_pf", "mean")).reset_index())
    order = {k: i for i, k in enumerate(TIMEFRAMES)}
    piv = piv.sort_values(["instrument", "timeframe"], key=lambda s: s.map(order) if s.name == "timeframe" else s)
    for _, r in piv.iterrows():
        print(f"  {r['instrument']:>6} {r['timeframe']:>3} {r['risk_med']:>11.1f} "
              f"{r['cost_R']*100:>7.1f}% {r['gR']:>+11.4f} {r['nR']:>+10.4f} "
              f"{r['gpf']:>5.2f} {r['npf']:>6.2f}")

    print("\n  GOLD COMPARISON (prior sweeps, same families & cost method):")
    print("    XAUUSD M5  cost_R ~60%   |  M15 ~32%  |  M30 ~21%  |  H4 ~4-6%")

    survivors = traded[traded["SURVIVOR"]]
    print("\n  VERDICT")
    print("  " + "-" * 74)
    if len(survivors):
        print(f"  {len(survivors)} config(s) SURVIVED all three gates:")
        for _, r in survivors.iterrows():
            print(f"    {r['instrument']} {r['timeframe']} {r['family']} v{int(r['variant'])}: "
                  f"SR {r['sharpe']:+.2f}, DSR {r['dsr']:.3f}, netPF {r['net_pf']:.2f}, "
                  f"IS PF {r['is_pf']:.2f} / OOS PF {r['oos_pf']:.2f}, FTMO {r['ftmo_pass_rate']*100:.1f}%")
    else:
        top = lb.iloc[0]
        print("  NO config survived. Zero cleared DSR + OOS + FTMO.")
        print(f"  Best raw net Sharpe: {top['instrument']} {top['timeframe']} {top['family']} "
              f"v{int(top['variant'])} -> SR {top['sharpe']:+.2f}, netPF {top['net_pf']:.2f}")
        print(f"    - DSR {top['dsr']:.3f} (need > {DSR_BAR}) -> "
              f"{'PASS' if top['dsr'] > DSR_BAR else f'FAIL: inside the noise of {cumulative} cumulative trials'}")
        print(f"    - OOS holds: {'YES' if top['oos_holds'] else 'NO'} "
              f"(IS PF {top['is_pf']:.2f} / OOS PF {top['oos_pf']:.2f}, OOS SR {top['oos_sharpe']:+.2f}, "
              f"OOS trades {int(top['oos_trades'])})")
        fp = top['ftmo_pass_rate'] * 100 if np.isfinite(top['ftmo_pass_rate']) else float('nan')
        print(f"    - FTMO P1 pass {fp:.1f}% (need >= {FTMO_BAR:.0%})")

    print("\n  vs BUY-AND-HOLD THE INDEX (same period, spread crossed once):")
    for inst, path in INSTRUMENTS.items():
        if not path.exists():
            continue
        bh = buy_and_hold(path)
        sub = traded[traded["instrument"] == inst]
        if sub.empty:
            continue
        b = sub.sort_values("sharpe", ascending=False).iloc[0]
        print(f"    {inst}: B&H Sharpe {bh['sharpe']:+.2f}, MDD {bh['max_dd']*100:.1f}%, "
              f"CAGR {bh['cagr']*100:.1f}%  |  best strategy SR {b['sharpe']:+.2f} -> "
              f"{'BEATS' if b['sharpe'] > bh['sharpe'] else 'LOSES TO'} B&H "
              f"(gap {b['sharpe'] - bh['sharpe']:+.2f})")

    print("\n  Batch summary:")
    print(f"    positive net Sharpe : {(traded['sharpe'] > 0).sum()} / {len(traded)}")
    print(f"    net PF > 1          : {(traded['net_pf'] > 1).sum()} / {len(traded)}")
    print(f"    gross PF > 1        : {(traded['gross_pf'] > 1).sum()} / {len(traded)}")
    print(f"    look-ahead guard    : {(traded['guard'] == 'PASS').sum()} / {len(traded)} PASS")
    print(f"    OOS holds           : {traded['oos_holds'].sum()} / {len(traded)}")
    print(f"    clears DSR haircut  : {traded['dsr_survives'].sum()} / {len(traded)}")

    out = _ROOT / "results" / "leaderboard_indices.csv"
    lb.to_csv(out, index=False)
    traded.to_csv(_ROOT / "results" / "sweep_indices_scored.csv", index=False)
    print(f"\n  Leaderboard -> {out}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--analyze" in sys.argv:
        analyze()
    else:
        run_grid()
        analyze()
