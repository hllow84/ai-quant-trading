#!/usr/bin/env python3
"""
run_orb_vol_regime.py  --  STATE_OF_PLAY section 10 follow-up (§10.9).

QUESTION
--------
Every ORB variant tested so far (§10 plain, §10.1 audit, §10.2 moderate stop,
§10.4 trend filter, §10.5 RETEST + DI, §10.6-10.8 RETEST generalisation) has
died the same way: a 2018-2025 in-regime gross edge that (a) inverts or vanishes
out of regime and (b) is dominated by costs relative to a tight OR-width stop.
The RETEST variant (§10.5) came closest -- XAUUSD OR30/1R: gross PF 1.78, net PF
1.34, net Sharpe +1.14 -- and failed on DSR, on buy-and-hold, and on the
2013-2017 window.

This script tests ONE genuinely different hypothesis, pre-registered:

    A VOLATILITY-REGIME FILTER on the RETEST OR30/1R variant -- only take the
    setup when session realised volatility is ELEVATED (or, tested as the
    inverse, only when it is SUPPRESSED) -- directly targeting the
    cost-to-risk ratio that has killed every ORB variant. A wider OR when
    vol is high => a wider 1R => cost is a smaller fraction of 1R.

WHAT IS FIXED (reused byte-for-byte from §10.5/§10.8, NOT re-derived)
-------------------------------------------------------------------
  * Entry logic: strategies.orb.orb(m1_mid, {or_minutes:30, target:"1R",
    stop_mode:"or_range"}, retest=True, retest_tol_frac=0.10, **ET_SESSION).
    The vol filter NEVER touches orb() -- it removes whole candidate days from
    the list orb() returns, by session date, so entry price / stop / 1R / the
    retest walk are identical to the unfiltered RETEST cell.
  * Resolution: research.ftmo_engine.simulate_trades + de_overlap, 1% fixed-
    fractional risk (RISK_PER_TRADE), one position/day, no pyramiding.
  * Session anchor: 09:30 America/New_York, DST-correct per bar (unchanged for
    FX -- the §10.8 decision: this tests whether the SAME rule set responds to
    a vol filter, not whether an instrument-specific anchor exists).
  * Costs per instrument, each its established model:
      XAUUSD          -- engine legacy $/oz (cost_bps=None, slip_fn=None)
      NAS100/US30/SPX500 -- run_orb.COST_BPS (real spread + 0.35 bps comm)
                            + run_orb.slip_bps (ET-anchored 1.00/0.15 bps/side)
      EURUSD          -- §10.8 model: commission 0.30 bps (FTMO $3/100k lot)
                         + run_orb.slip_bps slippage, UNCHANGED
  * Scoring / honesty gates: run_orb_entry_filters.score_cands, imported and
    called unchanged.

THE VOLATILITY MEASURE (pre-registered, causal)
----------------------------------------------
Session (daily) ATR(14), Wilder RMA, computed on the RTH session bars exactly
as strategies.orb.wilder_dmi_direction builds its daily bars (high = max intra-
session mid_high, low = min mid_low, close = last mid_close). Then:

    ratio_D = ATR14_{D-1} / mean(ATR14_{D-90 .. D-1})

i.e. `(atr / atr.rolling(90).mean()).shift(1)` -- session D is gated ONLY by
ATR history completed strictly before D. Look-ahead: the .shift(1) plus the
rolling window's own right edge at D-1 means session D's own bar never enters
its gate value. Verified by assertion + the runner's statistical guard.

THE GRID (pre-registered)
-------------------------
  Instruments : XAUUSD, EURUSD, NAS100, US30, SPX500   (FX + indices, per brief)
  Windows     : in-regime 2018-2025 (all five);
                out-of-regime 2013-2017 (EURUSD, NAS100, US30 -- REAL 5y window);
                out-of-regime 2017-only stub (XAUUSD, SPX500 -- ONE bull year,
                  NOT a real regime test, flagged exactly as §10.6)
  Filter mode : BASELINE (no filter -- reproduces the §10.5/§10.8 RETEST cell)
                ELEVATED : trade only if ratio > {1.2, 1.5, 2.0}
                SUPPRESSED: trade only if ratio < {0.8, 0.6}
  => 6 cells per instrument-window. 5 inst x 2 windows x 6 = 60 rows.

  NOTE on "threshold 1.0": the brief lists 1.0 as "no filter, baseline". A
  literal `ratio > 1.0` is NOT no-filter -- the ratio is centred near 1.0, so
  it would still drop ~half the days. The BASELINE row here is the true
  unfiltered RETEST cell (reproduction-checked against
  results/orb_entry_filters_scored.csv for XAUUSD-in / NAS100-in/out /
  US30-in/out). Stated, not hidden.

TRIAL COUNT
-----------
NEW cells this batch = the 50 FILTER cells (5 inst x 2 windows x 5 thresholds).
The 10 BASELINE cells reproduce already-counted RETEST OR30/1R results
(§10.5, §10.6, §10.8) and are NOT re-counted.
  PRIOR cumulative (through §30.1) : 1237
  NEW filter cells                 : 50
  NEW CUMULATIVE TOTAL             : 1287
DSR is reported against BOTH a batch structural pool (N=50 filter cells) AND
the full cumulative pool (N=1287, E[max SR] estimated from this batch's own
Sharpe mean/std at N=1287) -- the latter is the primary bar, and it is high
because the search is wide.

Usage:  py -3.14 run_orb_vol_regime.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
from scipy import stats

import run_orb as ro
from research.gold_data import load_m1_spot, aggregate_daily
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe
from strategies.orb import orb, rth_m1, ET
from run_orb_entry_filters import score_cands, BARS_PER_YEAR, CONC_BAR, DSR_BAR, MIN_OOS_TRADES, THIN

D = _ROOT / "data"
RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)
OUT_CSV = RESULTS / "orb_vol_regime.csv"
SCORED_REF = RESULTS / "orb_entry_filters_scored.csv"

PRIOR_CUM_TRIALS = 1237
EULER_GAMMA = 0.5772156649015329

ET_SESSION = dict(session_tz=ET, open_min=9 * 60 + 30, close_min=16 * 60, min_sess_bars=300)
PARAMS = dict(or_minutes=30, target="1R", stop_mode="or_range")

ATR_LEN = 14
AVG_WIN = 90
ELEVATED = [1.2, 1.5, 2.0]
SUPPRESSED = [0.8, 0.6]

EURUSD_COST_BPS = dict(commission=0.30, slip_normal=ro.SLIP_NORMAL_BPS, slip_news=ro.SLIP_OPEN_BPS)

# instrument -> cost model + window files (+ optional date slice + IS/OOS split)
INSTRUMENTS = {
    "XAUUSD": dict(
        cost_bps=None, slip_fn=None,
        windows={
            "in":  dict(file="XAUUSD_M1_2018_2025_spot_dukascopy.csv", split="2023-01-01",
                        real_oos=True),
            "out": dict(file="XAUUSD_M1_2017_spot_dukascopy.csv", split="2017-07-01",
                        real_oos=False, stub="2017-only, ONE bull year -- NOT a real regime test"),
        }),
    "EURUSD": dict(
        cost_bps=EURUSD_COST_BPS, slip_fn=ro.slip_bps,
        windows={
            "in":  dict(file="EURUSD_M1_2018_2025_spot_dukascopy.csv", split="2023-01-01",
                        real_oos=True),
            "out": dict(file="EURUSD_M1_2013_2017_spot_dukascopy.csv", split="2016-01-01",
                        real_oos=True),
        }),
    "NAS100": dict(
        cost_bps=ro.COST_BPS, slip_fn=ro.slip_bps,
        windows={
            "in":  dict(file="NAS100_M1_2018_2025_cfd_dukascopy.csv", split="2023-01-01",
                        real_oos=True),
            "out": dict(file="NAS100_M1RTH_2013_2017_cfd_dukascopy.csv", split="2016-01-01",
                        real_oos=True),
        }),
    "US30": dict(
        cost_bps=ro.COST_BPS, slip_fn=ro.slip_bps,
        windows={
            "in":  dict(file="US30_M1_2018_2025_cfd_dukascopy.csv", split="2023-01-01",
                        real_oos=True),
            "out": dict(file="US30_M1RTH_2013_2017_cfd_dukascopy.csv", split="2016-01-01",
                        real_oos=True),
        }),
    "SPX500": dict(
        cost_bps=ro.COST_BPS, slip_fn=ro.slip_bps,
        windows={
            "in":  dict(file="SPX500_M1_2017_2025_cfd_dukascopy.csv", slice=("2018-01-01", None),
                        split="2023-01-01", real_oos=True),
            "out": dict(file="SPX500_M1_2017_2025_cfd_dukascopy.csv", slice=("2017-01-01", "2017-12-31"),
                        split="2017-07-01", real_oos=False,
                        stub="2017-only, ONE bull year -- NOT a real regime test"),
        }),
}


def load_window(path: Path, date_slice=None):
    spot = load_m1_spot(path)
    if date_slice is not None:
        lo, hi = date_slice
        if lo is not None:
            spot = spot.loc[spot.index >= pd.Timestamp(lo, tz="UTC")]
        if hi is not None:
            spot = spot.loc[spot.index <= pd.Timestamp(hi, tz="UTC") + pd.Timedelta(days=1)]
    daily = aggregate_daily(spot)
    m1 = pd.DataFrame(index=spot.index)
    for c in ("open", "high", "low", "close"):
        m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
    m1["spread"] = spot["spread"]
    m1["volume"] = spot["volume"]
    bh = ro.buy_and_hold(daily)
    return m1, daily.index, bh


def session_atr_ratio(rth: pd.DataFrame, atr_len: int = ATR_LEN, avg_win: int = AVG_WIN) -> pd.Series:
    """Causal session ATR(14) / trailing-90-session-mean(ATR14), indexed by et_date.

    ratio_D = ATR14_{D-1} / mean(ATR14_{D-90..D-1})   -- .shift(1) => session D's
    own bar never enters its own gate value."""
    g = rth.groupby("et_date")
    high = g["mid_high"].max()
    low = g["mid_low"].min()
    close = g["mid_close"].last()
    prev_close = close.shift(1)
    tr = pd.concat([(high - low).abs(), (high - prev_close).abs(),
                    (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0 / atr_len, adjust=False, min_periods=atr_len).mean()
    avg = atr.rolling(avg_win, min_periods=avg_win).mean()
    ratio = (atr / avg).shift(1)
    return ratio


def filter_cands(cands: list[dict], ratio: pd.Series, mode: str, thr: float) -> list[dict]:
    if mode == "baseline":
        return cands
    out = []
    for c in cands:
        v = ratio.get(c["et_date"], np.nan)
        if not np.isfinite(v):
            continue
        if mode == "elevated" and v > thr:
            out.append(c)
        elif mode == "suppressed" and v < thr:
            out.append(c)
    return out


def emax_sr_for_N(mu: float, sigma: float, N: int) -> float:
    if N < 2:
        return mu
    z1 = stats.norm.ppf(1.0 - 1.0 / N)
    z2 = stats.norm.ppf(1.0 - 1.0 / (N * np.e))
    return float(mu + sigma * ((1.0 - EULER_GAMMA) * z1 + EULER_GAMMA * z2))


def dsr_given_emax(sr_best, e_max, n_obs, ann_factor, skew, ekurt) -> float:
    if n_obs is None or n_obs < 4 or not np.isfinite(sr_best):
        return float("nan")
    sr_pp = sr_best / np.sqrt(ann_factor)
    var_pp = (1.0 + 0.5 * sr_pp ** 2 - skew * sr_pp + (ekurt / 4.0) * sr_pp ** 2) / n_obs
    se = float(np.sqrt(max(ann_factor * var_pp, 1e-16)))
    return float(stats.norm.cdf((sr_best - e_max) / se))


def repro_check(instrument, window, n_trades, net_R_total):
    """Baseline cells must reproduce the already-counted RETEST OR30/1R result."""
    try:
        ref = pd.read_csv(SCORED_REF).query(
            f"instrument=='{instrument}' and window=='{window}' and variant=='RETEST' "
            f"and or_minutes==30 and target=='1R'")
    except Exception:
        return "no-ref"
    if ref.empty:
        return "no-ref"
    r = ref.iloc[0]
    ok = (int(r["n_trades"]) == int(n_trades)) and abs(float(r["net_R_total"]) - net_R_total) < 1e-4
    return "OK" if ok else f"MISMATCH(ref n={int(r['n_trades'])} R={float(r['net_R_total']):.3f})"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    W = 160
    print("=" * W)
    print("  ORB VOLATILITY-REGIME FILTER on RETEST OR30/1R  (§10.9)  --  FX + indices, both windows where available")
    print("=" * W)

    rows = []
    for name, cfg in INSTRUMENTS.items():
        for wk, wcfg in cfg["windows"].items():
            path = D / wcfg["file"]
            if not path.exists():
                print(f"  [{name} {wk}] MISSING {path.name} -- skipped", flush=True)
                continue
            m1, daily_index, bh = load_window(path, wcfg.get("slice"))
            rth = rth_m1(m1, ET_SESSION["session_tz"], ET_SESSION["open_min"], ET_SESSION["close_min"])
            ratio = session_atr_ratio(rth)
            # explicit look-ahead assertion on the gate series
            assert ratio.index.is_monotonic_increasing
            cov = float(np.isfinite(ratio).mean())
            split = pd.Timestamp(wcfg["split"], tz="UTC")
            base_cands = orb(m1, PARAMS, retest=True, retest_tol_frac=0.10, **ET_SESSION)
            stub = wcfg.get("stub")
            print(f"\n[{name} {wk}] {len(m1):,} M1 bars {m1.index[0].date()}->{m1.index[-1].date()} | "
                  f"B&H SR {bh['sharpe']:+.2f} maxDD {bh['max_dd']*100:.1f}% | "
                  f"ratio finite on {cov*100:.0f}% of sessions | base RETEST cands={len(base_cands)}"
                  + (f" | OOS-STUB: {stub}" if stub else ""), flush=True)

            cells = [("baseline", np.nan)] + [("elevated", t) for t in ELEVATED] \
                    + [("suppressed", t) for t in SUPPRESSED]
            for mode, thr in cells:
                cands = filter_cands(base_cands, ratio, mode, thr)
                res, _ = score_cands(m1, cands, cfg["cost_bps"], cfg["slip_fn"],
                                     split, daily_index, PARAMS["or_minutes"], ET_SESSION["open_min"])
                label = "baseline (no filter)" if mode == "baseline" else f"{mode} {'>' if mode=='elevated' else '<'} {thr}"
                row = dict(instrument=name, window=wk, real_oos=wcfg["real_oos"],
                           stub=stub or "", mode=mode, thr=(None if mode == "baseline" else thr),
                           label=label, bh_sharpe=bh["sharpe"], bh_max_dd=bh["max_dd"],
                           n_trades=res.get("n_trades", 0), **{k: res.get(k) for k in (
                               "guard", "gross_pf", "net_pf", "sharpe", "skew", "ekurt", "max_dd",
                               "cost_R_mean", "net_R_total", "win_rate", "risk_med_bps", "n_obs",
                               "is_pf", "oos_pf", "is_sharpe", "oos_sharpe", "oos_trades",
                               "top_year_share")})
                if mode == "baseline":
                    row["repro"] = repro_check(name, wk, row["n_trades"], row["net_R_total"] or 0.0)
                else:
                    row["repro"] = ""
                rows.append(row)
                extra = f" repro={row['repro']}" if row["repro"] else ""
                print(f"    {label:<24} n={row['n_trades']:>4} grPF={_f(row['gross_pf'])} "
                      f"netPF={_f(row['net_pf'])} SR={_s(row['sharpe'])} "
                      f"costR%={_f(row['cost_R_mean'],100)} topYr%={_f(row['top_year_share'],100)}"
                      f"{extra}", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    analyze(df)


def _f(x, mult=1.0):
    return "  n/a" if x is None or not np.isfinite(x) else f"{x*mult:6.2f}"


def _s(x):
    return "  n/a" if x is None or not np.isfinite(x) else f"{x:+6.2f}"


def analyze(df: pd.DataFrame):
    W = 160
    traded = df[df["n_trades"].fillna(0) >= 1].copy()
    filt = traded[traded["mode"] != "baseline"].copy()
    n_new = len(df[df["mode"] != "baseline"])
    cum = PRIOR_CUM_TRIALS + n_new

    # ---- DSR pools ----
    srs = filt["sharpe"].to_numpy(dtype=float)
    srs = srs[np.isfinite(srs)]
    mu_b, sd_b = float(np.mean(srs)), float(np.std(srs, ddof=1))
    e_batch, Nb, _, _ = expected_max_sharpe(srs)
    e_cum = emax_sr_for_N(mu_b, sd_b, cum)

    def add_dsr(r):
        nobs = int(r["n_obs"]) if r["n_obs"] and np.isfinite(r["n_obs"]) else 0
        sk = float(r["skew"]) if np.isfinite(r["skew"]) else 0.0
        ek = float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0
        return pd.Series(dict(
            dsr_batch=dsr_given_emax(r["sharpe"], e_batch, nobs, BARS_PER_YEAR, sk, ek),
            dsr_cum=dsr_given_emax(r["sharpe"], e_cum, nobs, BARS_PER_YEAR, sk, ek)))
    traded[["dsr_batch", "dsr_cum"]] = traded.apply(add_dsr, axis=1)

    # ---- cross-window OOS-regime check: does this (inst,mode,thr) also hold in the REAL 2013-2017 window? ----
    def oos_regime(r):
        if r["window"] != "in":
            return np.nan
        m = df[(df["instrument"] == r["instrument"]) & (df["window"] == "out")
               & (df["mode"] == r["mode"]) & (df["thr"].fillna(-1) == (r["thr"] if r["thr"] is not None else -1))]
        if m.empty:
            return np.nan
        o = m.iloc[0]
        if not o["real_oos"]:
            return np.nan          # 2017 stub -> no true OOS
        if not (o["n_trades"] and o["n_trades"] >= MIN_OOS_TRADES):
            return False
        return bool(np.isfinite(o["net_pf"]) and o["net_pf"] > 1.0 and np.isfinite(o["sharpe"]) and o["sharpe"] > 0)
    traded["oos_regime_holds"] = traded.apply(oos_regime, axis=1)

    traded["not_conc"] = traded["top_year_share"].notna() & (traded["top_year_share"] <= CONC_BAR)
    traded["beats_bh"] = traded["sharpe"] > traded["bh_sharpe"]
    traded["thin"] = traded["n_trades"] < THIN
    traded["is_oos_split_holds"] = ((traded["is_pf"] > 1.0) & (traded["oos_pf"] > 1.0)
                                    & (traded["oos_trades"] >= MIN_OOS_TRADES) & (traded["oos_sharpe"] > 0))
    traded["SURVIVOR"] = ((traded["guard"] == "PASS") & (traded["gross_pf"] > 1.0)
                          & (traded["net_pf"] > 1.0) & (traded["sharpe"] > 0)
                          & (traded["dsr_cum"] > DSR_BAR)
                          & (traded["oos_regime_holds"] == True)
                          & traded["not_conc"] & traded["beats_bh"] & ~traded["thin"]
                          & (traded["mode"] != "baseline"))

    traded = traded.sort_values("sharpe", ascending=False, na_position="last").reset_index(drop=True)
    traded.to_csv(RESULTS / "orb_vol_regime_scored.csv", index=False)

    print("\n" + "#" * W)
    print("  TRIAL COUNT & DSR POOL")
    print("#" * W)
    print(f"  PRIOR cumulative (through §30.1) : {PRIOR_CUM_TRIALS}")
    print(f"  NEW filter cells this batch      : {n_new}   (5 instruments x 2 windows x 5 thresholds; 10 baseline cells reproduce §10.5/10.6/10.8, not re-counted)")
    print(f"  NEW CUMULATIVE TOTAL             : {cum}")
    print(f"  batch filter-cell Sharpe dist    : mean {mu_b:+.3f}, sd {sd_b:.3f}, n {len(srs)}")
    print(f"  E[max SR] batch pool  N={Nb:<4}    : {e_batch:+.3f}")
    print(f"  E[max SR] cumulative  N={cum:<4}    : {e_cum:+.3f}   <-- primary DSR bar")

    print("\n" + "#" * W)
    print("  ALL CELLS RANKED BY NET SHARPE")
    print("#" * W)
    hdr = (f"  {'inst':>7} {'win':>4} {'filter':>18} {'n':>5} {'grPF':>6} {'netPF':>6} {'SR':>7} "
           f"{'DSRbat':>7} {'DSRcum':>7} {'maxDD':>7} {'costR%':>7} {'topYr%':>7} {'B&H':>5} "
           f"{'OOSreg':>7} {'SURV':>5}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for _, r in traded.iterrows():
        ty = f"{r['top_year_share']*100:.0f}" if np.isfinite(r["top_year_share"]) else "n/a"
        oreg = {True: "hold", False: "FAIL"}.get(r["oos_regime_holds"], "-")
        print(f"  {r['instrument']:>7} {r['window']:>4} {r['label'][:18]:>18} {int(r['n_trades']):>5} "
              f"{_f(r['gross_pf'])} {_f(r['net_pf'])} {_s(r['sharpe'])} "
              f"{_f(r['dsr_batch'])} {_f(r['dsr_cum'])} {_f(r['max_dd'],100)} "
              f"{_f(r['cost_R_mean'],100)} {ty:>7} {'BEAT' if r['beats_bh'] else 'lose':>5} "
              f"{oreg:>7} {'YES' if r['SURVIVOR'] else '':>5}")

    # ---- filter-effect summary vs each cell's own baseline ----
    print("\n" + "#" * W)
    print("  FILTER EFFECT vs the SAME instrument/window BASELINE  (does the vol filter help at all?)")
    print("#" * W)
    for (inst, wk), g in traded.groupby(["instrument", "window"]):
        base = df[(df["instrument"] == inst) & (df["window"] == wk) & (df["mode"] == "baseline")]
        if base.empty:
            continue
        b = base.iloc[0]
        bsr = b["sharpe"] if np.isfinite(b["sharpe"]) else float("nan")
        bpf = b["net_pf"] if np.isfinite(b["net_pf"]) else float("nan")
        print(f"  {inst} {wk}: baseline netPF {bpf:.3f} SR {bsr:+.2f} n={int(b['n_trades'])}"
              + (f"   [{b['stub']}]" if b["stub"] else ""))
        for _, r in g[g["mode"] != "baseline"].sort_values("thr").iterrows():
            dsr_pf = (r["net_pf"] - bpf) if np.isfinite(r["net_pf"]) and np.isfinite(bpf) else float("nan")
            dsr_sr = (r["sharpe"] - bsr) if np.isfinite(r["sharpe"]) and np.isfinite(bsr) else float("nan")
            print(f"      {r['label']:<20} n={int(r['n_trades']):>4}  netPF {_f(r['net_pf'])} ({dsr_pf:+.3f})  "
                  f"SR {_s(r['sharpe'])} ({dsr_sr:+.2f})  costR% {_f(r['cost_R_mean'],100)}")

    # ---- verdict ----
    print("\n" + "#" * W)
    print("  VERDICT")
    print("#" * W)
    surv = traded[traded["SURVIVOR"]]
    n_netpf = int(((filt["net_pf"] > 1) & np.isfinite(filt["net_pf"])).sum())
    n_srpos = int(((filt["sharpe"] > 0) & np.isfinite(filt["sharpe"])).sum())
    print(f"  Filter cells with net PF > 1     : {n_netpf} / {len(filt)}")
    print(f"  Filter cells with net Sharpe > 0 : {n_srpos} / {len(filt)}")
    print(f"  Filter cells clearing DSR(cum) {DSR_BAR}: {int((traded.loc[traded['mode']!='baseline','dsr_cum'] > DSR_BAR).sum())} / {len(filt)}")
    if len(surv):
        print(f"\n  {len(surv)} cell(s) clear EVERY gate (guard, grossPF>1, netPF>1, SR>0, DSR_cum>{DSR_BAR}, "
              f"OOS-regime holds, not year-conc, beats B&H, not thin):")
        for _, r in surv.iterrows():
            print(f"    >>> {r['instrument']} {r['window']} RETEST OR30/1R + [{r['label']}] : "
                  f"grPF {r['gross_pf']:.3f} netPF {r['net_pf']:.3f} SR {r['sharpe']:+.2f} "
                  f"DSR_cum {r['dsr_cum']:.3f} topYr {r['top_year_share']*100:.0f}%")
        print("\n  *** These are NOT declared survivors. They REQUIRE independent confirmation on an")
        print("      instrument / window NOT used to find them before any trust. ***")
    else:
        print(f"\n  NO cell clears every gate -- no volatility threshold, on any of the 5 instruments,")
        print(f"  in EITHER direction (elevated or suppressed), produces a config that is net-PF>1,")
        print(f"  positive-Sharpe, holds in the real 2013-2017 out-of-regime window, AND clears a DSR")
        print(f"  bar appropriate to the true cumulative trial count (N={cum}, E[max SR] {e_cum:+.2f}).")
        # closest elevated + closest suppressed
        for mode in ("elevated", "suppressed"):
            sub = filt[(filt["mode"] == mode) & ~filt["sharpe"].isna()]
            if sub.empty:
                continue
            best = traded[(traded["mode"] == mode)].sort_values("sharpe", ascending=False).iloc[0]
            fails = []
            for g, ok in [("guard", best["guard"] == "PASS"), ("grossPF>1", best["gross_pf"] > 1),
                          ("netPF>1", best["net_pf"] > 1), ("SR>0", best["sharpe"] > 0),
                          (f"DSRcum>{DSR_BAR}", bool(best["dsr_cum"] > DSR_BAR)),
                          ("OOS-regime", best["oos_regime_holds"] == True),
                          ("not-conc", bool(best["not_conc"])), ("beats-B&H", bool(best["beats_bh"])),
                          ("not-thin", not bool(best["thin"]))]:
                if not ok:
                    fails.append(g)
            print(f"\n  closest {mode.upper()} cell: {best['instrument']} {best['window']} [{best['label']}] "
                  f"SR {best['sharpe']:+.2f} netPF {best['net_pf']:.3f} DSR_cum {best['dsr_cum']:.3f}")
            print(f"     FAILS: {', '.join(fails)}")

    print(f"\n  results -> {OUT_CSV} , {RESULTS/'orb_vol_regime_scored.csv'}")
    print("=" * W)


if __name__ == "__main__":
    main()
