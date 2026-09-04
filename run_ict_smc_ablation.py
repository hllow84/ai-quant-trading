#!/usr/bin/env python3
"""
run_ict_smc_ablation.py -- section 29.x. Isolates which of the FOUR section-29
filters, if any, carries real signal ON ITS OWN.

Deferred in section 29 ("An ablation isolating which filter matters most is
deliberately deferred to section 29.x"). This is that ablation.

WHAT IS REUSED UNCHANGED:
    - the section-28 engine (run_ict_smc): per-bar ICT state machine mechanics,
      per-instrument cost model, min-stop floor max(20 ticks, 5 bps of price)
      and its fill-gap re-check, next-bar-open fills, sequential no_pos gate
      (run_one_window), $100k / 1% compounding, ruin diagnostic, look-ahead
      guard, per-year concentration, buy-and-hold comparison.
    - ALL FOUR filter definitions, byte-identical, imported from
      run_ict_smc_selective:
          F1 sweep quality     -- swept level within 10 bps of the last
                                  240-bar (4h) extreme
          F2 HTF context       -- daily 50 EMA bias PLUS daily 200 EMA stack
                                  (close vs EMA200 and EMA50 vs EMA200)
          F3 selectivity cap   -- 1 entry / rolling 7 days per instrument
                                  PLUS a 2.0x displacement conviction floor
                                  (both parts, exactly as section 29 defined
                                  "FILTER 3")
          F4 level significance-- swept level near prior-day H/L, or touched
                                  >=3x in the last 480 bars, or a round number

METHOD: the section-29 stateful loop, re-parameterised with four on/off flags.
Each of the four gates is wrapped in `if <flag>` and is otherwise the SAME
expression as in run_ict_smc_selective.run_state_machine_selective. With all
four flags OFF the loop is byte-equivalent to run_ict_smc.run_state_machine --
verified at run time by asserting the baseline trade count per cell matches
results/ict_smc.csv (the section-28 result) exactly.

GRID (6 variants x the SAME 7 a priori cells as section 28/29):
    baseline    -- all flags off  (= section 28, reference, NOT a new trial)
    F1 only     -- sweep quality alone on top of baseline
    F2 only     -- HTF context alone
    F3 only     -- selectivity cap alone (weekly cap + conviction floor)
    F4 only     -- level significance alone
    ALL FOUR    -- section 29, reference, NOT a new trial

NEW TRIALS: 4 individual filters x 7 cells = 28.  (baseline and ALL-FOUR are
already-tested references.)  Cumulative carried from section 29 (N=1105) -> 1133.

HEADLINE QUESTION: does any single filter, applied ALONE, improve the RAW
BEFORE-COST gross profit factor over the unfiltered section-28 baseline,
averaged across the 4 instruments (the 4 in-regime cells)?  Section 29 found
gross PF got WORSE on several cells when all four were combined -- so the
gross-PF column is the one that matters here.  If a single filter shows a
genuine isolated gross-edge improvement it is named explicitly.  If none do,
that is stated plainly as the complete answer.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

import run_ict_smc as base
import run_ict_smc_selective as sel
from run_ict_smc import (
    load_dukas_mid, load_crypto_mid, run_one_window, cell_stats, bh_dollars,
    MINTICK, MIN_STOP_TICKS, MIN_STOP_BPS, OB_MAX_BARS, OB_SCAN_BARS,
    SWEEP_WINDOW, RR_RATIO, START_CAP, BARS_PER_YEAR, CONC_BAR,
    DATA, RESULTS, CELLS,
)
from run_ict_smc_selective import (
    compute_state_selective, _level_significant, apply_selectivity_cap,
    SIG_SWING_LOOKBACK, SWEEP_EXTREME_TOL_BPS, HTF_EMA_LONG, DISP_CONVICTION_MIN,
    TOUCH_LOOKBACK,
)
from research.ftmo_engine import RISK_PER_TRADE
from research.metrics import profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe

PRIOR_TRIALS = 1105          # cumulative after section 29
NEW_TRIALS = 28             # 4 individual filters x 7 cells (baseline + all-four are references)


# ---------------------------------------------------------------------------
# section-29 stateful loop, re-parameterised with 4 on/off flags.
# Every gate expression is IDENTICAL to
# run_ict_smc_selective.run_state_machine_selective; only the `if <flag>`
# wrappers are added. All flags False  ==  run_ict_smc.run_state_machine.
# ---------------------------------------------------------------------------
def run_state_machine_flagged(m1: pd.DataFrame, inst: str,
                              use_q: bool, use_htf: bool, use_conv: bool, use_lvl: bool) -> pd.DataFrame:
    mintick = MINTICK[inst]
    st = compute_state_selective(m1, inst)
    n = len(m1)
    close, open_, high, low = st["close"], st["open_"], st["high"], st["low"]
    bullish_bias, bearish_bias, mkt_str = st["bullish_bias"], st["bearish_bias"], st["mkt_str"]
    bull_sweep, bear_sweep = st["bull_sweep"], st["bear_sweep"]
    bull_disp, bear_disp = st["bull_disp"], st["bear_disp"]
    bull_fvg_new, bear_fvg_new = st["bull_fvg_new"], st["bear_fvg_new"]
    in_kz = st["in_kz"]
    lowest10, highest10 = st["lowest10"], st["highest10"]
    last_sh_arr, last_sl_arr = st["last_sh_arr"], st["last_sl_arr"]
    sig_low, sig_high = st["sig_low"], st["sig_high"]
    htf_long_ok, htf_short_ok = st["htf_long_ok"], st["htf_short_ok"]
    disp_ratio = st["disp_ratio"]
    pdh, pdl = st["pdh"], st["pdl"]
    step = st["round_step"]

    buf = mintick * 5
    tol_ext = SWEEP_EXTREME_TOL_BPS / 1e4

    awaiting_bull = awaiting_bear = False
    bull_sw_bar = bear_sw_bar = -1
    bull_ob_hi = bull_ob_lo = np.nan
    bear_ob_hi = bear_ob_lo = np.nan
    bull_ob_on = bear_ob_on = False
    bull_ob_age = bear_ob_age = 0
    bull_fvg_armed = bear_fvg_armed = False
    bull_fvg_arm_age = bear_fvg_arm_age = 0
    bull_arm_disp = bear_arm_disp = 0.0
    bfvg: list[tuple[float, float]] = []
    sfvg: list[tuple[float, float]] = []

    cnt = dict(sweep=0, rej_quality=0, rej_levelsig=0, rej_htf=0, rej_conviction=0, rej_minstop=0)

    raw_long = np.zeros(n, dtype=bool)
    raw_short = np.zeros(n, dtype=bool)
    sl_long_arr = np.full(n, np.nan); tp_long_arr = np.full(n, np.nan)
    sl_short_arr = np.full(n, np.nan); tp_short_arr = np.full(n, np.nan)

    for i in range(2, n):
        # ---- sweep arming -- F1 (quality) and F4 (significance), each flag-gated ----
        if bull_sweep[i]:
            cnt["sweep"] += 1
            lvl = last_sl_arr[i]
            q_ok = (not use_q) or (np.isfinite(sig_low[i]) and np.isfinite(lvl) and lvl <= sig_low[i] * (1 + tol_ext))
            if not q_ok:
                cnt["rej_quality"] += 1
            else:
                if use_lvl:
                    seg = low[max(i - TOUCH_LOOKBACK, 0):i]
                    lvl_ok = _level_significant(lvl, i, seg, pdh[i], pdl[i], step)
                else:
                    lvl_ok = True
                if not lvl_ok:
                    cnt["rej_levelsig"] += 1
                else:
                    awaiting_bull = True
                    bull_sw_bar = i
        if bear_sweep[i]:
            cnt["sweep"] += 1
            lvl = last_sh_arr[i]
            q_ok = (not use_q) or (np.isfinite(sig_high[i]) and np.isfinite(lvl) and lvl >= sig_high[i] * (1 - tol_ext))
            if not q_ok:
                cnt["rej_quality"] += 1
            else:
                if use_lvl:
                    seg = high[max(i - TOUCH_LOOKBACK, 0):i]
                    lvl_ok = _level_significant(lvl, i, seg, pdh[i], pdl[i], step)
                else:
                    lvl_ok = True
                if not lvl_ok:
                    cnt["rej_levelsig"] += 1
                else:
                    awaiting_bear = True
                    bear_sw_bar = i

        if awaiting_bull and (i - bull_sw_bar) > SWEEP_WINDOW:
            awaiting_bull = False
        if awaiting_bear and (i - bear_sw_bar) > SWEEP_WINDOW:
            awaiting_bear = False

        # ---- OB creation + FVG arming (UNCHANGED mechanics) ----
        if awaiting_bull and bull_disp[i]:
            awaiting_bull = False
            lim = max(i - OB_SCAN_BARS, 0)
            for k in range(i - 1, lim - 1, -1):
                if close[k] < open_[k]:
                    bull_ob_hi, bull_ob_lo = open_[k], close[k]
                    bull_ob_on, bull_ob_age = True, 0
                    break
            bull_fvg_armed, bull_fvg_arm_age = True, 0
            bull_arm_disp = disp_ratio[i] if np.isfinite(disp_ratio[i]) else 0.0

        if awaiting_bear and bear_disp[i]:
            awaiting_bear = False
            lim = max(i - OB_SCAN_BARS, 0)
            for k in range(i - 1, lim - 1, -1):
                if close[k] > open_[k]:
                    bear_ob_hi, bear_ob_lo = close[k], open_[k]
                    bear_ob_on, bear_ob_age = True, 0
                    break
            bear_fvg_armed, bear_fvg_arm_age = True, 0
            bear_arm_disp = disp_ratio[i] if np.isfinite(disp_ratio[i]) else 0.0

        # ---- OB aging / FVG arm aging / new FVG registration (UNCHANGED) ----
        if bull_ob_on:
            bull_ob_age += 1
            if close[i] < bull_ob_lo or bull_ob_age > OB_MAX_BARS:
                bull_ob_on = False
        if bear_ob_on:
            bear_ob_age += 1
            if close[i] > bear_ob_hi or bear_ob_age > OB_MAX_BARS:
                bear_ob_on = False
        if bull_fvg_armed:
            bull_fvg_arm_age += 1
            if bull_fvg_arm_age > OB_MAX_BARS:
                bull_fvg_armed = False
        if bear_fvg_armed:
            bear_fvg_arm_age += 1
            if bear_fvg_arm_age > OB_MAX_BARS:
                bear_fvg_armed = False
        if bull_fvg_new[i]:
            bfvg.insert(0, (high[i - 2], low[i]))
            if len(bfvg) > 3:
                bfvg.pop()
        if bear_fvg_new[i]:
            sfvg.insert(0, (low[i - 2], high[i]))
            if len(sfvg) > 3:
                sfvg.pop()

        c = close[i]
        in_bull_fvg = any(lo <= c <= hi for lo, hi in bfvg)
        in_bear_fvg = any(lo <= c <= hi for lo, hi in sfvg)
        in_bull_ob = bull_ob_on and (bull_ob_lo <= c <= bull_ob_hi)
        in_bear_ob = bear_ob_on and (bear_ob_lo <= c <= bear_ob_hi)

        min_stop = max(MIN_STOP_TICKS * mintick, MIN_STOP_BPS * c / 1e4)

        # ---- LONG entry: base conditions + F2 (htf) + F3 conviction floor, each flag-gated ----
        if bullish_bias[i] and mkt_str[i] == 1 and in_kz[i] and (in_bull_ob or (bull_fvg_armed and in_bull_fvg)):
            if use_htf and not htf_long_ok[i]:
                cnt["rej_htf"] += 1
            elif use_conv and bull_arm_disp < DISP_CONVICTION_MIN:
                cnt["rej_conviction"] += 1
            else:
                sl = (bull_ob_lo if bull_ob_on else lowest10[i]) - buf
                if (c - sl) >= min_stop:
                    raw_long[i] = True
                    sl_long_arr[i] = sl
                    tp_long_arr[i] = c + (c - sl) * RR_RATIO
                else:
                    cnt["rej_minstop"] += 1

        if bearish_bias[i] and mkt_str[i] == -1 and in_kz[i] and (in_bear_ob or (bear_fvg_armed and in_bear_fvg)):
            if use_htf and not htf_short_ok[i]:
                cnt["rej_htf"] += 1
            elif use_conv and bear_arm_disp < DISP_CONVICTION_MIN:
                cnt["rej_conviction"] += 1
            else:
                sl = (bear_ob_hi if bear_ob_on else highest10[i]) + buf
                if (sl - c) >= min_stop:
                    raw_short[i] = True
                    sl_short_arr[i] = sl
                    tp_short_arr[i] = c - (sl - c) * RR_RATIO
                else:
                    cnt["rej_minstop"] += 1

    out = pd.DataFrame({
        "raw_long": raw_long, "raw_short": raw_short,
        "sl_long": sl_long_arr, "tp_long": tp_long_arr,
        "sl_short": sl_short_arr, "tp_short": tp_short_arr,
    }, index=m1.index)
    out.attrs["cnt"] = cnt
    return out


VARIANTS = [
    # key,        label,                              q,     htf,   conv,  lvl,   cap,   is_new_trial
    ("baseline",  "baseline (sec 28, unfiltered)",    False, False, False, False, False, False),
    ("F1",        "F1 sweep-quality ONLY",            True,  False, False, False, False, True),
    ("F2",        "F2 HTF-context ONLY",              False, True,  False, False, False, True),
    ("F3",        "F3 selectivity-cap ONLY",          False, False, True,  False, True,  True),
    ("F4",        "F4 level-significance ONLY",       False, False, False, True,  False, True),
    ("ALL4",      "ALL FOUR (sec 29, reference)",     True,  True,  True,  True,  True,  False),
]

IN_REGIME_INSTS = ["XAUUSD", "EURUSD", "SPX500", "BTCUSDT"]   # the 4 in-regime cells


def main() -> None:
    W = 128
    print("=" * W)
    print("  ICT SMC -- SECTION 29.x FILTER ABLATION: each of the 4 section-29 filters applied ALONE on the sec-28 engine")
    print("  Headline column = GROSS PF (before costs). Section 29 found gross PF got WORSE when all four were combined.")
    print("=" * W)

    s28 = pd.read_csv(RESULTS / "ict_smc.csv").set_index("label")

    _file_cache: dict[str, pd.DataFrame] = {}
    _sig_cache: dict[tuple[str, str], pd.DataFrame] = {}
    rows = []
    guard_rows = []
    baseline_check = []

    for vkey, vlabel, q, htf, conv, lvl, cap, is_new in VARIANTS:
        print(f"\n{'#' * W}\n  VARIANT: {vlabel}   (q={q} htf={htf} conv={conv} lvl={lvl} cap={cap})\n{'#' * W}", flush=True)
        for cell in CELLS:
            fpath = DATA / cell["file"]
            fk = cell["file"]
            if fk not in _file_cache:
                print(f"[{cell['inst']}] loading {cell['file']} ...", flush=True)
                m1 = load_crypto_mid(fpath) if cell["kind"] == "crypto" else load_dukas_mid(fpath)
                print(f"[{cell['inst']}] {len(m1):,} bars, {m1.index.min()} -> {m1.index.max()}", flush=True)
                _file_cache[fk] = m1
            m1 = _file_cache[fk]

            sk = (vkey, fk)
            if sk not in _sig_cache:
                sig = run_state_machine_flagged(m1, cell["inst"], q, htf, conv, lvl)
                c = sig.attrs["cnt"]
                n_pre = int(sig["raw_long"].sum() + sig["raw_short"].sum())
                if cap:
                    sig, n_fire, n_kept = apply_selectivity_cap(sig)
                    print(f"[{cell['inst']}/{vkey}] raw {n_pre:,} -> after 1-per-7d cap {n_kept:,}  "
                          f"(rej: quality {c['rej_quality']:,}, level-sig {c['rej_levelsig']:,}, "
                          f"htf {c['rej_htf']:,}, conviction {c['rej_conviction']:,})", flush=True)
                else:
                    print(f"[{cell['inst']}/{vkey}] raw signals {n_pre:,}  "
                          f"(rej: quality {c['rej_quality']:,}, level-sig {c['rej_levelsig']:,}, "
                          f"htf {c['rej_htf']:,}, conviction {c['rej_conviction']:,})", flush=True)
                _sig_cache[sk] = sig
            sig = _sig_cache[sk]

            tr = run_one_window(m1, cell["start"], cell["end"], sig, cell["cost_bps"], cell["slip_fn"],
                                f"{vkey}:{cell['label']}", MINTICK[cell["inst"]])
            tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True) if not tr.empty else tr.get("entry_time")
            tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True) if not tr.empty else tr.get("exit_time")

            guard_ok = True
            if not tr.empty:
                for _, rr in tr.head(200).iterrows():
                    pos = m1.index.searchsorted(rr["entry_time"])
                    if pos == 0 or abs(m1["mid_open"].iloc[pos] - rr["entry_mid"]) > 1e-6:
                        guard_ok = False
                        break

            stats = cell_stats(tr)
            bh = bh_dollars(m1, cell["start"], cell["end"])
            rows.append(dict(variant=vkey, vlabel=vlabel, is_new_trial=is_new,
                             inst=cell["inst"], label=cell["label"], regime=cell["regime"],
                             n=stats["n"], win_rate=stats["win_rate"],
                             gross_pf=stats["gross_pf"], net_pf=stats["net_pf"], sharpe=stats["sharpe"],
                             ending_cap=stats["ending_cap"], bh_ending=bh, top_year=stats["top_year"],
                             ruin_trade=stats["ruin_trade"]))
            guard_rows.append((vkey, cell["label"], guard_ok))

            if vkey == "baseline":
                exp_n = int(s28.loc[cell["label"], "n"]) if cell["label"] in s28.index else -1
                exp_pf = float(s28.loc[cell["label"], "gross_pf"]) if cell["label"] in s28.index else float("nan")
                baseline_check.append((cell["label"], stats["n"], exp_n,
                                       stats["gross_pf"], exp_pf))

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "ict_smc_ablation.csv", index=False)

    # ---- baseline reproduction check ----
    print("\n" + "=" * W)
    print("  BASELINE REPRODUCTION CHECK -- all-flags-off must equal section 28 (results/ict_smc.csv) exactly")
    print("=" * W)
    print(f"  {'cell':<56} {'n (this)':>9} {'n (sec28)':>10} {'grossPF (this)':>15} {'grossPF (sec28)':>16} {'match':>7}")
    all_match = True
    for label, n_this, n_exp, pf_this, pf_exp in baseline_check:
        ok = (n_this == n_exp) and (abs(pf_this - pf_exp) < 1e-6)
        all_match = all_match and ok
        print(f"  {label:<56} {n_this:>9,} {n_exp:>10,} {pf_this:>15.4f} {pf_exp:>16.4f} {'OK' if ok else 'DIFF':>7}")
    print(f"\n  Baseline reproduces section 28 exactly on every cell: {'YES' if all_match else '*** NO -- investigate ***'}")

    # ---- FULL GRID: variant x cell ----
    print("\n" + "#" * W)
    print("  FULL GRID -- gross PF / net PF / Sharpe / trades / ending$ vs B&H, per variant per cell")
    print("#" * W)
    for cell in CELLS:
        print(f"\n  --- {cell['label']} ---")
        print(f"    {'variant':<32} {'trades':>7} {'grossPF':>8} {'netPF':>7} {'Sharpe':>8} "
              f"{'end $':>13} {'B&H $':>13} {'beat B&H':>9}")
        sub = df[df["label"] == cell["label"]]
        for _, r in sub.iterrows():
            beat = "YES" if (r["bh_ending"] and r["ending_cap"] > r["bh_ending"]) else "no"
            gp = f"{r['gross_pf']:.3f}" if np.isfinite(r["gross_pf"]) else "n/a"
            npf = f"{r['net_pf']:.3f}" if np.isfinite(r["net_pf"]) else "n/a"
            sh = f"{r['sharpe']:+.2f}" if np.isfinite(r["sharpe"]) else "n/a"
            print(f"    {r['vlabel']:<32} {int(r['n']):>7,} {gp:>8} {npf:>7} {sh:>8} "
                  f"${r['ending_cap']:>11,.0f} ${r['bh_ending']:>11,.0f} {beat:>9}")

    # ---- HEADLINE: mean gross PF across the 4 in-regime instruments, per variant ----
    print("\n" + "#" * W)
    print("  HEADLINE -- does any SINGLE filter improve the RAW BEFORE-COST edge (gross PF)?")
    print("  Mean over the 4 in-regime cells (XAUUSD/EURUSD/SPX500/BTCUSDT 2018-2025). Ranked by gross-PF delta vs baseline.")
    print("#" * W)
    inreg = df[(df["regime"] == "in") & (df["inst"].isin(IN_REGIME_INSTS))]
    base_row = inreg[inreg["variant"] == "baseline"]
    base_gpf = float(base_row["gross_pf"].mean())
    base_npf = float(base_row["net_pf"].mean())
    base_shp = float(base_row["sharpe"].mean())

    summ = []
    for vkey, vlabel, *_ in VARIANTS:
        s = inreg[inreg["variant"] == vkey]
        mean_gpf = float(s["gross_pf"].mean())
        mean_npf = float(s["net_pf"].mean())
        mean_shp = float(s["sharpe"].mean())
        n_beat = int((s["ending_cap"] > s["bh_ending"].fillna(np.inf)).sum())
        n_gpf_up = int((s.set_index("inst")["gross_pf"] >
                        base_row.set_index("inst")["gross_pf"]).sum())
        tot_n = int(s["n"].sum())
        summ.append(dict(vkey=vkey, vlabel=vlabel, mean_gpf=mean_gpf, d_gpf=mean_gpf - base_gpf,
                         mean_npf=mean_npf, mean_shp=mean_shp, n_beat=n_beat,
                         n_gpf_up=n_gpf_up, tot_n=tot_n))
    order = sorted(summ, key=lambda x: -x["d_gpf"])
    print(f"  {'variant':<32} {'mean grossPF':>13} {'d vs base':>11} {'#inst grossPF>base':>19} "
          f"{'mean netPF':>11} {'mean Sharpe':>12} {'#beat B&H':>10} {'trades':>8}")
    for x in order:
        tag = "" if x["vkey"] in ("baseline", "ALL4") else "  <- new"
        print(f"  {x['vlabel']:<32} {x['mean_gpf']:>13.4f} {x['d_gpf']:>+11.4f} {x['n_gpf_up']:>19}/4 "
              f"{x['mean_npf']:>11.4f} {x['mean_shp']:>+12.2f} {x['n_beat']:>8}/4 {x['tot_n']:>8,}{tag}")
    print(f"\n  baseline mean gross PF = {base_gpf:.4f}  |  mean net PF = {base_npf:.4f}  |  mean Sharpe = {base_shp:+.2f}")

    # ---- also: mean gross PF across ALL 7 cells (in + out of regime) ----
    print("\n  Same ranking over ALL 7 cells (in + out of regime):")
    base7 = df[df["variant"] == "baseline"].set_index("label")["gross_pf"]
    rows7 = []
    for vkey, vlabel, *_ in VARIANTS:
        s = df[df["variant"] == vkey].set_index("label")["gross_pf"]
        d = float(s.mean() - base7.mean())
        n_up = int((s > base7).sum())
        rows7.append((vlabel, float(s.mean()), d, n_up))
    for vlabel, mg, d, n_up in sorted(rows7, key=lambda x: -x[2]):
        print(f"    {vlabel:<32} mean grossPF {mg:.4f}   d vs base {d:+.4f}   #cells grossPF>base {n_up}/7")

    # ---- verdict ----
    print("\n" + "#" * W)
    print("  PLAIN VERDICT")
    print("#" * W)
    improvers = [x for x in order if x["vkey"] not in ("baseline", "ALL4") and x["d_gpf"] > 1e-4 and x["n_gpf_up"] >= 3]
    marginal = [x for x in order if x["vkey"] not in ("baseline", "ALL4") and x["d_gpf"] > 1e-4 and x["n_gpf_up"] < 3]
    if improvers:
        for x in improvers:
            print(f"  {x['vlabel']}: mean gross PF {base_gpf:.4f} -> {x['mean_gpf']:.4f} "
                  f"({x['d_gpf']:+.4f}), higher on {x['n_gpf_up']}/4 instruments.")
        print("  --> A single filter DOES lift the raw before-cost edge. See whether it also survives costs "
              "(net PF / Sharpe / vs B&H columns above).")
    elif marginal:
        for x in marginal:
            print(f"  {x['vlabel']}: mean gross PF {x['d_gpf']:+.4f} vs baseline but higher on only "
                  f"{x['n_gpf_up']}/4 instruments -- not a consistent isolated improvement.")
        print("  --> No single filter shows a CONSISTENT isolated gross-edge improvement (a positive mean "
              "driven by 1-2 instruments is not a finding).")
    else:
        print("  NO single filter improves the mean gross PF over the unfiltered section-28 baseline.")
        print("  Neither individually nor combined does any tested filter recover a raw before-cost edge --")
        print("  the ICT SMC entry logic itself carries no edge that these quality/selectivity filters can find.")

    # ---- ruin re-confirmation across variants ----
    print("\n" + "#" * W)
    print("  ACCOUNT-RUIN across variants (trade # at which equity first <= 1% of $100k start; '-' = never)")
    print("#" * W)
    print(f"  {'cell':<40} " + " ".join(f"{v[0]:>9}" for v in VARIANTS))
    for cell in CELLS:
        cells_lbl = cell["label"][:38]
        parts = []
        for vkey, *_ in VARIANTS:
            rr = df[(df["variant"] == vkey) & (df["label"] == cell["label"])]
            rt = rr["ruin_trade"].iloc[0] if len(rr) else None
            parts.append(f"{('#' + str(int(rt))) if (rt is not None and pd.notna(rt)) else '-':>9}")
        print(f"  {cells_lbl:<40} " + " ".join(parts))

    # ---- guard ----
    any_fail = any(not ok for _, _, ok in guard_rows)
    print(f"\n  Look-ahead guard: {'*** FAIL ***' if any_fail else 'PASS on every variant x cell'} "
          f"({len(guard_rows)} checks, first 200 trades each: entry_mid == next bar open).")

    cumulative = PRIOR_TRIALS + NEW_TRIALS
    print(f"\n  NEW TRIALS: {NEW_TRIALS} (4 individual filters x 7 cells; baseline and ALL-FOUR are references).")
    print(f"  Cumulative project trials after this batch: {cumulative} ({PRIOR_TRIALS} prior + {NEW_TRIALS}).")
    print("  saved -> results/ict_smc_ablation.csv, results/ict_smc_ablation_run.log")
    print("=" * W)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
