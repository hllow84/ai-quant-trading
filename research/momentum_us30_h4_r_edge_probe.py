"""
momentum_us30_h4_r_edge_probe.py -- SS64 third follow-up: the peak-confirm
grid (research/momentum_us30_h4_peak_confirm.py) found Sharpe still rising
monotonically along the R axis all the way to R=5.0 (the tested edge) at
k_atr=1.25 (Sharpe +1.010, the best cell so far) while the k_atr axis DID
turn over (1.0/0.75 both worse than 1.25 -- a real interior optimum on
that axis, per the earlier edge probe). This section extends R further
outward (R in {6, 7, 8, 10}) at the two best k_atr values (1.25, 1.5),
N=96 fixed, to find where the R axis actually turns over -- or to confirm
it doesn't, in which case the "peak" is an unstable edge-hug (very wide
targets on a fixed 60-bar-ish hold cap are increasingly rarely hit, so
apparent Sharpe gains there are a small-sample artifact, not a real edge)
and should be DISTRUSTED regardless of headline Sharpe. 8 new trials.
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
PRIOR_TRIALS = 1637
NEW_TRIALS = 8
US30_BAH_SHARPE = 0.547

N = 96
K_ATRS = (1.25, 1.5)
RS = (6.0, 7.0, 8.0, 10.0)


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
    n_targets = int((trades["gross_R"] > 0.5 * params["R"]).sum())  # proxy: hit close to full target
    return dict(
        n_trades=len(trades), guard=guard,
        gross_pf=profit_factor(trades["gross_R"]), net_pf=profit_factor(trades["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR), max_dd=max_drawdown(equity),
        win_rate=float((trades["net_R"] > 0).mean()), n_targets=n_targets,
        daily_ret=daily_ret,
    )


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    m1 = load_m1_mid(DATA)
    daily_index = aggregate_daily(load_m1_spot(DATA)).index
    m = resample_mid(m1, "4h")

    rows = []
    for k_atr in K_ATRS:
        for R in RS:
            params = dict(N=N, k_atr=k_atr, R=R, H=2 * N)
            res = score(m, params, daily_index)
            label = f"N{N}_k{k_atr}_R{R}"
            if res is None:
                print(f"{label}: <20 trades, skipped\n")
                continue
            yr_log = np.log1p(res["daily_ret"]).groupby(res["daily_ret"].index.year).sum()
            ret_yr = np.expm1(yr_log)
            top_yr = float(ret_yr.abs().max() / ret_yr.sum()) if ret_yr.sum() != 0 else float("nan")
            rows.append(dict(label=label, N=N, k_atr=k_atr, R=R, H=2 * N,
                              n_trades=res["n_trades"], guard=res["guard"],
                              gross_pf=res["gross_pf"], net_pf=res["net_pf"], sharpe=res["sharpe"],
                              max_dd=res["max_dd"], win_rate=res["win_rate"],
                              n_targets=res["n_targets"], top_year_share=top_yr))
            print(f"--- {label} ---")
            print(f"  n={res['n_trades']} guard={res['guard']} grossPF={res['gross_pf']:.3f} "
                  f"netPF={res['net_pf']:.3f} Sharpe={res['sharpe']:+.3f} maxDD={res['max_dd']*100:.1f}% "
                  f"win={res['win_rate']*100:.1f}% n_near_target={res['n_targets']} topyr={top_yr*100:.1f}%")

    df = pd.DataFrame(rows)
    out = RESULTS / "momentum_us30_h4_r_edge_probe.csv"
    df.to_csv(out, index=False)

    df_sorted = df.sort_values("sharpe", ascending=False)
    print("\n=== ALL CELLS BY SHARPE ===")
    print(df_sorted[["label", "n_trades", "win_rate", "gross_pf", "net_pf", "sharpe", "max_dd", "top_year_share"]].to_string(index=False))

    print(f"\nbeat US30 B&H ({US30_BAH_SHARPE:+.3f}): {int((df['sharpe'] > US30_BAH_SHARPE).sum())}/{len(df)}")

    print(f"\nSaved {out}")
    print(f"Trial count: {NEW_TRIALS} new. Cumulative N={PRIOR_TRIALS} -> {PRIOR_TRIALS + NEW_TRIALS}")


if __name__ == "__main__":
    main()
