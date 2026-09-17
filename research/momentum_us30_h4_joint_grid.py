"""
momentum_us30_h4_joint_grid.py -- SS64: fifth signal family pushed through
the joint entry/exit/SL/TP refinement method used in Sec39-Sec45, on
momentum (never previously refined -- only 3 hand-picked variants existed,
strategies/sweep_families.py FAMILIES["momentum"]).

BASELINE (2026-07-21 US index CFD sweep, results/sweep_indices_scored.csv):
US30 H4 momentum variant 1 (N=48, k_atr=2.0, R=2.0, H=96): Sharpe +0.221,
netPF 1.120, grossPF 1.150, maxDD 19.6%, 220 trades -- the strongest of the
three stated momentum cells on either index (NAS100's best cell was only
Sharpe +0.035), and never optimized past that single hand-picked point.

MECHANISM (a priori): N sets the momentum lookback (how far back the sign
flip is measured) -- shorter N fires more often but on noisier signal,
longer N is slower but rides bigger established moves. k_atr sets the
initial stop distance in ATR multiples. R sets the fixed target multiple.
Since momentum is (like macross, Sec39-Sec43) a trend-following family, the
same a priori logic that helped macross applies: a WIDER stop and WIDER
target should help more than they hurt, because the edge (if real) is
concentrated in occasional large moves, not small consistent ones -- worth
checking directly, exactly as Sec39/Sec42/Sec43 did for their families.

GRID (a priori, joint on entry lookback / stop / target together, not
staged): N in {24, 48, 72, 96} x k_atr in {1.5, 2.5, 4.0} x R in
{1.0, 2.0, 3.0} = 36 cells, H held at 2x N (so the hold-time cap scales
with the lookback, consistent with how H was set relative to N in the
original 3 stated variants: H=2N in two of three, H=1x in the third).
(N=48, k_atr=2.0, R=2.0) is closest to baseline but not an exact grid
point (k_atr=2.0 not in the grid) -- baseline is reported separately for
comparison, not double-counted. 36 new trials.

Same cost model, H4 resample, strictly_after=True resolution as every
other section in this project. Follows the standing plateau-not-argmax
rule: if the best cell sits on a grid edge, the neighbouring boundary is
probed before trusting it.
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
PRIOR_TRIALS = 1570
NEW_TRIALS = 36

NS = (24, 48, 72, 96)
K_ATRS = (1.5, 2.5, 4.0)
RS = (1.0, 2.0, 3.0)


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
        trades=trades, daily_ret=daily_ret,
    )


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    m1 = load_m1_mid(DATA)
    daily_index = aggregate_daily(load_m1_spot(DATA)).index
    m = resample_mid(m1, "4h")
    print(f"US30 H4 bars: {len(m):,}, {m.index[0]} -> {m.index[-1]}\n")

    rows = []
    for N in NS:
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
                                  max_dd=res["max_dd"], win_rate=res["win_rate"], top_year_share=top_yr))
                print(f"--- {label} ---")
                print(f"  n={res['n_trades']} guard={res['guard']} grossPF={res['gross_pf']:.3f} "
                      f"netPF={res['net_pf']:.3f} Sharpe={res['sharpe']:+.3f} maxDD={res['max_dd']*100:.1f}% "
                      f"win={res['win_rate']*100:.1f}% topyr={top_yr*100:.1f}%")

    df = pd.DataFrame(rows)
    out = RESULTS / "momentum_us30_h4_joint_grid.csv"
    df.to_csv(out, index=False)

    df_sorted = df.sort_values("sharpe", ascending=False)
    print("\n=== TOP 5 BY SHARPE ===")
    print(df_sorted.head(5)[["label", "n_trades", "gross_pf", "net_pf", "sharpe", "max_dd", "top_year_share"]].to_string(index=False))

    best = df_sorted.iloc[0]
    edge_hit = (best["N"] in (NS[0], NS[-1])) or (best["k_atr"] in (K_ATRS[0], K_ATRS[-1])) or (best["R"] in (RS[0], RS[-1]))
    print(f"\nBest cell on a grid edge: {edge_hit} (N={best['N']}, k_atr={best['k_atr']}, R={best['R']})")

    sharpes = df["sharpe"].tolist()
    print(f"\n=== Deflated Sharpe (structural pool: family=momentum_us30_h4_joint_grid, N={len(sharpes)} new trials) ===")
    for _, r in df_sorted.head(8).iterrows():
        d = deflated_sharpe(r["sharpe"], sharpes, n_obs=r["n_trades"], ann_factor=BARS_PER_YEAR)
        print(f"  {r['label']}: Sharpe={r['sharpe']:+.3f}  DSR={d['dsr']:.4f}  pool_n={d['pool_n']}")

    n_pos_net = int((df["net_pf"] > 1.0).sum())
    n_pos_gross = int((df["gross_pf"] > 1.0).sum())
    print(f"\nnet PF > 1: {n_pos_net}/{len(df)}   gross PF > 1: {n_pos_gross}/{len(df)}")
    print(f"\nSaved {out}")
    print(f"Trial count: {NEW_TRIALS} new. Cumulative N={PRIOR_TRIALS} -> {PRIOR_TRIALS + NEW_TRIALS}")


if __name__ == "__main__":
    main()
