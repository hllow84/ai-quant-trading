"""
momentum_us30_h4_edge_probe.py -- SS64 follow-up: the joint grid in
research/momentum_us30_h4_joint_grid.py found its best cells sitting on
TWO grid edges simultaneously (k_atr=1.5, the lowest tested; R=3.0, the
highest tested), at both N=48 and N=96 (near-tied, Sharpe +0.801/+0.799).
Per this project's standing rule ("follow the gradient past the grid edge
before trusting an edge-hugging result -- never argmax, always confirm a
plateau"), this section extends the grid outward on BOTH edges at the two
tied-best N values to check whether the result keeps improving (edge-
hugging artifact, distrust it) or turns over into a real interior plateau
(confirms it).

Probe: k_atr in {0.75, 1.0, 1.5} (extending down) x R in {3.0, 4.0, 5.0}
(extending up), at N in {48, 96}, H=2N -- 2x3x3=18 cells (k_atr=1.5/R=3.0
repeats the known grid point at each N, not counted as new).
16 new trials.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, load_m1_mid, resample_mid, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.ftmo_engine import simulate_trades, de_overlap, build_daily_returns, equity_from_returns, build_position_series
from research.dsr import deflated_sharpe
from strategies.sweep_families import momentum, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
DATA = _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv"
PRIOR_TRIALS = 1606
NEW_TRIALS = 16
US30_BAH_SHARPE = 0.547  # §43, same data span, for comparison

NS = (48, 96)
K_ATRS = (0.75, 1.0, 1.5)
RS = (3.0, 4.0, 5.0)


def score(m, params, daily_index):
    cands = momentum(m, params, TF_DELTA["H4"])
    for tr in cands:
        tr["session_end"] = pd.Timestamp(tr["session_end"]).tz_convert("UTC") if pd.Timestamp(tr["session_end"]).tz else pd.Timestamp(tr["session_end"]).tz_localize("UTC")
        tr["entry_time"] = pd.Timestamp(tr["entry_time"]).tz_convert("UTC") if pd.Timestamp(tr["entry_time"]).tz else pd.Timestamp(tr["entry_time"]).tz_localize("UTC")
    trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=COST_BPS))
    if trades.empty or len(trades) < 20:
        return None
    pos = build_position_series(trades, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"
    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    return dict(
        n_trades=len(trades), guard=guard,
        gross_pf=profit_factor(trades["gross_R"]), net_pf=profit_factor(trades["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR), max_dd=max_drawdown(equity),
        win_rate=float((trades["net_R"] > 0).mean()),
        daily_ret=daily_ret,
    )


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    m1 = load_m1_mid(DATA)
    daily_index = aggregate_daily(load_m1_spot(DATA)).index
    m = resample_mid(m1, "4h")

    seen = set()
    rows = []
    for N in NS:
        for k_atr in K_ATRS:
            for R in RS:
                key = (N, k_atr, R)
                is_repeat = (k_atr == 1.5 and R == 3.0)
                params = dict(N=N, k_atr=k_atr, R=R, H=2 * N)
                res = score(m, params, daily_index)
                label = f"N{N}_k{k_atr}_R{R}" + (" [repro]" if is_repeat else "")
                if res is None:
                    print(f"{label}: <20 trades, skipped\n")
                    continue
                yr_log = np.log1p(res["daily_ret"]).groupby(res["daily_ret"].index.year).sum()
                ret_yr = np.expm1(yr_log)
                top_yr = float(ret_yr.abs().max() / ret_yr.sum()) if ret_yr.sum() != 0 else float("nan")
                rows.append(dict(label=label, N=N, k_atr=k_atr, R=R, H=2 * N, is_repeat=is_repeat,
                                  n_trades=res["n_trades"], guard=res["guard"],
                                  gross_pf=res["gross_pf"], net_pf=res["net_pf"], sharpe=res["sharpe"],
                                  max_dd=res["max_dd"], win_rate=res["win_rate"], top_year_share=top_yr))
                print(f"--- {label} ---")
                print(f"  n={res['n_trades']} guard={res['guard']} grossPF={res['gross_pf']:.3f} "
                      f"netPF={res['net_pf']:.3f} Sharpe={res['sharpe']:+.3f} maxDD={res['max_dd']*100:.1f}% "
                      f"win={res['win_rate']*100:.1f}% topyr={top_yr*100:.1f}%")

    df = pd.DataFrame(rows)
    out = RESULTS / "momentum_us30_h4_edge_probe.csv"
    df.to_csv(out, index=False)

    df_sorted = df.sort_values("sharpe", ascending=False)
    print("\n=== TOP 5 BY SHARPE (probe cells) ===")
    print(df_sorted.head(5)[["label", "n_trades", "gross_pf", "net_pf", "sharpe", "max_dd", "top_year_share"]].to_string(index=False))

    new_df = df[~df["is_repeat"]]
    print(f"\nnew cells: {len(new_df)}   beat US30 B&H ({US30_BAH_SHARPE:+.3f}): {int((new_df['sharpe'] > US30_BAH_SHARPE).sum())}/{len(new_df)}")

    sharpes = new_df["sharpe"].tolist()
    print(f"\n=== Deflated Sharpe (structural pool: family=momentum_us30_h4_edge_probe, N={len(sharpes)} new trials) ===")
    for _, r in df_sorted.head(6).iterrows():
        if r["is_repeat"]:
            continue
        d = deflated_sharpe(r["sharpe"], sharpes, n_obs=r["n_trades"], ann_factor=BARS_PER_YEAR)
        print(f"  {r['label']}: Sharpe={r['sharpe']:+.3f}  DSR={d['dsr']:.4f}  pool_n={d['pool_n']}")

    print(f"\nSaved {out}")
    print(f"Trial count: {NEW_TRIALS} new. Cumulative N={PRIOR_TRIALS} -> {PRIOR_TRIALS + NEW_TRIALS}")


if __name__ == "__main__":
    main()
