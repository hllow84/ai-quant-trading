#!/usr/bin/env python3
"""
audit_orb_tiebreak.py — AUDIT 3: quantify the stop-first same-bar tie rule.

For every ORB config (both windows), re-resolve trades with the SAME engine but
under the OPPOSITE tie convention (target-first) and report:
  - how many trades actually had stop AND target hit in the same bar (the only
    trades this assumption can possibly change)
  - net PF under stop-first (current, conservative) vs target-first (optimistic)
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot
from research.metrics import profit_factor
from research.ftmo_engine import de_overlap
from strategies.orb import orb, OR_MINUTES, TARGETS
import run_orb as ro


def simulate_trades_tiebreak(m1_mid, trades, cost_bps, slip_bps_fn, tie_rule="stop"):
    """Copy of ftmo_engine.simulate_trades with an explicit tie_rule for same-bar
    stop+target hits. tie_rule='stop' reproduces the engine exactly.
    tie_rule='target' flips ONLY the bars where i_stop == i_tgt (a true same-bar
    tie); it does not touch bars where the stop or target isolate as strictly
    earlier for the other by construction of a scan starting from index 0."""
    idx = m1_mid.index
    ts_ns = idx.tz_localize(None).values.astype("datetime64[ns]").view("int64")
    lows = m1_mid["mid_low"].to_numpy()
    highs = m1_mid["mid_high"].to_numpy()
    closes = m1_mid["mid_close"].to_numpy()
    spreads = m1_mid["spread"].to_numpy()
    n = len(idx)

    rows = []
    for tr in trades:
        entry_time = tr["entry_time"]
        side = tr["side"]
        entry_mid = float(tr["entry_mid"])
        stop = float(tr["stop"])
        target = float(tr["target"])
        sess_end = tr["session_end"]

        risk = (entry_mid - stop) if side == "long" else (stop - entry_mid)
        if risk <= 0:
            continue

        entry_ns = pd.Timestamp(entry_time).tz_convert(None).value
        end_ns = pd.Timestamp(sess_end).tz_convert(None).value
        start = int(np.searchsorted(ts_ns, entry_ns, side="left"))
        end = int(np.searchsorted(ts_ns, end_ns, side="right"))
        if start >= n or start >= end:
            continue

        w_lo = lows[start:end]
        w_hi = highs[start:end]
        if side == "long":
            stop_mask = w_lo <= stop
            tgt_mask = w_hi >= target
        else:
            stop_mask = w_hi >= stop
            tgt_mask = w_lo <= target
        i_stop = int(np.argmax(stop_mask)) if stop_mask.any() else -1
        i_tgt = int(np.argmax(tgt_mask)) if tgt_mask.any() else -1

        is_true_tie = (i_stop != -1 and i_tgt != -1 and i_stop == i_tgt)

        if i_stop == -1 and i_tgt == -1:
            exit_i = end - 1
            exit_mid = float(closes[exit_i])
            reason = "time"
        elif is_true_tie:
            if tie_rule == "stop":
                exit_i, exit_mid, reason = start + i_stop, stop, "stop"
            else:
                exit_i, exit_mid, reason = start + i_tgt, target, "target"
        elif i_tgt == -1 or (i_stop != -1 and i_stop < i_tgt):
            exit_i, exit_mid, reason = start + i_stop, stop, "stop"
        else:
            exit_i, exit_mid, reason = start + i_tgt, target, "target"

        gross_R = ((exit_mid - entry_mid) if side == "long" else (entry_mid - exit_mid)) / risk

        slip_side = slip_bps_fn(entry_time)
        spread_at_entry = float(spreads[start])
        total_bps = (spread_at_entry / entry_mid) * 1e4 + cost_bps["commission"] + 2.0 * slip_side
        cost_price = total_bps / 1e4 * entry_mid
        cost_R = cost_price / risk
        net_R = gross_R - cost_R

        rows.append({
            "entry_time": entry_time, "exit_time": idx[exit_i], "side": side,
            "reason": reason, "is_true_tie": is_true_tie,
            "gross_R": gross_R, "cost_R": cost_R, "net_R": net_R,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("exit_time").reset_index(drop=True)
    return df


def run_window(label, instruments, cost_bps_map):
    print(f"\n{'='*100}\n{label}\n{'='*100}")
    results = []
    for inst, path in instruments.items():
        if not path.exists():
            print(f"[{inst}] MISSING {path}")
            continue
        spot = load_m1_spot(path)
        m1 = pd.DataFrame(index=spot.index)
        for c in ("open", "high", "low", "close"):
            m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
        m1["spread"] = spot["spread"]
        del spot

        for n_or in OR_MINUTES:
            for target in TARGETS:
                cands = orb(m1, dict(or_minutes=n_or, target=target))
                if not cands:
                    continue
                t_stop = de_overlap(simulate_trades_tiebreak(
                    m1, cands, ro.COST_BPS, ro.slip_bps, tie_rule="stop"))
                t_tgt = de_overlap(simulate_trades_tiebreak(
                    m1, cands, ro.COST_BPS, ro.slip_bps, tie_rule="target"))

                n_ties_stop_kept = int(t_stop["is_true_tie"].sum()) if not t_stop.empty else 0
                n_ties_tgt_kept = int(t_tgt["is_true_tie"].sum()) if not t_tgt.empty else 0

                pf_stop = profit_factor(t_stop["net_R"]) if not t_stop.empty else float("nan")
                pf_tgt = profit_factor(t_tgt["net_R"]) if not t_tgt.empty else float("nan")

                results.append(dict(
                    instrument=inst, or_minutes=n_or, target=target,
                    n_trades_stop=len(t_stop), n_trades_target=len(t_tgt),
                    n_true_ties_in_stop_run=n_ties_stop_kept,
                    n_true_ties_in_target_run=n_ties_tgt_kept,
                    net_pf_stop_first=pf_stop, net_pf_target_first=pf_tgt,
                    d_pf=pf_tgt - pf_stop if np.isfinite(pf_tgt) and np.isfinite(pf_stop) else float("nan"),
                ))
                print(f"  {inst:>6} OR{n_or:>2} {target:<5} n={len(t_stop):>4} "
                      f"ties(stop-run)={n_ties_stop_kept:>3} "
                      f"netPF stop-first={pf_stop:.3f} target-first={pf_tgt:.3f} "
                      f"d={results[-1]['d_pf']:+.4f}")
    return pd.DataFrame(results)


def main():
    in_regime = {
        "NAS100": _ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv",
        "US30": _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",
    }
    out_regime = {
        "NAS100": _ROOT / "data" / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv",
        "US30": _ROOT / "data" / "US30_M1RTH_2013_2017_cfd_dukascopy.csv",
    }
    r1 = run_window("IN REGIME 2018-2025", in_regime, None)
    r2 = run_window("OUT OF REGIME 2013-2017", out_regime, None)
    r1["window"] = "in_regime"
    r2["window"] = "out_regime"
    allr = pd.concat([r1, r2], ignore_index=True)
    out = _ROOT / "results" / "audit_orb_tiebreak.csv"
    allr.to_csv(out, index=False)

    print(f"\n\n{'='*100}\nSUMMARY\n{'='*100}")
    for w, g in allr.groupby("window"):
        total_ties = g["n_true_ties_in_stop_run"].sum()
        total_trades = g["n_trades_stop"].sum()
        mean_pf_stop = g["net_pf_stop_first"].replace([np.inf, -np.inf], np.nan).mean()
        mean_pf_tgt = g["net_pf_target_first"].replace([np.inf, -np.inf], np.nan).mean()
        print(f"  {w}: total trades={total_trades}, true same-bar ties={total_ties} "
              f"({total_ties/total_trades*100:.2f}% of trades)")
        print(f"    mean net PF stop-first={mean_pf_stop:.3f}  target-first={mean_pf_tgt:.3f}  "
              f"d={mean_pf_tgt-mean_pf_stop:+.4f}")
    print(f"\nSaved -> {out}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
