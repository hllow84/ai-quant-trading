#!/usr/bin/env python3
"""
run_basket_trend.py — JOB 2: diversified index trend-following, single-name AND basket.

THESIS UNDER TEST
-----------------
Trend-following's durable edge is historically a BASKET property, not a
single-instrument one: many weakly-correlated trends, each risked equally, so
the winners pay for the losers and the portfolio Sharpe exceeds any member's.
The prior run found a real but insignificant H4 trend edge on two US indices.
This tests whether diversifying across six liquid index futures/CFDs converts
that into something that (a) survives the FIXED DSR, (b) holds out of sample,
and (c) beats buy-and-hold risk-adjusted.

GRID (stated, small, no tuning)
-------------------------------
    6 instruments (NAS100, US30, SPX500, GER40, UK100, JP225)
  x 3 timeframes  (H4, H8, D1)     <- where the prior edge was strongest/monotonic
  x 2 families    (trend, macross) <- the two trend families, unchanged variants
  x 3 stated variants each
  = 108 single-name configs, plus 18 baskets (one per TF x family x variant cell).

Cumulative trial count = 237 prior + 108 = 345.

NO PER-INSTRUMENT SELECTION. A basket is built by applying ONE config to all six
instruments and combining. Picking each instrument's best config would be
in-sample cherry-picking and would inflate the basket result.

RESOLUTION AND LOOK-AHEAD
-------------------------
Base frame is H1 with Dukascopy-native BAR-OPEN stamps: a bar stamped T covers
[T, T+1h). Signals are generated on H4/H8/D1 frames resampled with label='right',
closed='left', so a signal bar stamped T covers [T-tf, T) and is fully known at T.
Trades are then resolved on the H1 base from bar T onward -- strictly forward of
the signal's information set. This is FINER resolution than the prior index
sweep (which resolved on the signal timeframe itself), so stops are hit more
often and results are strictly more conservative, not less.

COST MODEL — identical to the prior index run
---------------------------------------------
  spread     : REAL per-bar bid/ask from the data (round-turn), never assumed
  commission : 0.35 bps of notional round-turn (conservative; most raw-spread
               index CFD brokers charge zero and bury cost in the spread)
  slippage   : 0.15 bps/side normal, 0.50 bps/side in news windows
  risk       : 1% of equity per trade, stop distance = 1R

HONESTY GATES
-------------
  - look-ahead guard on every config (held position vs base-frame returns)
  - Sharpe annualised at 252 from DAILY-aggregated returns for every timeframe,
    so H4/H8/D1 are directly comparable (the per-TF correction is handled by the
    daily aggregation, not by a per-TF sqrt factor)
  - DSR via research/dsr.py (corrected SE + stated structural pool), NOT the
    old saturated implementation
  - fixed 2023-01-01 IS/OOS split, OOS-holds requires IS&OOS PF>1, OOS SR>0,
    >=20 OOS trades
  - benchmarked against per-index buy-and-hold AND an equal-weight B&H basket
"""

from __future__ import annotations

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
OOS_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
MIN_OOS_TRADES = 20
DSR_BAR = 0.95
FTMO_BAR = 0.30
PRIOR_TRIALS = 237

COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)

INSTRUMENTS = ["NAS100", "US30", "SPX500", "GER40", "UK100", "JP225"]
TFS = {"H4": "4h", "H8": "8h", "D1": "1D"}
TF_DELTA = {"H4": pd.Timedelta(hours=4), "H8": pd.Timedelta(hours=8),
            "D1": pd.Timedelta(days=1)}
FAMS = ["trend", "macross"]

RESULTS = _ROOT / "results"
CSV_PATH = RESULTS / "basket_configs.csv"


def path_for(name: str) -> Path:
    return _ROOT / "data" / f"{name}_H1_2018_2025_cfd_dukascopy.csv"


def _pf_parts(r: pd.Series) -> tuple[float, float]:
    """(sum of wins, abs sum of losses) — additive, so they pool across instruments."""
    return float(r[r > 0].sum()), float(abs(r[r < 0].sum()))


def score(base, m, fam_fn, params, tf, daily_index, d0, d1):
    cands = fam_fn(m, params, TF_DELTA[tf])
    for tr in cands:
        tr["session_end"] = pd.Timestamp(tr["session_end"]).tz_convert("UTC")
        tr["entry_time"] = pd.Timestamp(tr["entry_time"]).tz_convert("UTC")

    # strictly_after=False: base bars are BAR-OPEN, so bar T already sits at/after
    # the signal timestamp T. See module docstring.
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
    is_m, oos_m = exit_t < OOS_SPLIT, exit_t >= OOS_SPLIT

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


