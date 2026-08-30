#!/usr/bin/env python3
"""
run_orb_rerun.py — AUDIT re-run.

AUDIT-1 (entry timing) found the code ALREADY uses intrabar M1 high/low crossing
for entry, not bar-close confirmation — no fix needed, no fill logic changed.
AUDIT-3 (stop-first tie rule) found ZERO trades across 30,840 resolved trades
(both windows, all 12 cells) where stop and target were hit in the same M1 bar —
the tie convention is provably inert on this data, no fix needed.
AUDIT-4 added ONE new variant: a MODERATE, cost-sensible fixed-bps stop
(strategies/orb.py MODERATE_STOP_BPS=25, stop_mode='moderate'), tested at the
same breadth as the original grid (2 instruments x 2 OR x 3 targets = 12 cells),
alongside the original stop_mode='or_range' 12 cells. This script re-scores all
24 cells on BOTH windows with the SAME gates run_orb.py used: look-ahead guard,
gross PF>1, net PF>1, positive Sharpe, DSR>0.95 (structural pool = this run's own
24 a priori cells), OOS holds, top-year<=60% concentration, beats buy-and-hold.

Nothing about strategies/orb.py's DEFAULT behaviour changed — stop_mode defaults
to 'or_range', so results/orb.csv and orb_pre2018.csv (the original 12-cell runs)
are reproduced byte-identically by run_orb.py / run_orb_pre2018.py; this script
does not touch them.
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
from research.dsr import deflated_sharpe, expected_max_sharpe
from strategies.orb import orb, OR_MINUTES, TARGETS

STOP_MODES = ("or_range", "moderate")


def run_grid(instruments: dict, window_label: str, oos_split: pd.Timestamp) -> tuple[pd.DataFrame, dict]:
    rows = []
    bh = {}
    for inst, (path, cost_bps) in instruments.items():
        if not path.exists():
            print(f"[{inst}] MISSING {path.name}")
            continue
        spot = load_m1_spot(path)
        daily = aggregate_daily(spot)
        daily_index = daily.index
        bh[inst] = ro.buy_and_hold(daily)
        m1 = pd.DataFrame(index=spot.index)
        for c in ("open", "high", "low", "close"):
            m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
        m1["spread"] = spot["spread"]
        del spot

        ro.OOS_SPLIT = oos_split
        for n_or in OR_MINUTES:
            for target in TARGETS:
                for stop_mode in STOP_MODES:
                    p = dict(or_minutes=n_or, target=target, stop_mode=stop_mode)
                    res, tr = ro.score(m1, p, daily_index, cost_bps)
                    rows.append(dict(instrument=inst, window=window_label, **p, **res))
                    print(f"  [{window_label}] {inst:>6} OR={n_or:>2} tgt={target:<5} "
                          f"stop={stop_mode:<9} n={res.get('n_trades', 0):>4} "
                          f"grPF={res.get('gross_pf', float('nan')):.3f} "
                          f"netPF={res.get('net_pf', float('nan')):.3f} "
                          f"SR={res.get('sharpe', float('nan')):+.2f} "
                          f"guard={res.get('guard', '?')[:5]}", flush=True)
    return pd.DataFrame(rows), bh


def score_gates(traded: pd.DataFrame, bh: dict, conc_bar: float = 0.60, dsr_bar: float = 0.95) -> pd.DataFrame:
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
                           & (traded["oos_trades"] >= ro.MIN_OOS_TRADES)
                           & (traded["oos_sharpe"] > 0))
    traded["gross_edge"] = traded["gross_pf"] > 1.0
    traded["not_concentrated"] = (traded["top_year_share"].notna()
                                  & (traded["top_year_share"] <= conc_bar))
    traded["beats_bh"] = traded.apply(
        lambda r: bool(np.isfinite(r["sharpe"]) and r["instrument"] in bh
                       and r["sharpe"] > bh[r["instrument"]]["sharpe"]), axis=1)
    traded["SURVIVOR"] = (traded["gross_edge"] & (traded["net_pf"] > 1.0)
                          & (traded["sharpe"] > 0) & (traded["dsr"] > dsr_bar)
                          & traded["oos_holds"] & traded["not_concentrated"]
                          & traded["beats_bh"] & (traded["guard"] == "PASS"))
    e_struct = expected_max_sharpe(sr_batch)
    return traded, e_struct


def main():
    in_instr = {
        "NAS100": (_ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv", ro.COST_BPS),
        "US30":   (_ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",   ro.COST_BPS),
    }
    out_instr = {
        "NAS100": (_ROOT / "data" / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv", ro.COST_BPS),
        "US30":   (_ROOT / "data" / "US30_M1RTH_2013_2017_cfd_dukascopy.csv",   ro.COST_BPS),
    }

    print("=" * 110)
    print("RE-RUN — 12 original (or_range) + 12 moderate-stop cells, both windows")
    print("=" * 110)
    in_df, in_bh = run_grid(in_instr, "in_regime", pd.Timestamp("2023-01-01", tz="UTC"))
    out_df, out_bh = run_grid(out_instr, "out_regime", pd.Timestamp("2016-01-01", tz="UTC"))

    in_df.to_csv(_ROOT / "results" / "orb_rerun_in.csv", index=False)
    out_df.to_csv(_ROOT / "results" / "orb_rerun_out.csv", index=False)

    in_traded = in_df[in_df.get("n_trades", pd.Series(dtype=int)).fillna(0) > 0].copy()
    out_traded = out_df[out_df.get("n_trades", pd.Series(dtype=int)).fillna(0) > 0].copy()

    in_scored, e_in = score_gates(in_traded, in_bh)
    out_scored, e_out = score_gates(out_traded, out_bh)
    in_scored.to_csv(_ROOT / "results" / "orb_rerun_in_scored.csv", index=False)
    out_scored.to_csv(_ROOT / "results" / "orb_rerun_out_scored.csv", index=False)

    KEYS = ["instrument", "or_minutes", "target", "stop_mode"]
    W = 150
    for label, df in (("IN REGIME 2018-2025", in_scored), ("OUT OF REGIME 2013-2017", out_scored)):
        print(f"\n{'='*W}\n{label}\n{'='*W}")
        print(f"  {'inst':>6} {'OR':>3} {'target':>6} {'stop':>9} {'n':>5} "
              f"{'grPF':>6} {'netPF':>6} {'Sharpe':>7} {'DSR':>5} {'costR%':>7} "
              f"{'top%':>5} {'OOS?':>4} {'B&H?':>5} {'guard':>6}")
        for _, r in df.sort_values(["stop_mode", "instrument", "or_minutes", "target"]).iterrows():
            share = r["top_year_share"]
            print(f"  {r['instrument']:>6} {int(r['or_minutes']):>3} {r['target']:>6} "
                  f"{r['stop_mode']:>9} {int(r['n_trades']):>5} "
                  f"{r['gross_pf']:>6.3f} {r['net_pf']:>6.3f} {r['sharpe']:>+7.2f} "
                  f"{r['dsr']:>5.2f} {r['cost_R_mean']*100:>6.1f}% "
                  + (f"{share*100:>4.0f}%" if np.isfinite(share) else f"{'n/a':>5}")
                  + f" {'YES' if r['oos_holds'] else 'no':>4} "
                  f"{'BEAT' if r['beats_bh'] else 'lose':>5} {r['guard'][:6]:>6}")

    def block_summary(df, label):
        n = len(df)
        print(f"\n  {label}: n={n}  gross>1={int((df['gross_pf']>1).sum())}/{n}  "
              f"net>1={int((df['net_pf']>1).sum())}/{n}  SR>0={int((df['sharpe']>0).sum())}/{n}  "
              f"DSR>0.95={int((df['dsr']>0.95).sum())}/{n}  OOSholds={int(df['oos_holds'].sum())}/{n}  "
              f"notConc={int(df['not_concentrated'].sum())}/{n}  beatsBH={int(df['beats_bh'].sum())}/{n}  "
              f"SURVIVORS={int(df['SURVIVOR'].sum())}/{n}  meanGrPF={df['gross_pf'].mean():.3f}  "
              f"meanSR={df['sharpe'].mean():+.3f}")

    print(f"\n{'='*W}\nOLD vs CORRECTED — side by side\n{'='*W}")
    for window, df in (("IN REGIME", in_scored), ("OUT OF REGIME", out_scored)):
        old = df[df["stop_mode"] == "or_range"]
        new = df[df["stop_mode"] == "moderate"]
        print(f"\n {window}")
        block_summary(old, "OLD (or_range, original 12 cells)")
        block_summary(new, "NEW (moderate stop, 12 cells)")

    print(f"\n{'='*W}\nDSR pools (structural, this run's own 24 a-priori cells per window)\n{'='*W}")
    print(f"  in regime : E[max SR] {e_in[0]:+.3f} (mu {e_in[2]:+.3f}, sd {e_in[3]:.3f}), n={len(in_scored)}")
    print(f"  out regime: E[max SR] {e_out[0]:+.3f} (mu {e_out[2]:+.3f}, sd {e_out[3]:.3f}), n={len(out_scored)}")

    print(f"\nSaved: results/orb_rerun_in_scored.csv, results/orb_rerun_out_scored.csv")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
