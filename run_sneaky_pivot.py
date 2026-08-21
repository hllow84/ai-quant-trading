#!/usr/bin/env python3
"""
run_sneaky_pivot.py — Strategy 2 of the 2026-08-19 brief: the 15-minute
"Sneaky Pivot", tested cost-inclusively on real Dukascopy M1 with a spread.

GRID (small, a priori, stated — breadth not depth)
--------------------------------------------------
    3 instruments  (NAS100, US30, XAUUSD)
  x 2 targets      (range-opposite, swing-opposite)
  x 2 stops        (sneaky-candle extreme, low/high of day)
  x 2 trigger windows (C3 only = the literal reading, rest-of-session = the spirit)
  = 24 configs THIS BATCH.

Every one of those four axes is a choice the brief itself leaves open; none is a
free parameter fitted to the data. There is no numeric optimisation anywhere in
this script.

COSTS
-----
Indices use the engine's instrument-agnostic bps model, identical to
run_sweep_indices.py so results are comparable: REAL per-bar spread from the data
(round-turn) + 0.35 bps commission + 0.15/0.50 bps per-side slippage. Gold uses
the legacy $/oz model (real spread + $0.07/oz + $0.03/$0.10 per side).

GATES (FTMO is deliberately absent — STATE_OF_PLAY §1 closed that question)
--------------------------------------------------------------------------
  1. gross PF > 1      — is there an edge BEFORE costs at all? This is the test
                         that killed the index-trend lead in §6; it comes first.
  2. net PF > 1 and positive net Sharpe.
  3. DSR > 0.95 against a STATED STRUCTURAL pool — the 24 a priori cells of this
     batch, fixed before any result was seen. That follows recompute_dsr.py's
     convention (structural = headline). The 459-trial project-cumulative pool is
     printed for contrast ONLY: research/dsr.py BUG 2 documents that it is
     contaminated by structurally doomed legacy M5 configs at Sharpe -14, which
     inflate its sigma and push E[max SR] to a bar nothing can clear. A DSR
     against that pool is not a gate, it is an artefact.
  4. OOS holds across the fixed 2023-01-01 split.
  5. Look-ahead guard passes.

WHAT THIS RUN CANNOT SETTLE
---------------------------
2018-2025 only. STATE_OF_PLAY §7 rule 3 requires the out-of-regime re-run BEFORE
any candidate is believed, and the M1 archive in this repo starts 2018-01.
scripts/download_pre2018_m1.mjs is pulling 2013-09-30 -> 2018 M1 for NAS100 and
US30 so that test can be run. Nothing here is a lead until it survives that.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns,
    build_position_series,
)
from strategies.sneaky_pivot import sneaky_pivot, TARGETS, STOPS, TRIGGERS

BARS_PER_YEAR = 252
OOS_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
MIN_OOS_TRADES = 20
DSR_BAR = 0.95

# Cumulative trial count carried by the project before this batch (STATE_OF_PLAY §1).
PRIOR_TRIALS = 435
PRIOR_CSVS = [
    "sweep_progress.csv",                   # 75  gold family sweep
    "htf_breakout.csv",                     # 12  HTF-gated breakout
    "sweep_indices.csv",                    # 150 US index sweep
    "basket_configs.csv",                   # 108 index trend basket 2018-25
    "basket_configs_scored_pre2018.csv",    # 90  pre-2018 out-of-regime
]

COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)

INSTRUMENTS = {
    "NAS100": (_ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv", COST_BPS),
    "US30":   (_ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",   COST_BPS),
    # Gold is a stated robustness instrument, not the strategy's home market: the
    # 09:30-16:00 ET session anchor is native to US equity indices and merely
    # plausible for spot gold. Read its rows as a cross-check, not a headline.
    "XAUUSD": (_ROOT / "data" / "XAUUSD_M1_2018_2025_spot_dukascopy.csv", None),
}

OUT_CSV = _ROOT / "results" / "sneaky_pivot.csv"
SCORED_CSV = _ROOT / "results" / "sneaky_pivot_scored.csv"
TRADES_CSV = _ROOT / "results" / "sneaky_pivot_trades.csv"


def _split_stats(trades: pd.DataFrame) -> tuple:
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


def score(m1: pd.DataFrame, params: dict, daily_index, cost_bps) -> tuple[dict, pd.DataFrame]:
    """Returns (metrics, trade ledger). The ledger is kept so the out-of-regime
    re-run can be compared trade-for-trade rather than metric-for-metric."""
    empty = pd.DataFrame()
    cands = sneaky_pivot(m1, params)
    if not cands:
        return dict(n_cands=0, n_trades=0, guard="N/A"), empty

    trades = de_overlap(simulate_trades(m1, cands, strictly_after=True, cost_bps=cost_bps))
    if trades.empty:
        return dict(n_cands=len(cands), n_trades=0, guard="N/A"), empty

    pos = build_position_series(trades, m1.index)
    try:
        guard_look_ahead(pos, m1["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"

    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    is_n, oos_n, is_pf, oos_pf, is_sr, oos_sr = _split_stats(trades)

    return dict(
        n_cands=len(cands), n_trades=len(trades), guard=guard,
        n_long=int((trades["side"] == "long").sum()),
        n_short=int((trades["side"] == "short").sum()),
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
        rr_med=float((abs(trades["entry_mid"] - trades["exit_mid"]) / trades["risk_price"]).median()),
        n_targets=int((trades["reason"] == "target").sum()),
        n_stops=int((trades["reason"] == "stop").sum()),
        n_time=int((trades["reason"] == "time").sum()),
        n_obs=int(len(daily_ret)),
        is_trades=is_n, oos_trades=oos_n,
        is_pf=is_pf, oos_pf=oos_pf, is_sharpe=is_sr, oos_sharpe=oos_sr,
    ), trades


def buy_and_hold(daily: pd.DataFrame) -> dict:
    """Daily buy-and-hold on the same file, mid prices, spread crossed once."""
    px = daily["mid_close"]
    ret = px.pct_change().dropna()
    entry_cost = float(daily["spread_close"].iloc[0] / px.iloc[0])
    eq = (1 + ret).cumprod() * (1 - entry_cost)
    return dict(sharpe=sharpe(ret, BARS_PER_YEAR), max_dd=max_drawdown(eq))


def main():
    rows, bh, ledger = [], {}, []
    for inst, (path, cost_bps) in INSTRUMENTS.items():
        if not path.exists():
            print(f"[{inst}] MISSING {path.name} — skipped.", flush=True)
            continue
        print(f"[{inst}] loading M1 ...", flush=True)
        spot = load_m1_spot(path)                 # loaded ONCE; 300 MB files
        daily = aggregate_daily(spot)
        daily_index = daily.index
        bh[inst] = buy_and_hold(daily)
        m1 = pd.DataFrame(index=spot.index)
        for c in ("open", "high", "low", "close"):
            m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
        m1["spread"] = spot["spread"]
        m1["volume"] = spot["volume"]
        del spot
        print(f"[{inst}] {len(m1):,} M1 bars {m1.index[0].date()} -> {m1.index[-1].date()} "
              f"| median spread {m1['spread'].median():.3f} "
              f"({m1['spread'].median() / m1['mid_close'].median() * 1e4:.2f} bps) "
              f"| B&H SR {bh[inst]['sharpe']:+.2f}", flush=True)

        for target in TARGETS:
            for stop in STOPS:
                for trigger in TRIGGERS:
                    p = dict(target=target, stop=stop, trigger=trigger)
                    res, tr = score(m1, p, daily_index, cost_bps)
                    rows.append(dict(instrument=inst, **p, **res))
                    if not tr.empty:
                        ledger.append(tr.assign(instrument=inst, **p))
                    print(f"  {inst:>6} tgt={target:<5} stop={stop:<6} trig={trigger:<7} "
                          f"cands={res.get('n_cands', 0):>4} n={res.get('n_trades', 0):>4} "
                          f"grPF={res.get('gross_pf', float('nan')):.3f} "
                          f"netPF={res.get('net_pf', float('nan')):.3f} "
                          f"SR={res.get('sharpe', float('nan')):+.2f} "
                          f"guard={res.get('guard', '?')[:4]}", flush=True)

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    trades_all = pd.concat(ledger, ignore_index=True) if ledger else pd.DataFrame()
    if not trades_all.empty:
        trades_all.to_csv(TRADES_CSV, index=False)
    analyze(df, bh, trades_all)


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


def per_year(trades_all: pd.DataFrame, traded: pd.DataFrame):
    """
    Year-by-year net R for the best config per instrument. The last lead in this
    project died because a strong 2018-2025 number was a regime artefact, so a
    single blended Sharpe is never enough — the yearly spread has to be visible
    before the out-of-regime re-run confirms or kills it.
    """
    if trades_all.empty:
        return
    print("\n  YEAR-BY-YEAR net R for the best config per instrument (regime concentration check)")
    key = ["instrument", "target", "stop", "trigger"]
    years = sorted(pd.to_datetime(trades_all["exit_time"], utc=True).dt.year.unique())
    print("  " + " " * 34 + "".join(f"{y:>8}" for y in years))
    print("  " + "-" * (34 + 8 * len(years)))
    for inst in traded["instrument"].unique():
        sub = traded[traded["instrument"] == inst].sort_values("sharpe", ascending=False)
        if sub.empty:
            continue
        b = sub.iloc[0]
        m = np.ones(len(trades_all), dtype=bool)
        for k in key:
            m &= (trades_all[k] == b[k]).to_numpy()
        t = trades_all[m]
        yr = pd.to_datetime(t["exit_time"], utc=True).dt.year
        agg = t.groupby(yr)["net_R"].sum()
        cnt = t.groupby(yr)["net_R"].size()
        label = f"{inst} {b['target']}/{b['stop']}/{b['trigger']}"
        print(f"  {label:<34}" + "".join(f"{agg.get(y, 0.0):>+8.1f}" for y in years))
        print(f"  {'  (trades)':<34}" + "".join(f"{cnt.get(y, 0):>8}" for y in years))
    print("  Read: net R summed per calendar year. A single dominant year is the "
          "signature that killed the last lead.")


def analyze(df: pd.DataFrame, bh: dict, trades_all: pd.DataFrame | None = None):
    traded = df[df.get("n_trades", pd.Series(dtype=int)).fillna(0) > 0].copy()
    n_batch = len(df)
    cumulative = PRIOR_TRIALS + n_batch

    prior, prior_note = _prior_sharpes()
    sr_batch = traded["sharpe"].fillna(0.0).to_numpy()
    pool_project = np.concatenate([prior, sr_batch]) if prior.size else sr_batch

    def _dsr(r, pool):
        if not np.isfinite(r["sharpe"]) or r["n_obs"] < 4:
            return np.nan
        return deflated_sharpe(
            sr_best=float(r["sharpe"]), sr_trials=pool, n_obs=int(r["n_obs"]),
            skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
            excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0,
        )["dsr"]

    # HEADLINE = structural pool (this batch's a priori cells). CONTRAST = the
    # project-cumulative pool, which dsr.py BUG 2 shows is sigma-contaminated.
    traded["dsr"] = traded.apply(lambda r: _dsr(r, sr_batch), axis=1)
    traded["dsr_cumulative_pool"] = traded.apply(lambda r: _dsr(r, pool_project), axis=1)
    e_struct = expected_max_sharpe(sr_batch)
    e_cumul = expected_max_sharpe(pool_project)
    traded["oos_holds"] = ((traded["is_pf"] > 1.0) & (traded["oos_pf"] > 1.0)
                           & (traded["oos_trades"] >= MIN_OOS_TRADES)
                           & (traded["oos_sharpe"] > 0))
    traded["gross_edge"] = traded["gross_pf"] > 1.0
    traded["SURVIVOR"] = (traded["gross_edge"] & (traded["net_pf"] > 1.0)
                          & (traded["dsr"] > DSR_BAR) & traded["oos_holds"]
                          & (traded["guard"] == "PASS"))

    W = 122
    print("\n" + "=" * W)
    print("  STRATEGY 2 — 15-MINUTE SNEAKY PIVOT | real Dukascopy M1 with spread, 2018-2025, RTH 09:30-16:00 ET")
    print(f"  Cost: REAL per-bar spread + {COST_BPS['commission']} bps commission (round-turn) + "
          f"{COST_BPS['slip_normal']}/{COST_BPS['slip_news']} bps per-side slippage (indices); "
          f"$0.07/oz + $0.03/$0.10 per side (gold) | 1% risk/trade | NO tuning")
    print(f"  Configs THIS BATCH: {n_batch}  |  CUMULATIVE PROJECT TRIALS (DSR N): "
          f"{PRIOR_TRIALS} prior + {n_batch} = {cumulative}")
    print(f"  DSR pool (HEADLINE)  = STRUCTURAL: this batch's {len(sr_batch)} a priori cells "
          f"-> E[max SR] {e_struct[0]:+.3f} (mu {e_struct[2]:+.3f}, sd {e_struct[3]:.3f})")
    print(f"  DSR pool (CONTRAST)  = project-cumulative {len(pool_project)} "
          f"[{prior_note}] -> E[max SR] {e_cumul[0]:+.3f} (mu {e_cumul[2]:+.3f}, sd {e_cumul[3]:.3f})")
    print("                         ^ NOT a gate: sigma-contaminated by legacy structurally-doomed")
    print("                           configs (research/dsr.py BUG 2). Shown so the difference is visible.")
    print(f"  Gates: gross PF > 1 AND net PF > 1 AND DSR > {DSR_BAR} AND OOS holds "
          f"(IS&OOS netPF>1, OOS SR>0, OOS trades>={MIN_OOS_TRADES}) AND look-ahead guard PASS")
    print("=" * W)

    if traded.empty:
        print("  NO config produced a single trade. Check the setup filter before reading anything into this.")
        return

    print(f"  {'inst':>6} {'target':>6} {'stop':>6} {'trig':>7} {'cands':>5} {'trades':>6} "
          f"{'grPF':>6} {'netPF':>6} {'Sharpe':>7} {'DSR':>5} {'maxDD':>6} {'win%':>5} "
          f"{'OOS?':>4} {'guard':>5}")
    print("  " + "-" * (W - 4))
    for _, r in traded.sort_values("sharpe", ascending=False).iterrows():
        print(f"  {r['instrument']:>6} {r['target']:>6} {r['stop']:>6} {r['trigger']:>7} "
              f"{int(r['n_cands']):>5} {int(r['n_trades']):>6} "
              f"{r['gross_pf']:>6.3f} {r['net_pf']:>6.3f} {r['sharpe']:>+7.2f} "
              f"{r['dsr']:>5.2f} {r['max_dd'] * 100:>5.1f}% {r['win_rate'] * 100:>4.1f}% "
              f"{'YES' if r['oos_holds'] else 'no':>4} {r['guard'][:5]:>5}")
    print("=" * W)

    print("\n  GROSS vs NET R — is there an edge BEFORE costs? (the test that killed the last lead)")
    print(f"  {'inst':>6} {'target':>6} {'stop':>6} {'trig':>7} {'grossR/trd':>11} {'costR/trd':>10} "
          f"{'netR/trd':>9} {'cost as %R':>11} {'tgt/stop/time':>14}")
    print("  " + "-" * 84)
    for _, r in traded.sort_values(["instrument", "target", "stop", "trigger"]).iterrows():
        mix = f"{int(r['n_targets'])}/{int(r['n_stops'])}/{int(r['n_time'])}"
        print(f"  {r['instrument']:>6} {r['target']:>6} {r['stop']:>6} {r['trigger']:>7} "
              f"{r['gross_R_mean']:>+11.4f} {r['cost_R_mean']:>10.4f} {r['net_R_mean']:>+9.4f} "
              f"{r['cost_R_mean'] * 100:>10.1f}% {mix:>14}")

    survivors = traded[traded["SURVIVOR"]]
    best = traded.sort_values("sharpe", ascending=False).iloc[0]

    print("\n  VERDICT")
    print("  " + "-" * 78)
    if len(survivors):
        print(f"  {len(survivors)} config(s) cleared every gate:")
        for _, r in survivors.iterrows():
            print(f"    {r['instrument']} tgt={r['target']} stop={r['stop']} trig={r['trigger']}: "
                  f"SR {r['sharpe']:+.2f}, DSR {r['dsr']:.3f}, grossPF {r['gross_pf']:.3f}, "
                  f"netPF {r['net_pf']:.3f}, IS PF {r['is_pf']:.2f} / OOS PF {r['oos_pf']:.2f}")
        print("\n  NOT A LEAD YET — STATE_OF_PLAY §7 rule 3: the 2013-2017 out-of-regime re-run")
        print("  must be passed before any of this is believed.")
    else:
        print("  NO config cleared all gates.")
        print(f"  Best raw net Sharpe: {best['instrument']} tgt={best['target']} "
              f"stop={best['stop']} trig={best['trigger']} -> SR {best['sharpe']:+.2f}")
        print(f"    - gross PF {best['gross_pf']:.3f} -> "
              f"{'edge exists before costs' if best['gross_pf'] > 1 else 'NO edge even before costs'}")
        print(f"    - net PF   {best['net_pf']:.3f}")
        print(f"    - DSR {best['dsr']:.3f} (need > {DSR_BAR}) -> "
              f"{'PASS' if best['dsr'] > DSR_BAR else f'FAIL: inside the noise of {cumulative} cumulative trials'}")
        print(f"    - OOS holds: {'YES' if best['oos_holds'] else 'NO'} "
              f"(IS PF {best['is_pf']:.2f} / OOS PF {best['oos_pf']:.2f}, "
              f"OOS SR {best['oos_sharpe']:+.2f}, OOS trades {int(best['oos_trades'])})")

    print("\n  vs BUY-AND-HOLD (same file, same window):")
    for inst, b in bh.items():
        sub = traded[traded["instrument"] == inst]
        if sub.empty:
            continue
        s = sub.sort_values("sharpe", ascending=False).iloc[0]
        print(f"    {inst:>6}: best strategy SR {s['sharpe']:+.2f} (maxDD {s['max_dd'] * 100:.1f}%) "
              f"vs B&H SR {b['sharpe']:+.2f} (maxDD {b['max_dd'] * 100:.1f}%) -> "
              f"{'BEATS' if s['sharpe'] > b['sharpe'] else 'LOSES TO'} B&H")

    if trades_all is not None:
        per_year(trades_all, traded)

    print("\n  Batch summary:")
    print(f"    gross PF > 1        : {(traded['gross_pf'] > 1).sum()} / {len(traded)}")
    print(f"    net PF > 1          : {(traded['net_pf'] > 1).sum()} / {len(traded)}")
    print(f"    positive net Sharpe : {(traded['sharpe'] > 0).sum()} / {len(traded)}")
    print(f"    OOS holds           : {traded['oos_holds'].sum()} / {len(traded)}")
    print(f"    clears DSR haircut  : {(traded['dsr'] > DSR_BAR).sum()} / {len(traded)} "
          f"(structural pool; contaminated cumulative pool: {(traded['dsr_cumulative_pool'] > DSR_BAR).sum()})")
    print(f"    look-ahead guard    : {(traded['guard'] == 'PASS').sum()} / {len(traded)} PASS")
    print(f"\n  Results -> {OUT_CSV}\n  Scored  -> {SCORED_CSV}")

    traded.to_csv(SCORED_CSV, index=False)


def analyze_only():
    """Re-score from the saved CSVs without re-running the 300 MB backtest."""
    df = pd.read_csv(OUT_CSV)
    trades_all = pd.read_csv(TRADES_CSV) if TRADES_CSV.exists() else pd.DataFrame()
    bh = {}
    for inst, (path, _) in INSTRUMENTS.items():
        if path.exists():
            bh[inst] = buy_and_hold(aggregate_daily(load_m1_spot(path)))
    analyze(df, bh, trades_all)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--analyze" in sys.argv:
        analyze_only()
    else:
        main()
