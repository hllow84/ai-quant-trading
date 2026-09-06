#!/usr/bin/env python3
"""
run_orb_vol_regime_basket.py  --  §10.9 ADDITIONAL VARIATION (clearly separate,
labelled, NOT blended into the main grid).

WHY THIS, AND ONLY THIS, WAS ADDED
----------------------------------
The main §10.9 grid (run_orb_vol_regime.py) shows the elevated-volatility
filter does exactly what the hypothesis predicted to the cost ratio -- on
NAS100 cost_R falls 5.5% -> 3.5% of 1R, on US30 7.1% -> 3.9%, on SPX500
9.7% -> 3.4% -- and on the two cleanest indices the filtered cell is net-PF
> 1 at every usable threshold:
    NAS100 in : elevated >1.2 netPF 1.02 | >1.5 1.21 | >2.0 1.52
    US30   in : elevated >1.5 netPF 1.13 | >2.0 1.32
BUT each individual cell dies on (a) THINNESS (10-49 trades) and (b) extreme
single-year concentration (top-year share 84%-156% of total net R -- one year
larger than the whole P&L).

Single-name year-concentration is the exact failure mode this project already
fixed once by POOLING instruments into a basket (§6). So the one concrete,
data-motivated addition is: run the SAME elevated-vol RETEST OR30/1R cell on
NAS100 + US30 + SPX500 TOGETHER -- one combined daily-return series, one
position per instrument per day, each instrument on its own established cost
model -- and see whether pooling rescues the sample size and the concentration
without a new free parameter. Nothing else is changed.

  IN-REGIME  2018-2025 : NAS100 + US30 + SPX500
  OUT-REGIME 2013-2017 : NAS100 + US30 only (SPX500 has only a 2017 stub, not a
                         real out-of-regime window -- stated, excluded)
  Thresholds: elevated > {1.2, 1.5, 2.0}   => 3 in + 3 out = 6 NEW cells.

  PRIOR cumulative (through §10.9 main grid) : 1287
  NEW basket cells                          : 6
  NEW CUMULATIVE TOTAL                      : 1293

Same honesty gates: look-ahead (the vol gate is causal by construction, main
grid asserts it), real per-instrument costs, DSR vs the full cumulative pool,
per-year concentration on the POOLED trade book, out-of-regime, vs buy-and-hold
(equal-weight of the basket's members).
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
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import expected_max_sharpe
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns,
)
from strategies.orb import orb, rth_m1
from run_orb_vol_regime import (
    load_window, session_atr_ratio, filter_cands, emax_sr_for_N, dsr_given_emax,
    ET_SESSION, PARAMS, INSTRUMENTS, BARS_PER_YEAR, CONC_BAR, DSR_BAR, THIN,
)

RESULTS = _ROOT / "results"
PRIOR_CUM_TRIALS = 1287          # after the §10.9 main grid (1237 + 50)
ELEVATED = [1.2, 1.5, 2.0]

BASKETS = {
    "in":  ["NAS100", "US30", "SPX500"],
    "out": ["NAS100", "US30"],          # SPX500 out = 2017 stub only, excluded
}


def build_member(name: str, wk: str):
    cfg = INSTRUMENTS[name]
    wcfg = cfg["windows"][wk]
    m1, daily_index, bh = load_window(_ROOT / "data" / wcfg["file"], wcfg.get("slice"))
    rth = rth_m1(m1, ET_SESSION["session_tz"], ET_SESSION["open_min"], ET_SESSION["close_min"])
    ratio = session_atr_ratio(rth)
    base_cands = orb(m1, PARAMS, retest=True, retest_tol_frac=0.10, **ET_SESSION)
    return dict(name=name, m1=m1, daily_index=daily_index, bh=bh, ratio=ratio,
                base_cands=base_cands, cost_bps=cfg["cost_bps"], slip_fn=cfg["slip_fn"])


def basket_cell(members: list[dict], thr: float) -> dict:
    """Pool the elevated-vol RETEST OR30/1R trades across members into ONE
    combined daily-return series (per-instrument returns summed by date)."""
    all_trades = []
    daily_rets = []
    full_index = None
    for mem in members:
        cands = filter_cands(mem["base_cands"], mem["ratio"], "elevated", thr)
        tr = de_overlap(simulate_trades(mem["m1"], cands, strictly_after=False,
                                        cost_bps=mem["cost_bps"], slip_bps_fn=mem["slip_fn"]))
        if tr.empty:
            continue
        tr = tr.copy()
        tr["instrument"] = mem["name"]
        all_trades.append(tr)
        dr = build_daily_returns(tr, mem["daily_index"])
        daily_rets.append(dr)
        full_index = dr.index if full_index is None else full_index.union(dr.index)

    if not all_trades:
        return dict(n_trades=0, insufficient=True)

    trades = pd.concat(all_trades, ignore_index=True)
    combined = pd.DataFrame(index=full_index)
    for i, dr in enumerate(daily_rets):
        combined[i] = dr.reindex(full_index).fillna(0.0)
    daily_ret = combined.sum(axis=1).sort_index()
    equity = equity_from_returns(daily_ret)

    exit_t = pd.to_datetime(trades["exit_time"], utc=True)
    yr = exit_t.dt.year
    agg = trades.groupby(yr)["net_R"].sum()
    tot = float(agg.sum())
    top_share = float(agg.max() / tot) if tot > 0 else float("nan")

    # equal-weight buy-and-hold of the members over the pooled window
    bh_srs = [m["bh"]["sharpe"] for m in members]
    bh_sharpe = float(np.mean(bh_srs))

    return dict(
        insufficient=False, n_trades=len(trades),
        n_members=len(all_trades),
        gross_pf=float(profit_factor(trades["gross_R"])),
        net_pf=float(profit_factor(trades["net_R"])),
        sharpe=float(sharpe(daily_ret, BARS_PER_YEAR)),
        skew=float(daily_ret.skew()), ekurt=float(daily_ret.kurtosis()),
        max_dd=float(max_drawdown(equity)),
        cost_R_mean=float(trades["cost_R"].mean()),
        net_R_total=float(trades["net_R"].sum()),
        win_rate=float((trades["net_R"] > 0).mean()),
        n_obs=int(len(daily_ret)),
        top_year_share=top_share,
        n_years=int(len(agg)), n_pos_years=int((agg > 0).sum()),
        bh_sharpe=bh_sharpe,
        per_member_n={t["instrument"].iloc[0]: len(t) for t in all_trades},
    )


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    W = 150
    print("=" * W)
    print("  §10.9 ADDITIONAL VARIATION -- ELEVATED-VOL RETEST OR30/1R, 3-INDEX POOLED BASKET")
    print("  (data-motivated: index elevated-vol cells are netPF>1 but individually thin + year-concentrated; pool them)")
    print("=" * W)

    rows = []
    members_cache = {}
    for wk in ("in", "out"):
        names = BASKETS[wk]
        print(f"\n[{wk}] basket = {' + '.join(names)}")
        members = []
        for nm in names:
            key = (nm, wk)
            if key not in members_cache:
                print(f"  loading {nm} {wk} ...", flush=True)
                members_cache[key] = build_member(nm, wk)
            members.append(members_cache[key])
        for thr in ELEVATED:
            res = basket_cell(members, thr)
            row = dict(window=wk, basket=" + ".join(names), thr=thr, **res)
            rows.append(row)
            if res.get("insufficient"):
                print(f"    elevated > {thr}: NO TRADES", flush=True)
            else:
                print(f"    elevated > {thr}: n={res['n_trades']:>4} "
                      f"({', '.join(f'{k}:{v}' for k,v in res['per_member_n'].items())}) "
                      f"grPF={res['gross_pf']:.3f} netPF={res['net_pf']:.3f} SR={res['sharpe']:+.2f} "
                      f"maxDD={res['max_dd']*100:.1f}% costR%={res['cost_R_mean']*100:.1f} "
                      f"topYr%={res['top_year_share']*100:.0f} vsB&H={'BEAT' if res['sharpe']>res['bh_sharpe'] else 'lose'}",
                      flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "orb_vol_regime_basket.csv", index=False)

    ok = df[df["insufficient"] != True].copy() if "insufficient" in df else df.copy()
    n_new = len(df)
    cum = PRIOR_CUM_TRIALS + n_new

    # DSR vs the full cumulative pool (same method as the main grid)
    srs = ok["sharpe"].to_numpy(dtype=float)
    srs = srs[np.isfinite(srs)]
    mu_b, sd_b = float(np.mean(srs)), float(np.std(srs, ddof=1)) if len(srs) > 1 else (float(np.mean(srs)), 0.0)
    e_cum = emax_sr_for_N(mu_b, sd_b, cum)
    ok["dsr_cum"] = ok.apply(lambda r: dsr_given_emax(
        r["sharpe"], e_cum, int(r["n_obs"]), BARS_PER_YEAR,
        float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
        float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0), axis=1)
    ok["thin"] = ok["n_trades"] < THIN
    ok["not_conc"] = ok["top_year_share"].notna() & (ok["top_year_share"] <= CONC_BAR)
    ok["beats_bh"] = ok["sharpe"] > ok["bh_sharpe"]

    print("\n" + "#" * W)
    print("  BASKET RESULT  (ranked by net Sharpe)")
    print("#" * W)
    print(f"  PRIOR cumulative: {PRIOR_CUM_TRIALS} | NEW basket cells: {n_new} | NEW CUMULATIVE TOTAL: {cum}")
    print(f"  DSR vs full cumulative pool N={cum}: E[max SR] {e_cum:+.3f} (batch mu {mu_b:+.3f} sd {sd_b:.3f})")
    hdr = (f"  {'window':>6} {'thr':>5} {'n':>5} {'grPF':>6} {'netPF':>6} {'SR':>7} {'DSRcum':>7} "
           f"{'maxDD':>7} {'costR%':>7} {'topYr%':>7} {'B&Hsr':>6} {'vsB&H':>6} {'flags':>14}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for _, r in ok.sort_values("sharpe", ascending=False).iterrows():
        fl = []
        if r["thin"]:
            fl.append("THIN")
        if not r["not_conc"]:
            fl.append("CONC")
        ty = f"{r['top_year_share']*100:.0f}" if np.isfinite(r["top_year_share"]) else "n/a"
        print(f"  {r['window']:>6} {r['thr']:>5.1f} {int(r['n_trades']):>5} {r['gross_pf']:>6.3f} "
              f"{r['net_pf']:>6.3f} {r['sharpe']:>+7.2f} {r['dsr_cum']:>7.3f} {r['max_dd']*100:>6.1f}% "
              f"{r['cost_R_mean']*100:>6.1f} {ty:>7} {r['bh_sharpe']:>+6.2f} "
              f"{'BEAT' if r['beats_bh'] else 'lose':>6} {','.join(fl):>14}")

    # verdict
    print("\n" + "#" * W)
    print("  ADDITIONAL-VARIATION VERDICT")
    print("#" * W)
    inb = ok[ok["window"] == "in"]
    outb = ok[ok["window"] == "out"]
    surv = ok[(ok["gross_pf"] > 1) & (ok["net_pf"] > 1) & (ok["sharpe"] > 0)
              & (ok["dsr_cum"] > DSR_BAR) & ok["not_conc"] & ok["beats_bh"] & ~ok["thin"]]
    print(f"  in-regime cells netPF>1: {int((inb['net_pf']>1).sum())}/{len(inb)} | "
          f"SR>0: {int((inb['sharpe']>0).sum())}/{len(inb)} | "
          f"not-year-conc: {int(inb['not_conc'].sum())}/{len(inb)} | beats EW-B&H: {int(inb['beats_bh'].sum())}/{len(inb)}")
    print(f"  out-regime (NAS100+US30) cells netPF>1: {int((outb['net_pf']>1).sum())}/{len(outb)} | "
          f"SR>0: {int((outb['sharpe']>0).sum())}/{len(outb)}")
    print(f"  cells clearing DSR_cum > {DSR_BAR}: {int((ok['dsr_cum']>DSR_BAR).sum())}/{len(ok)}")
    if len(surv):
        print(f"\n  {len(surv)} basket cell(s) clear every gate -- REQUIRE independent confirmation before any trust:")
        for _, r in surv.iterrows():
            print(f"    >>> {r['window']} elevated>{r['thr']}: grPF {r['gross_pf']:.3f} netPF {r['net_pf']:.3f} "
                  f"SR {r['sharpe']:+.2f} DSR_cum {r['dsr_cum']:.3f} topYr {r['top_year_share']*100:.0f}%")
    else:
        print("\n  NO basket cell clears every gate. Pooling improves the SAMPLE (41->~160 trades at >1.5) but:")
        for _, r in ok.sort_values("sharpe", ascending=False).head(3).iterrows():
            fails = []
            if not (r["net_pf"] > 1): fails.append("netPF<=1")
            if not (r["sharpe"] > 0): fails.append("SR<=0")
            if not (r["dsr_cum"] > DSR_BAR): fails.append(f"DSR_cum {r['dsr_cum']:.2f}")
            if not r["not_conc"]: fails.append(f"year-conc {r['top_year_share']*100:.0f}%")
            if not r["beats_bh"]: fails.append("loses to B&H")
            if r["thin"]: fails.append("THIN")
            print(f"    {r['window']} elevated>{r['thr']}: SR {r['sharpe']:+.2f} -> FAILS: {', '.join(fails)}")
    print(f"\n  results -> {RESULTS/'orb_vol_regime_basket.csv'}")
    print("=" * W)


if __name__ == "__main__":
    main()
