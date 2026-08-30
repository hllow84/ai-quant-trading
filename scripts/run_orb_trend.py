#!/usr/bin/env python3
"""
run_orb_trend.py — TREND-FILTERED VARIANT of the audited ORB (STATE_OF_PLAY
section 10 / 10.1-10.3). Reuses the audited breakout-detection and cost engine
UNCHANGED (strategies.orb.orb() with stop_mode='or_range', the audited default;
research.ftmo_engine.simulate_trades unchanged) and adds ONE new filter on top:
a causal daily-SMA-50 trend gate (strategies.orb.daily_trend_direction()).

WHY THIS TEST EXISTS
---------------------
The unfiltered ORB kill (section 10) was driven by two specific failures:
  (a) out-of-regime gross PF reversal (mean gross PF 1.141 -> 0.960, 12/12 -> 2/12
      cells gross-positive), and
  (b) single-year P&L concentration (0/12 cells pass top-year<=60% in regime).
A trend filter that only decides WHICH SIDE of a breakout to take has no
mechanism to fix either of these on its own: it cannot change whether the
breakout edge exists at all pre-2018 (that is a property of the raw price
action, not of which direction is allowed), and it cannot on its own spread
P&L more evenly across years (a trend filter concentrates INTO trending years,
if anything). This script checks that empirically rather than assuming it.

THE FILTER — stated, causal, unfitted
---------------------------------------
Daily 50-session SMA of the CASH-SESSION close (see strategies.orb.
daily_trend_direction() for why the cash close, not the 23-hour CFD close, is
used — it is the one definition available identically on both windows).
50 sessions (~10 weeks) is the canonical "intermediate trend" length, chosen
for being a standard textbook value, not fitted to this data. Only a long
break is taken when the PRIOR session's close was above its (also prior-only)
50-session SMA; only a short break when below. The trend value assigned to
session D is computed from an explicit .shift(1), so no information from
session D itself (including which way it breaks) can leak into the gate that
decides whether D's trade is taken. This is proven, not just asserted, by:
  (1) run_orb.py's existing statistical look-ahead guard on the position series
      (unchanged, run against the FILTERED trades), and
  (2) a DIRECT alignment assertion here: for every filtered candidate, trend_dir
      is looked up strictly on the candidate's own et_date via .get(), and
      trend_dir itself was built by .shift(1) over an et_date-sorted Series — so
      the value used for day D is definitionally sourced from index position
      D-1 or earlier. assert_causal() below re-derives this from the raw
      (unshifted) sma/close pair and checks every SURVIVING candidate against it.

GRID — 12 filtered cells, same breadth as the audited 12
-----------------------------------------------------------
2 instruments (NAS100, US30) x 2 opening ranges (15/30 min) x 3 targets
(1R/2R/close). stop_mode='or_range' throughout (the audited default, NOT the
audit's moderate-stop variant). Run on BOTH windows: 2018-2025 (in regime) and
2013-2017 (out of regime), same data files and cost model as section 10.

Usage: py -3.14 scripts/run_orb_trend.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

import run_orb as ro
from research.gold_data import load_m1_spot, aggregate_daily
from research.ftmo_engine import simulate_trades, de_overlap, build_daily_returns, equity_from_returns
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe
from research.backtest import guard_look_ahead, LookAheadError
from strategies.orb import (
    orb, rth_m1, daily_trend_direction, OR_MINUTES, TARGETS, ET, RTH_OPEN_MIN,
    TREND_SMA_LENGTH,
)

BARS_PER_YEAR = 252
CONC_BAR = 0.60
MIN_OOS_TRADES = 20
DSR_BAR = 0.95

WINDOWS = {
    "in_regime": dict(
        label="2018-2025",
        oos_split=pd.Timestamp("2023-01-01", tz="UTC"),
        instruments={
            "NAS100": _ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv",
            "US30":   _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",
        },
    ),
    "out_regime": dict(
        label="2013-2017",
        oos_split=pd.Timestamp("2016-01-01", tz="UTC"),
        instruments={
            "NAS100": _ROOT / "data" / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv",
            "US30":   _ROOT / "data" / "US30_M1RTH_2013_2017_cfd_dukascopy.csv",
        },
    ),
}


def assert_causal(rth: pd.DataFrame, trend_dir: pd.Series, cands: list[dict]) -> bool:
    """Direct re-derivation check: for every surviving candidate, the trend value
    used to admit it must equal sign(close_{d-1} - sma_{d-1}) computed from
    sessions STRICTLY BEFORE the candidate's own et_date, with the candidate's
    own et_date's close/range excluded from that computation entirely."""
    sess_close = rth.groupby("et_date")["mid_close"].last().sort_index()
    sma = sess_close.rolling(TREND_SMA_LENGTH, min_periods=TREND_SMA_LENGTH).mean()
    raw_dir = np.sign(sess_close - sma)  # NOT shifted — value AT that session
    dates = sess_close.index
    ok = True
    for c in cands:
        day = c["et_date"]
        pos = dates.get_loc(day)
        if pos == 0:
            ok = False
            continue
        prior_date = dates[pos - 1]
        expected = raw_dir.loc[prior_date]  # strictly the PRIOR session's own value
        got = trend_dir.get(day, np.nan)
        if not (np.isfinite(expected) and np.isfinite(got) and expected == got):
            ok = False
        side_ok = (c["side"] == "long" and expected == 1) or (c["side"] == "short" and expected == -1)
        if not side_ok:
            ok = False
    return ok