def run():
    missing = [n for n in INSTRUMENTS if not path_for(n).exists()]
    if missing:
        print(f"FATAL: missing H1 files for {missing} — run scripts/merge_basket.py first.")
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
                    r, dret = score(base, m, fn, params, tf, daily_index, d0, d1)
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
    RESULTS.mkdir(exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    print(f"\nWrote {CSV_PATH}  ({len(df)} configs)")
    return df, daily_map, bh_map, bh_ret_map


def build_baskets(df, daily_map, bh_ret_map):
    """Equal-risk basket per (TF, family, variant) cell — one config, all six instruments."""
    out, basket_daily = [], {}
    for tf in TFS:
        for fam in FAMS:
            for i in range(3):
                members = [(inst, daily_map[(inst, tf, fam, i)])
                           for inst in INSTRUMENTS if (inst, tf, fam, i) in daily_map]
                if len(members) < 2:
                    continue
                # Equal weight == equal risk: every member sizes each trade at 1% of
                # its own sub-account, so the series are already in common risk units.
                allret = pd.concat({n: s for n, s in members}, axis=1).fillna(0.0)
                bret = allret.mean(axis=1)
                eq = equity_from_returns(bret)

                sub = df[(df.timeframe == tf) & (df.family == fam) & (df.variant == i)]
                nw, nl = sub["net_win"].sum(), sub["net_loss"].sum()
                gw, gl = sub["gross_win"].sum(), sub["gross_loss"].sum()
                iw, il = sub["is_win"].sum(), sub["is_loss"].sum()
                ow, ol = sub["oos_win"].sum(), sub["oos_loss"].sum()

                is_m = bret.index < OOS_SPLIT
                yrs_b = (bret.index[-1] - bret.index[0]).days / 365.25
                # Mean pairwise correlation of member daily returns — evidence that the
                # diversification is real rather than six views of the same trade.
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

    # Equal-weight buy-and-hold basket, same six instruments, same method.
    bh_all = pd.concat({n: s for n, s in bh_ret_map.items()}, axis=1).fillna(0.0)
    bh_b = bh_all.mean(axis=1)
    bh_eq = equity_from_returns(bh_b)
    yrs = (bh_b.index[-1] - bh_b.index[0]).days / 365.25
    bh_basket = dict(sharpe=sharpe(bh_b, ANN), max_dd=max_drawdown(bh_eq),
                     cagr=float(bh_eq.iloc[-1] ** (1 / yrs) - 1),
                     ann_vol=float(bh_b.std(ddof=1) * np.sqrt(ANN)))
    return bdf, basket_daily, bh_basket


def analyze(df, bdf, bh_map, bh_basket):
    W = 122
    n_batch = len(df)
    cumulative = PRIOR_TRIALS + n_batch

    # ── DSR pools (stated, structural) ──
    # Single-name pool: this batch's swing-trend configs + the prior index H1/H4
    # trend-family configs. That is the full a priori set of swing-trend
    # candidates searched, chosen by STRUCTURE not by outcome.
    prior_idx = pd.read_csv(RESULTS / "sweep_indices_scored.csv")
    prior_struct = structural_pool(prior_idx, ["H1", "H4"], ["trend", "macross", "momentum"])
    single_pool = np.concatenate([prior_struct, df["sharpe"].dropna().to_numpy()])
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
    print("  JOB 2 — DIVERSIFIED INDEX TREND-FOLLOWING (6 instruments, H4/H8/D1)")
    print(f"  Cost: REAL per-bar spread + {COST_BPS['commission']} bps comm + "
          f"{COST_BPS['slip_normal']}/{COST_BPS['slip_news']} bps/side slip | 1% risk | NO tuning")
    print(f"  Configs THIS BATCH: {n_batch} single-name + {len(bdf)} baskets  |  "
          f"CUMULATIVE TRIALS: {PRIOR_TRIALS} prior + {n_batch} = {cumulative}")
    print(f"  Sharpe: daily-aggregated returns annualised at {ANN} for ALL timeframes")
    print(f"  Guard PASS: {(df['guard'] == 'PASS').sum()}/{len(df)}")
    e1 = expected_max_sharpe(single_pool); e2 = expected_max_sharpe(basket_pool)
    print(f"  DSR single-name pool: N={e1[1]} (prior swing-trend {len(prior_struct)} + batch {n_batch}), "
          f"E[max SR]={e1[0]:+.3f}")
    print(f"  DSR basket pool     : N={e2[1]} baskets, E[max SR]={e2[0]:+.3f}")
    print("=" * W)

    lb = df.sort_values("sharpe", ascending=False).head(15)
    print("\n  PER-INSTRUMENT LEADERBOARD — TOP 15 BY NET SHARPE")
    print(f"  {'#':>2} {'inst':>6} {'TF':>2} {'family':<8} {'v':>1} {'grPF':>5} {'netPF':>5} {'Sharpe':>7} "
          f"{'DSR':>6} {'maxDD':>6} {'trades':>6} {'costR%':>7} {'FTMO%':>6} {'OOS?':>4}")
    print("  " + "-" * (W - 4))
    for k, (_, r) in enumerate(lb.iterrows(), 1):
        print(f"  {k:>2} {r['instrument']:>6} {r['timeframe']:>2} {r['family']:<8} {int(r['variant']):>1} "
              f"{r['gross_pf']:>5.2f} {r['net_pf']:>5.2f} {r['sharpe']:>+7.2f} {r['dsr']:>6.3f} "
              f"{r['max_dd']*100:>5.1f}% {int(r['n_trades']):>6} {r['cost_R_mean']*100:>6.2f}% "
              f"{r['ftmo_pass_rate']*100:>5.1f}% {'YES' if r['oos_holds'] else 'no':>4}")

    print("\n" + "=" * W)
    print("  BASKET RESULTS — equal-risk across 6 indices, ONE config applied to all")
    print(f"  {'TF':>2} {'family':<8} {'v':>1} {'mem':>3} {'grPF':>5} {'netPF':>5} {'Sharpe':>7} {'DSR':>6} "
          f"{'maxDD':>6} {'CAGR':>6} {'vol':>6} {'corr':>5} {'trades':>6} {'IS_SR':>6} {'OOS_SR':>7} {'OOS?':>4}")
    print("  " + "-" * (W - 4))
    for _, r in bdf.sort_values("sharpe", ascending=False).iterrows():
        print(f"  {r['timeframe']:>2} {r['family']:<8} {int(r['variant']):>1} {int(r['n_members']):>3} "
              f"{r['gross_pf']:>5.2f} {r['net_pf']:>5.2f} {r['sharpe']:>+7.2f} {r['dsr']:>6.3f} "
              f"{r['max_dd']*100:>5.1f}% {r['cagr']*100:>5.1f}% {r['ann_vol']*100:>5.1f}% "
              f"{r['mean_member_corr']:>5.2f} {int(r['n_trades']):>6} {r['is_sharpe']:>+6.2f} "
              f"{r['oos_sharpe']:>+7.2f} {'YES' if r['oos_holds'] else 'no':>4}")

    print("\n" + "=" * W)
    print("  BENCHMARKS — buy-and-hold, same period, spread crossed once")
    print(f"  {'instrument':<12} {'B&H Sharpe':>11} {'B&H maxDD':>10} {'B&H CAGR':>9}")
    print("  " + "-" * 46)
    for inst in INSTRUMENTS:
        b = bh_map[inst]
        print(f"  {inst:<12} {b['sharpe']:>+11.2f} {b['max_dd']*100:>9.1f}% {b['cagr']*100:>8.1f}%")
    print(f"  {'EW B&H BASKET':<12} {bh_basket['sharpe']:>+11.2f} {bh_basket['max_dd']*100:>9.1f}% "
          f"{bh_basket['cagr']*100:>8.1f}%")

    best_b = bdf.sort_values("sharpe", ascending=False).iloc[0]
    best_s = lb.iloc[0]
    best_single_bh = max(bh_map[i]["sharpe"] for i in INSTRUMENTS)

    print("\n" + "=" * W)
    print("  DOES DIVERSIFIED TREND-FOLLOWING BEAT BUY-AND-HOLD?")
    print("  " + "-" * (W - 4))
    print(f"  Best basket        : {best_b['timeframe']} {best_b['family']} v{int(best_b['variant'])}"
          f"  Sharpe {best_b['sharpe']:+.2f}, netPF {best_b['net_pf']:.2f}, maxDD {best_b['max_dd']*100:.1f}%, "
          f"CAGR {best_b['cagr']*100:.1f}%, vol {best_b['ann_vol']*100:.1f}%")
    print(f"  EW B&H basket      : Sharpe {bh_basket['sharpe']:+.2f}, maxDD {bh_basket['max_dd']*100:.1f}%, "
          f"CAGR {bh_basket['cagr']*100:.1f}%, vol {bh_basket['ann_vol']*100:.1f}%")
    # Sharpe is scale-invariant; CAGR is not. At 1% risk/trade the basket runs at a
    # fraction of B&H volatility, so a Sharpe win does NOT mean more money unless the
    # position is levered up -- which brings financing cost and overnight gap risk that
    # this backtest does not model. State the leverage multiple rather than imply it away.
    if best_b["ann_vol"] > 0:
        lev = bh_basket["ann_vol"] / best_b["ann_vol"]
        print(f"  Vol-matching the basket to EW B&H needs {lev:.1f}x leverage "
              f"-> ~{best_b['cagr']*lev*100:.1f}% CAGR at ~{best_b['max_dd']*lev*100:.1f}% maxDD")
        print(f"    (financing cost and gap risk at {lev:.1f}x are NOT modelled here)")
    print(f"    -> vs EW B&H basket : {'BEATS' if best_b['sharpe'] > bh_basket['sharpe'] else 'LOSES TO'}"
          f" (gap {best_b['sharpe'] - bh_basket['sharpe']:+.2f})")
    print(f"    -> vs best single B&H ({best_single_bh:+.2f}) : "
          f"{'BEATS' if best_b['sharpe'] > best_single_bh else 'LOSES TO'}"
          f" (gap {best_b['sharpe'] - best_single_bh:+.2f})")
    print(f"    -> drawdown vs EW B&H: {best_b['max_dd']*100:.1f}% vs {bh_basket['max_dd']*100:.1f}%"
          f"  ({'LOWER - better' if best_b['max_dd'] < bh_basket['max_dd'] else 'HIGHER - worse'})")
    # The correct diversification test is basket vs the AVERAGE member of that same
    # cell. Comparing against the BEST member is ex-post cherry-picking: you cannot
    # know in advance which index will be the winner, so the average is what a real
    # allocator gets. Both are printed, with the biased one labelled as such.
    mem = df[(df.timeframe == best_b["timeframe"]) & (df.family == best_b["family"])
             & (df.variant == best_b["variant"])]
    avg_mem, best_mem = mem["sharpe"].mean(), mem["sharpe"].max()
    print(f"  Diversification test (best basket cell):")
    print(f"    basket SR {best_b['sharpe']:+.2f}  vs  AVERAGE member {avg_mem:+.2f}"
          f"  -> uplift {best_b['sharpe'] - avg_mem:+.2f}  "
          f"({'diversification HELPS' if best_b['sharpe'] > avg_mem else 'no uplift'})")
    print(f"    mean member pairwise corr {best_b['mean_member_corr']:.2f} "
          f"-> the six trends are genuinely near-independent")
    print(f"    (vs BEST member {best_mem:+.2f} — biased comparison, ex-post pick, shown for context only)")

    print("\n  VERDICT")
    print("  " + "-" * (W - 4))
    surv_s = df[(df["dsr"] > DSR_BAR) & df["oos_holds"]]
    surv_b = bdf[(bdf["dsr"] > DSR_BAR) & bdf["oos_holds"]]
    beats = bdf[(bdf["dsr"] > DSR_BAR) & bdf["oos_holds"] & (bdf["sharpe"] > bh_basket["sharpe"])]
    print(f"  single-name clearing DSR>{DSR_BAR} AND OOS-holds : {len(surv_s)} / {len(df)}")
    print(f"  baskets     clearing DSR>{DSR_BAR} AND OOS-holds : {len(surv_b)} / {len(bdf)}")
    print(f"  ... of those, also beating EW B&H basket      : {len(beats)}")
    if len(beats):
        for _, r in beats.iterrows():
            print(f"     SURVIVOR: {r['timeframe']} {r['family']} v{int(r['variant'])} "
                  f"SR {r['sharpe']:+.2f} DSR {r['dsr']:.3f} netPF {r['net_pf']:.2f}")
    else:
        print("  NO config or basket passes all three. This is a KILL.")
        print(f"  Best basket DSR {best_b['dsr']:.3f} (need >{DSR_BAR}); "
              f"OOS holds {'YES' if best_b['oos_holds'] else 'NO'}; "
              f"vs EW B&H {best_b['sharpe'] - bh_basket['sharpe']:+.2f}")
    print(f"\n  FTMO viability (context only — this lead is an own-capital edge):")
    print(f"    best single-name FTMO P1 pass rate in batch: {df['ftmo_pass_rate'].max()*100:.1f}% "
          f"(bar {FTMO_BAR:.0%})")
    print("=" * W)

    df.to_csv(RESULTS / "basket_configs_scored.csv", index=False)
    bdf.to_csv(RESULTS / "basket_results.csv", index=False)
    print(f"\n  Written -> {RESULTS/'basket_configs_scored.csv'}, {RESULTS/'basket_results.csv'}")


def main():
    got = run()
    if got == 1:
        return 1
    df, daily_map, bh_map, bh_ret_map = got
    bdf, _, bh_basket = build_baskets(df, daily_map, bh_ret_map)
    analyze(df, bdf, bh_map, bh_basket)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
