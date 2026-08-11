#!/usr/bin/env python3
"""
run_basket_pre2018.py — OUT-OF-REGIME TEST of the diversified index-trend lead.

WHAT THIS IS
------------
STATE_OF_PLAY §5 step 3: re-run the macross basket UNCHANGED on pre-2018 data to
see whether the 2018-2025 edge is a favourable-regime artifact. The strategy code,
families, variants, cost model and engine are byte-identical to run_basket_trend.py
(imported from the same modules). Only four things differ, and none is a strategy
parameter:

  1. INSTRUMENT SET — 5 indices, NOT 6. GER40 (deuidxeur) has NO Dukascopy ask/
     spread data before 2015, so a real-spread basket cannot include it pre-2018.
     To keep the old-vs-new comparison a pure REGIME test (not "6 vs 5 members"),
     BOTH windows are run on the same 5 indices here.
  2. DATA FILE SUFFIX — 2013_2017 (this test) vs 2018_2025 (matched baseline),
     via --suffix.
  3. OOS SPLIT — moved into the window via --split. On a 2014-2017 sample the
     original 2023-01-01 split is degenerate (all-IS). 2016-01-01 splits it
     ~50/50. This is an EVALUATION cut, not a re-tune: the macross parameters
     (fast=20, slow=50, ema_trend=200, k_atr=2.0, R=2.0, H=96, etc.) are untouched.
  4. DSR POOL — the deflation pool is this run's OWN configs (structural: the
     trend+macross swing cells actually searched), stated explicitly, so the two
     windows are scored by identical construction. No cross-period pool mixing.

WINDOW AVAILABILITY (empirically probed, not assumed)
-----------------------------------------------------
Dukascopy index CFDs do not reach 2008 or 2011. Earliest real data: US30/GER40
2013-09-30, the rest 2012-06. Full-coverage common window for the 5 usable indices
is 2014-2017 (warmup from 2013-10). So this tests 2014's oil-crash onset, 2015's
China Black Monday / oil crash, and 2016's Brexit — a genuinely trend-hostile,
choppy regime — but it CANNOT test 2008 or 2011. Stated loudly in the report.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

from research.gold_data import load_m1_spot, load_m1_mid, resample_mid, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe, structural_pool
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns,
    build_position_series,
)
from research.ftmo_rules import rolling_pass_rate
from strategies.sweep_families import FAMILIES

ANN = 252
MIN_OOS_TRADES = 20
DSR_BAR = 0.95
FTMO_BAR = 0.30

COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)

# GER40 dropped: no Dukascopy ask/spread before 2015. Same 5 names on BOTH windows.
INSTRUMENTS = ["NAS100", "US30", "SPX500", "UK100", "JP225"]
TFS = {"H4": "4h", "H8": "8h", "D1": "1D"}
TF_DELTA = {"H4": pd.Timedelta(hours=4), "H8": pd.Timedelta(hours=8),
            "D1": pd.Timedelta(days=1)}
FAMS = ["trend", "macross"]

RESULTS = _ROOT / "results"


def make_path_for(suffix: str):
    def path_for(name: str) -> Path:
        return _ROOT / "data" / f"{name}_H1_{suffix}_cfd_dukascopy.csv"
    return path_for


def _pf_parts(r: pd.Series) -> tuple[float, float]:
    return float(r[r > 0].sum()), float(abs(r[r < 0].sum()))


def score(base, m, fam_fn, params, tf, daily_index, d0, d1, oos_split):
    cands = fam_fn(m, params, TF_DELTA[tf])
    for tr in cands:
        tr["session_end"] = pd.Timestamp(tr["session_end"]).tz_convert("UTC")
        tr["entry_time"] = pd.Timestamp(tr["entry_time"]).tz_convert("UTC")

    trades = de_overlap(simulate_trades(base, cands, strictly_after=False,
                                        cost_bps=COST_BPS))
    if trades.empty or len(trades) < 5:
        return None, None

    pos = build_position_series(trades, base.index)
    try:
        guard_look_ahead(pos, base["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:30]}"

    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)

    exit_t = pd.to_datetime(trades["exit_time"], utc=True)
    is_m, oos_m = exit_t < oos_split, exit_t >= oos_split

    def _sr(mask):
        sub = trades.loc[mask]
        if sub.empty:
            return float("nan")
        d = sub.groupby(pd.to_datetime(sub["exit_time"], utc=True).dt.normalize())["ret_frac"].sum()
        return sharpe(d, ANN) if len(d) > 1 else float("nan")

    w, l = _pf_parts(trades["net_R"])
    gw, gl = _pf_parts(trades["gross_R"])
    isw, isl = _pf_parts(trades.loc[is_m, "net_R"])
    osw, osl = _pf_parts(trades.loc[oos_m, "net_R"])
    ftmo = rolling_pass_rate(trades, d0, d1, phase=1, max_days=60)

    row = dict(
        n_trades=len(trades), guard=guard,
        gross_pf=profit_factor(trades["gross_R"]), net_pf=profit_factor(trades["net_R"]),
        sharpe=sharpe(daily_ret, ANN), skew=float(daily_ret.skew()),
        ekurt=float(daily_ret.kurtosis()), max_dd=max_drawdown(equity),
        gross_R_mean=float(trades["gross_R"].mean()),
        cost_R_mean=float(trades["cost_R"].mean()),
        net_R_mean=float(trades["net_R"].mean()),
        risk_med=float(trades["risk_price"].median()),
        win_rate=float((trades["net_R"] > 0).mean()), n_obs=int(len(daily_ret)),
        is_trades=int(is_m.sum()), oos_trades=int(oos_m.sum()),
        is_pf=(isw / isl if isl > 0 else np.nan), oos_pf=(osw / osl if osl > 0 else np.nan),
        is_sharpe=_sr(is_m), oos_sharpe=_sr(oos_m),
        net_win=w, net_loss=l, gross_win=gw, gross_loss=gl,
        is_win=isw, is_loss=isl, oos_win=osw, oos_loss=osl,
        ftmo_pass_rate=ftmo["pass_rate"],
    )
    return row, daily_ret


def buy_and_hold(path: Path) -> tuple[dict, pd.Series]:
    daily = aggregate_daily(load_m1_spot(path))
    px = daily["mid_close"]
    ret = px.pct_change().dropna()
    entry_cost = float(daily["spread_close"].iloc[0] / px.iloc[0])
    eq = (1 + ret).cumprod() * (1 - entry_cost)
    yrs = (px.index[-1] - px.index[0]).days / 365.25
    return dict(sharpe=sharpe(ret, ANN), max_dd=max_drawdown(eq),
                cagr=float(eq.iloc[-1] ** (1 / yrs) - 1)), ret


def run(path_for, oos_split):
    missing = [n for n in INSTRUMENTS if not path_for(n).exists()]
    if missing:
        print(f"FATAL: missing H1 files for {missing}.")
        return 1

    rows, daily_map, bh_map, bh_ret_map = [], {}, {}, {}
    total = len(INSTRUMENTS) * len(TFS) * len(FAMS) * 3
    done = 0

    for inst in INSTRUMENTS:
        p = path_for(inst)
        print(f"\n[{inst}] loading H1 base ...", flush=True)
        base = load_m1_mid(p)
        daily_index = aggregate_daily(load_m1_spot(p)).index
        d0, d1 = daily_index[0], daily_index[-1]
        med_px, med_sp = float(base["mid_close"].median()), float(base["spread"].median())
        print(f"[{inst}] {len(base):,} H1 bars | {base.index[0].date()} -> {base.index[-1].date()} "
              f"| median px {med_px:,.1f} | spread {med_sp:.3f} pts ({1e4*med_sp/med_px:.2f} bps)",
              flush=True)
        bh_map[inst], bh_ret_map[inst] = buy_and_hold(p)

        for tf, freq in TFS.items():
            m = resample_mid(base, freq)
            for fam in FAMS:
                fn, variants = FAMILIES[fam]
                for i, params in enumerate(variants):
                    r, dret = score(base, m, fn, params, tf, daily_index, d0, d1, oos_split)
                    done += 1
                    if r is None:
                        print(f"  [{done}/{total}] {inst:>6} {tf:>2} {fam:<8} v{i}  too few trades", flush=True)
                        continue
                    r.update(instrument=inst, timeframe=tf, family=fam, variant=i,
                             params=str(params))
                    rows.append(r)
                    daily_map[(inst, tf, fam, i)] = dret
                    print(f"  [{done}/{total}] {inst:>6} {tf:>2} {fam:<8} v{i} "
                          f"n={r['n_trades']:>4} netPF={r['net_pf']:.2f} SR={r['sharpe']:+.2f} "
                          f"costR={r['cost_R_mean']*100:.1f}% guard={r['guard'][:4]}", flush=True)

    df = pd.DataFrame(rows)
    return df, daily_map, bh_map, bh_ret_map


def build_baskets(df, daily_map, bh_ret_map, oos_split):
    out, basket_daily = [], {}
    for tf in TFS:
        for fam in FAMS:
            for i in range(3):
                members = [(inst, daily_map[(inst, tf, fam, i)])
                           for inst in INSTRUMENTS if (inst, tf, fam, i) in daily_map]
                if len(members) < 2:
                    continue
                allret = pd.concat({n: s for n, s in members}, axis=1, sort=True).fillna(0.0)
                bret = allret.mean(axis=1)
                eq = equity_from_returns(bret)

                sub = df[(df.timeframe == tf) & (df.family == fam) & (df.variant == i)]
                nw, nl = sub["net_win"].sum(), sub["net_loss"].sum()
                gw, gl = sub["gross_win"].sum(), sub["gross_loss"].sum()
                iw, il = sub["is_win"].sum(), sub["is_loss"].sum()
                ow, ol = sub["oos_win"].sum(), sub["oos_loss"].sum()

                is_m = bret.index < oos_split
                yrs_b = (bret.index[-1] - bret.index[0]).days / 365.25
                cm = allret.corr().to_numpy()
                mean_corr = float(cm[np.triu_indices_from(cm, k=1)].mean()) if len(members) > 1 else np.nan
                out.append(dict(
                    timeframe=tf, family=fam, variant=i, n_members=len(members),
                    n_trades=int(sub["n_trades"].sum()),
                    cagr=float(eq.iloc[-1] ** (1 / yrs_b) - 1) if yrs_b > 0 else np.nan,
                    ann_vol=float(bret.std(ddof=1) * np.sqrt(ANN)),
                    mean_member_corr=mean_corr,
                    gross_pf=(gw / gl if gl > 0 else np.nan),
                    net_pf=(nw / nl if nl > 0 else np.nan),
                    sharpe=sharpe(bret, ANN), skew=float(bret.skew()),
                    ekurt=float(bret.kurtosis()), max_dd=max_drawdown(eq),
                    n_obs=int(len(bret)),
                    is_pf=(iw / il if il > 0 else np.nan),
                    oos_pf=(ow / ol if ol > 0 else np.nan),
                    is_sharpe=sharpe(bret[is_m], ANN) if is_m.sum() > 1 else np.nan,
                    oos_sharpe=sharpe(bret[~is_m], ANN) if (~is_m).sum() > 1 else np.nan,
                    oos_trades=int(sub["oos_trades"].sum()),
                    cost_R_mean=float(sub["cost_R_mean"].mean()),
                    ftmo_pass_rate=float(sub["ftmo_pass_rate"].mean()),
                ))
                basket_daily[(tf, fam, i)] = bret

    bdf = pd.DataFrame(out)

    bh_all = pd.concat({n: s for n, s in bh_ret_map.items()}, axis=1, sort=True).fillna(0.0)
    bh_b = bh_all.mean(axis=1)
    bh_eq = equity_from_returns(bh_b)
    yrs = (bh_b.index[-1] - bh_b.index[0]).days / 365.25
    bh_basket = dict(sharpe=sharpe(bh_b, ANN), max_dd=max_drawdown(bh_eq),
                     cagr=float(bh_eq.iloc[-1] ** (1 / yrs) - 1),
                     ann_vol=float(bh_b.std(ddof=1) * np.sqrt(ANN)))
    return bdf, basket_daily, bh_basket


def analyze(df, bdf, bh_map, bh_basket, tag, window_label):
    W = 122

    # DSR pools — batch-own STRUCTURAL pools (the swing trend+macross cells actually
    # searched THIS run), stated. Identical construction for both windows, no
    # cross-period mixing.
    single_pool = structural_pool(df, list(TFS.keys()), FAMS)
    basket_pool = bdf["sharpe"].dropna().to_numpy()

    def add_dsr(frame, pool):
        vals = []
        for _, r in frame.iterrows():
            d = deflated_sharpe(float(r["sharpe"]), pool, int(r["n_obs"]),
                                ann_factor=ANN, skewness=float(r["skew"]),
                                excess_kurtosis=float(r["ekurt"]))
            vals.append(d["dsr"])
        frame = frame.copy()
        frame["dsr"] = vals
        frame["oos_holds"] = ((frame["is_pf"] > 1.0) & (frame["oos_pf"] > 1.0)
                              & (frame["oos_trades"] >= MIN_OOS_TRADES)
                              & (frame["oos_sharpe"] > 0))
        return frame

    df = add_dsr(df, single_pool)
    bdf = add_dsr(bdf, basket_pool)

    print("\n" + "=" * W)
    print(f"  PRE-2018 OUT-OF-REGIME TEST  [{tag}]  window: {window_label}")
    print(f"  Instruments (5): {', '.join(INSTRUMENTS)}   (GER40 excluded: no pre-2015 ask/spread)")
    print(f"  Cost: REAL per-bar spread + {COST_BPS['commission']} bps comm + "
          f"{COST_BPS['slip_normal']}/{COST_BPS['slip_news']} bps/side slip | 1% risk | NO tuning")
    print(f"  Sharpe: daily-aggregated returns annualised at {ANN} for ALL timeframes")
    print(f"  Guard PASS: {(df['guard'] == 'PASS').sum()}/{len(df)}")
    e1 = expected_max_sharpe(single_pool); e2 = expected_max_sharpe(basket_pool)
    print(f"  DSR single-name pool: N={e1[1]} (batch structural), E[max SR]={e1[0]:+.3f}")
    print(f"  DSR basket pool     : N={e2[1]} baskets, E[max SR]={e2[0]:+.3f}")
    print("=" * W)

    print("\n  BASKET RESULTS — equal-risk across 5 indices, ONE config applied to all")
    print(f"  {'TF':>2} {'family':<8} {'v':>1} {'mem':>3} {'grPF':>5} {'netPF':>5} {'Sharpe':>7} {'DSR':>6} "
          f"{'maxDD':>6} {'CAGR':>6} {'vol':>6} {'corr':>5} {'trades':>6} {'IS_SR':>6} {'OOS_SR':>7} {'OOS?':>4}")
    print("  " + "-" * (W - 4))
    for _, r in bdf.sort_values("sharpe", ascending=False).iterrows():
        print(f"  {r['timeframe']:>2} {r['family']:<8} {int(r['variant']):>1} {int(r['n_members']):>3} "
              f"{r['gross_pf']:>5.2f} {r['net_pf']:>5.2f} {r['sharpe']:>+7.2f} {r['dsr']:>6.3f} "
              f"{r['max_dd']*100:>5.1f}% {r['cagr']*100:>5.1f}% {r['ann_vol']*100:>5.1f}% "
              f"{r['mean_member_corr']:>5.2f} {int(r['n_trades']):>6} {r['is_sharpe']:>+6.2f} "
              f"{r['oos_sharpe']:>+7.2f} {'YES' if r['oos_holds'] else 'no':>4}")

    print("\n  BENCHMARKS — buy-and-hold, same window, spread crossed once")
    print(f"  {'instrument':<12} {'B&H Sharpe':>11} {'B&H maxDD':>10} {'B&H CAGR':>9}")
    print("  " + "-" * 46)
    for inst in INSTRUMENTS:
        b = bh_map[inst]
        print(f"  {inst:<12} {b['sharpe']:>+11.2f} {b['max_dd']*100:>9.1f}% {b['cagr']*100:>8.1f}%")
    print(f"  {'EW B&H BASKET':<12} {bh_basket['sharpe']:>+11.2f} {bh_basket['max_dd']*100:>9.1f}% "
          f"{bh_basket['cagr']*100:>8.1f}%")

    # Headline cell: H4 macross v2 — the 2018-2025 lead.
    lead = bdf[(bdf.timeframe == "H4") & (bdf.family == "macross") & (bdf.variant == 2)]
    print("\n" + "=" * W)
    print("  HEADLINE — H4 macross v2 basket (the 2018-2025 lead cell)")
    print("  " + "-" * (W - 4))
    if len(lead):
        r = lead.iloc[0]
        print(f"  Sharpe {r['sharpe']:+.3f} | netPF {r['net_pf']:.3f} | maxDD {r['max_dd']*100:.1f}% | "
              f"CAGR {r['cagr']*100:.1f}% | vol {r['ann_vol']*100:.1f}% | corr {r['mean_member_corr']:.2f}")
        print(f"  IS_SR {r['is_sharpe']:+.3f} -> OOS_SR {r['oos_sharpe']:+.3f} | DSR {r['dsr']:.3f} | "
              f"trades {int(r['n_trades'])} | OOS-holds {'YES' if r['oos_holds'] else 'NO'}")
        print(f"  vs EW B&H basket ({bh_basket['sharpe']:+.2f}): "
              f"{'BEATS' if r['sharpe'] > bh_basket['sharpe'] else 'LOSES TO'} "
              f"(gap {r['sharpe'] - bh_basket['sharpe']:+.3f}) | "
              f"drawdown {r['max_dd']*100:.1f}% vs {bh_basket['max_dd']*100:.1f}% "
              f"({'LOWER-better' if r['max_dd'] < bh_basket['max_dd'] else 'HIGHER-worse'})")
    else:
        print("  MISSING — H4 macross v2 basket not built (insufficient members).")

    df.to_csv(RESULTS / f"basket_configs_scored_{tag}.csv", index=False)
    bdf.to_csv(RESULTS / f"basket_results_{tag}.csv", index=False)
    print(f"\n  Written -> results/basket_configs_scored_{tag}.csv, results/basket_results_{tag}.csv")
    print("=" * W)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", required=True, help="data file suffix, e.g. 2013_2017 or 2018_2025")
    ap.add_argument("--split", required=True, help="IS/OOS split date, e.g. 2016-01-01")
    ap.add_argument("--tag", required=True, help="output tag, e.g. pre2018 or new5")
    ap.add_argument("--label", default="", help="human window label for the header")
    args = ap.parse_args()

    oos_split = pd.Timestamp(args.split, tz="UTC")
    path_for = make_path_for(args.suffix)
    got = run(path_for, oos_split)
    if got == 1:
        return 1
    df, daily_map, bh_map, bh_ret_map = got
    bdf, _, bh_basket = build_baskets(df, daily_map, bh_ret_map, oos_split)
    analyze(df, bdf, bh_map, bh_basket, args.tag, args.label or args.suffix)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