def _split_stats(trades: pd.DataFrame, oos_split: pd.Timestamp) -> tuple:
    exit_t = pd.to_datetime(trades["exit_time"], utc=True)
    is_m, oos_m = exit_t < oos_split, exit_t >= oos_split

    def pf(mask):
        return profit_factor(trades.loc[mask, "net_R"]) if mask.any() else float("nan")

    def sr(mask):
        sub = trades.loc[mask]
        if sub.empty:
            return float("nan")
        d = sub.groupby(pd.to_datetime(sub["exit_time"], utc=True).dt.normalize())["ret_frac"].sum()
        return sharpe(d, BARS_PER_YEAR) if len(d) > 1 else float("nan")

    return int(is_m.sum()), int(oos_m.sum()), pf(is_m), pf(oos_m), sr(is_m), sr(oos_m)


def _year_concentration(trades: pd.DataFrame) -> tuple[float, float, int, int]:
    yr = pd.to_datetime(trades["exit_time"], utc=True).dt.year
    agg = trades.groupby(yr)["net_R"].sum()
    total = float(agg.sum())
    top = float(agg.max()) if len(agg) else float("nan")
    share = (top / total) if total > 0 else float("nan")
    return top, share, int(len(agg)), int((agg > 0).sum())


def score(m1: pd.DataFrame, rth: pd.DataFrame, trend_dir: pd.Series | None, params: dict,
          daily_index, cost_bps, oos_split) -> tuple[dict, pd.DataFrame, list[dict]]:
    empty = pd.DataFrame()
    cands = orb(m1, params, trend_dir=trend_dir)
    if not cands:
        return dict(n_cands=0, n_trades=0, guard="N/A"), empty, cands

    ent = pd.DatetimeIndex([c["entry_time"] for c in cands]).tz_convert(ET)
    ent_min = ent.hour * 60 + ent.minute
    earliest_legal = RTH_OPEN_MIN + int(params["or_minutes"])
    or_ok = bool((ent_min >= earliest_legal).all())

    causal_ok = True
    if trend_dir is not None:
        causal_ok = assert_causal(rth, trend_dir, cands)

    trades = de_overlap(simulate_trades(m1, cands, strictly_after=False,
                                        cost_bps=cost_bps, slip_bps_fn=ro.slip_bps))
    if trades.empty:
        return dict(n_cands=len(cands), n_trades=0, guard="N/A"), empty, cands

    pos = pd.Series(0.0, index=m1.index)
    idx_ns = m1.index.tz_localize(None).values.astype("datetime64[ns]").view("int64")
    n = len(m1.index)
    delta = np.zeros(n + 1)
    for et_, xt, side in zip(trades["entry_time"], trades["exit_time"], trades["side"]):
        s = int(np.searchsorted(idx_ns, pd.Timestamp(et_).tz_convert(None).value, side="right"))
        e = int(np.searchsorted(idx_ns, pd.Timestamp(xt).tz_convert(None).value, side="right"))
        val = 1.0 if side == "long" else -1.0
        if s < e:
            delta[s] += val
            delta[e] -= val
    pos.iloc[:] = np.cumsum(delta[:n])

    guard = "N/A"
    try:
        guard_look_ahead(pos, m1["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS" if (or_ok and causal_ok) else (
            "FAIL:OR-window" if not or_ok else "FAIL:trend-causality")
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"

    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    is_n, oos_n, is_pf, oos_pf, is_sr, oos_sr = _split_stats(trades, oos_split)
    top_R, top_share, n_years, n_pos_years = _year_concentration(trades)

    res = dict(
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
        net_R_total=float(trades["net_R"].sum()),
        win_rate=float((trades["net_R"] > 0).mean()),
        n_obs=int(len(daily_ret)),
        is_trades=is_n, oos_trades=oos_n,
        is_pf=is_pf, oos_pf=oos_pf, is_sharpe=is_sr, oos_sharpe=oos_sr,
        top_year_R=top_R, top_year_share=top_share,
        n_years=n_years, n_pos_years=n_pos_years,
    )
    return res, trades, cands


def removed_trade_analysis(trades_unf: pd.DataFrame, trades_filt: pd.DataFrame) -> dict:
    """Characterise the trades the filter removed: kept = survives in trades_filt
    (matched on entry_time, which is unique per day/side by construction),
    removed = present in unfiltered, absent in filtered."""
    if trades_unf.empty:
        return dict(n_unf=0, n_filt=0, n_removed=0)
    kept_keys = set(trades_filt["entry_time"]) if not trades_filt.empty else set()
    is_removed = ~trades_unf["entry_time"].isin(kept_keys)
    removed = trades_unf[is_removed]
    kept = trades_unf[~is_removed]
    return dict(
        n_unf=len(trades_unf), n_filt=len(trades_filt), n_removed=len(removed),
        removed_win_rate=float((removed["net_R"] > 0).mean()) if len(removed) else float("nan"),
        kept_win_rate=float((kept["net_R"] > 0).mean()) if len(kept) else float("nan"),
        removed_mean_grossR=float(removed["gross_R"].mean()) if len(removed) else float("nan"),
        kept_mean_grossR=float(kept["gross_R"].mean()) if len(kept) else float("nan"),
        removed_mean_netR=float(removed["net_R"].mean()) if len(removed) else float("nan"),
        kept_mean_netR=float(kept["net_R"].mean()) if len(kept) else float("nan"),
    )


def buy_and_hold(daily: pd.DataFrame) -> dict:
    px = daily["mid_close"]
    ret = px.pct_change().dropna()
    entry_cost = float(daily["spread_close"].iloc[0] / px.iloc[0])
    eq = (1 + ret).cumprod() * (1 - entry_cost)
    return dict(sharpe=sharpe(ret, BARS_PER_YEAR), max_dd=max_drawdown(eq))


def run_window(win_key: str) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    w = WINDOWS[win_key]
    rows_filt, rows_unf, removed_rows = [], [], []
    bh = {}
    for inst, path in w["instruments"].items():
        if not path.exists():
            print(f"[{win_key}/{inst}] MISSING {path.name}")
            continue
        print(f"[{win_key}/{inst}] loading M1 ...", flush=True)
        spot = load_m1_spot(path)
        daily = aggregate_daily(spot)
        daily_index = daily.index
        bh[inst] = buy_and_hold(daily)
        m1 = pd.DataFrame(index=spot.index)
        for c in ("open", "high", "low", "close"):
            m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
        m1["spread"] = spot["spread"]
        del spot
        rth = rth_m1(m1)
        trend_dir = daily_trend_direction(rth, TREND_SMA_LENGTH)
        n_sessions = rth["et_date"].nunique()
        n_warmup = int(trend_dir.isna().sum())
        n_up = int((trend_dir == 1).sum())
        n_dn = int((trend_dir == -1).sum())
        print(f"[{win_key}/{inst}] {n_sessions} sessions | trend: {n_warmup} warmup/NaN, "
              f"{n_up} up-days, {n_dn} down-days", flush=True)

        for n_or in OR_MINUTES:
            for target in TARGETS:
                p = dict(or_minutes=n_or, target=target, stop_mode="or_range")
                res_unf, tr_unf, _ = score(m1, rth, None, p, daily_index, ro.COST_BPS, w["oos_split"])
                res_filt, tr_filt, _ = score(m1, rth, trend_dir, p, daily_index, ro.COST_BPS, w["oos_split"])
                rm = removed_trade_analysis(tr_unf, tr_filt)

                rows_unf.append(dict(instrument=inst, window=win_key, **p, **res_unf))
                rows_filt.append(dict(instrument=inst, window=win_key, **p, **res_filt))
                removed_rows.append(dict(instrument=inst, window=win_key, **p, **rm))

                print(f"  [{win_key}] {inst:>6} OR={n_or:>2} tgt={target:<5} "
                      f"UNF n={res_unf.get('n_trades',0):>4} grPF={res_unf.get('gross_pf',float('nan')):.3f} "
                      f"netPF={res_unf.get('net_pf',float('nan')):.3f} | "
                      f"FILT n={res_filt.get('n_trades',0):>4} grPF={res_filt.get('gross_pf',float('nan')):.3f} "
                      f"netPF={res_filt.get('net_pf',float('nan')):.3f} SR={res_filt.get('sharpe',float('nan')):+.2f} "
                      f"guard={res_filt.get('guard','?')[:12]} removed={rm.get('n_removed',0)}",
                      flush=True)

    return pd.DataFrame(rows_filt), pd.DataFrame(rows_unf), dict(bh=bh, removed=pd.DataFrame(removed_rows))


def score_gates(traded: pd.DataFrame, bh: dict) -> tuple[pd.DataFrame, tuple]:
    traded = traded.copy()
    sr_batch = traded["sharpe"].fillna(0.0).to_numpy()

    def _dsr(r):
        if not np.isfinite(r["sharpe"]) or r["n_obs"] < 4:
            return np.nan
        return deflated_sharpe(
            sr_best=float(r["sharpe"]), sr_trials=sr_batch, n_obs=int(r["n_obs"]),
            skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
            excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0,
        )["dsr"]

    traded["dsr"] = traded.apply(_dsr, axis=1)
    traded["oos_holds"] = ((traded["is_pf"] > 1.0) & (traded["oos_pf"] > 1.0)
                           & (traded["oos_trades"] >= MIN_OOS_TRADES)
                           & (traded["oos_sharpe"] > 0))
    traded["gross_edge"] = traded["gross_pf"] > 1.0
    traded["not_concentrated"] = (traded["top_year_share"].notna()
                                  & (traded["top_year_share"] <= CONC_BAR))
    traded["extreme_concentration"] = (traded["top_year_share"].notna()
                                       & (traded["top_year_share"] >= 1.0))
    traded["beats_bh"] = traded.apply(
        lambda r: bool(np.isfinite(r["sharpe"]) and r["instrument"] in bh
                       and r["sharpe"] > bh[r["instrument"]]["sharpe"]), axis=1)
    traded["SURVIVOR"] = (traded["gross_edge"] & (traded["net_pf"] > 1.0)
                          & (traded["sharpe"] > 0) & (traded["dsr"] > DSR_BAR)
                          & traded["oos_holds"] & traded["not_concentrated"]
                          & traded["beats_bh"] & (traded["guard"] == "PASS"))
    e_struct = expected_max_sharpe(sr_batch)
    return traded, e_struct


def print_table(df: pd.DataFrame, label: str):
    W = 150
    print(f"\n{'='*W}\n{label}\n{'='*W}")
    print(f"  {'inst':>6} {'OR':>3} {'target':>6} {'n':>5} {'grPF':>6} {'netPF':>6} "
          f"{'Sharpe':>7} {'DSR':>5} {'maxDD':>6} {'win%':>5} {'costR%':>7} {'top%':>6} "
          f"{'OOS?':>4} {'B&H?':>5} {'guard':>16}")
    for _, r in df.sort_values(["instrument", "or_minutes", "target"]).iterrows():
        share = r["top_year_share"]
        print(f"  {r['instrument']:>6} {int(r['or_minutes']):>3} {r['target']:>6} "
              f"{int(r['n_trades']):>5} {r['gross_pf']:>6.3f} {r['net_pf']:>6.3f} "
              f"{r['sharpe']:>+7.2f} {r['dsr']:>5.2f} {r['max_dd']*100:>5.1f}% "
              f"{r['win_rate']*100:>4.1f}% {r['cost_R_mean']*100:>6.1f}% "
              + (f"{share*100:>5.0f}%" if np.isfinite(share) else f"{'n/a':>6}")
              + f" {'YES' if r['oos_holds'] else 'no':>4} "
              f"{'BEAT' if r['beats_bh'] else 'lose':>5} {r['guard'][:16]:>16}")


def main():
    all_filt, all_unf, meta = {}, {}, {}
    for win_key in WINDOWS:
        df_filt, df_unf, m = run_window(win_key)
        all_filt[win_key] = df_filt
        all_unf[win_key] = df_unf
        meta[win_key] = m

    OUT = _ROOT / "results"
    OUT.mkdir(parents=True, exist_ok=True)

    scored = {}
    for win_key, df in all_filt.items():
        traded = df[df.get("n_trades", pd.Series(dtype=int)).fillna(0) > 0].copy()
        s, e = score_gates(traded, meta[win_key]["bh"])
        scored[win_key] = (s, e)
        s.to_csv(OUT / f"orb_trend_{win_key}_scored.csv", index=False)
        print_table(s, f"TREND-FILTERED — {WINDOWS[win_key]['label']} ({win_key})")
        n = len(s)
        print(f"\n  Batch summary [{win_key}]: n={n}  gross>1={int((s['gross_pf']>1).sum())}/{n}  "
              f"net>1={int((s['net_pf']>1).sum())}/{n}  SR>0={int((s['sharpe']>0).sum())}/{n}  "
              f"DSR>0.95={int((s['dsr']>0.95).sum())}/{n}  OOSholds={int(s['oos_holds'].sum())}/{n}  "
              f"notConc(<=60%)={int(s['not_concentrated'].sum())}/{n}  "
              f"extremeConc(>=100%)={int(s['extreme_concentration'].sum())}/{n}  "
              f"beatsBH={int(s['beats_bh'].sum())}/{n}  SURVIVORS={int(s['SURVIVOR'].sum())}/{n}  "
              f"meanGrPF={s['gross_pf'].mean():.3f}  meanSR={s['sharpe'].mean():+.3f}  "
              f"E[maxSR]={e[0]:+.3f} (mu {e[2]:+.3f}, sd {e[3]:.3f}, n={e[1]})")

    for win_key, df in all_unf.items():
        traded = df[df.get("n_trades", pd.Series(dtype=int)).fillna(0) > 0].copy()
        s, e = score_gates(traded, meta[win_key]["bh"])
        s.to_csv(OUT / f"orb_trend_{win_key}_unfiltered_reference.csv", index=False)

    print(f"\n{'='*150}\nFILTER IMPACT — trades removed vs unfiltered, per cell\n{'='*150}")
    for win_key, m in meta.items():
        rm = m["removed"]
        print(f"\n [{win_key}]")
        print(f"  {'inst':>6} {'OR':>3} {'target':>6} {'n_unf':>6} {'n_filt':>6} {'removed':>7} "
              f"{'rm win%':>8} {'kp win%':>8} {'rm meanNetR':>12} {'kp meanNetR':>12}")
        for _, r in rm.sort_values(["instrument", "or_minutes", "target"]).iterrows():
            print(f"  {r['instrument']:>6} {int(r['or_minutes']):>3} {r['target']:>6} "
                  f"{int(r['n_unf']):>6} {int(r['n_filt']):>6} {int(r['n_removed']):>7} "
                  f"{r.get('removed_win_rate', float('nan'))*100:>7.1f}% "
                  f"{r.get('kept_win_rate', float('nan'))*100:>7.1f}% "
                  f"{r.get('removed_mean_netR', float('nan')):>+12.4f} "
                  f"{r.get('kept_mean_netR', float('nan')):>+12.4f}")

    print(f"\n{'='*150}\nOLD (unfiltered, section 10 audited) vs NEW (trend-filtered) — side by side\n{'='*150}")
    for win_key in WINDOWS:
        s_filt, _ = scored[win_key]
        traded_unf = all_unf[win_key][all_unf[win_key].get("n_trades", pd.Series(dtype=int)).fillna(0) > 0].copy()
        s_unf, _ = score_gates(traded_unf, meta[win_key]["bh"])
        n = len(s_filt)
        print(f"\n {WINDOWS[win_key]['label']} ({win_key})")
        print(f"  UNFILTERED (this run's recompute, should match results/orb{'':0}"
              f"{'_pre2018' if win_key=='out_regime' else ''}.csv): "
              f"gross>1={int((s_unf['gross_pf']>1).sum())}/{len(s_unf)}  "
              f"net>1={int((s_unf['net_pf']>1).sum())}/{len(s_unf)}  "
              f"SURVIVORS={int(s_unf['SURVIVOR'].sum())}/{len(s_unf)}  meanGrPF={s_unf['gross_pf'].mean():.3f}  "
              f"meanSR={s_unf['sharpe'].mean():+.3f}")
        print(f"  TREND-FILTERED (new)                                   : "
              f"gross>1={int((s_filt['gross_pf']>1).sum())}/{n}  "
              f"net>1={int((s_filt['net_pf']>1).sum())}/{n}  "
              f"SURVIVORS={int(s_filt['SURVIVOR'].sum())}/{n}  meanGrPF={s_filt['gross_pf'].mean():.3f}  "
              f"meanSR={s_filt['sharpe'].mean():+.3f}")

    total_survivors = sum(int(scored[w][0]["SURVIVOR"].sum()) for w in WINDOWS)
    print(f"\n{'='*150}\nVERDICT\n{'='*150}")
    print(f"  Total trend-filtered SURVIVORS across both windows: {total_survivors}/24")
    print("  Saved: results/orb_trend_in_regime_scored.csv, orb_trend_out_regime_scored.csv,")
    print("         results/orb_trend_*_unfiltered_reference.csv")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
