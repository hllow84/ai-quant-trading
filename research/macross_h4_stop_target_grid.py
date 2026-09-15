"""
macross_h4_stop_target_grid.py — H4 index-trend macross: SL (k_atr) x TP (R)
grid on NAS100, same method as the ORB/credit-spread relooks (§39-41).

BASELINE (§ 2026-07-21 US INDEX CFD SWEEP, results/sweep_indices_scored.csv):
NAS100 H4 macross variant 0 (fast=10, slow=30, ema_trend=200, k_atr=2.0,
R=2.0, H=48): grossPF 1.515, netPF 1.469, Sharpe +0.669, maxDD 13.7%, 177
trades, OOS holds. This is the best gross-edge cell this project has found
outside the ORB/credit-spread families, but only 3 hand-picked (fast, slow,
ema_trend, k_atr, R, H) combinations were EVER tested — never an
independent SL/TP sweep. Confirmed by reading strategies/sweep_families.py:
FAMILIES["macross"] has exactly 3 stated variant dicts, no grid search.

MECHANISM (a priori): k_atr sets stop distance in ATR multiples — wider
stop absorbs more noise before being taken out (fewer whipsaw stops) at the
cost of a bigger loss per stop; narrower stop is the reverse. R sets the
fixed target multiple — for a TREND-FOLLOWING signal (which this family's
own gross-edge-monotonic-in-timeframe finding, §10.6, suggests IS what
macross is capturing), the classic literature favors a WIDER target (or no
fixed target) since the edge is concentrated in occasionally-large trend
moves, not small consistent ones — there is a real reason to expect R
matters a lot here, unlike ORB where widening R already failed.

GRID (a priori): k_atr in {1.5, 2.0, 3.0} x R in {1.5, 2.0, 3.0} = 9 cells,
fast/slow/ema_trend/H held at variant 0's values (10/30/200/48). (k_atr=2.0,
R=2.0) reproduces the known baseline exactly, not counted. 8 new trials.
Same cost model, same H4 resample, same strictly_after=True resolution as
the original sweep — reused unchanged from run_sweep_indices.py.
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
from strategies.sweep_families import ma_cross, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
DATA = _ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv"
PRIOR_TRIALS = 1401
NEW_TRIALS = 8

K_ATRS = (1.5, 2.0, 3.0)
RS = (1.5, 2.0, 3.0)
BASE_PARAMS = dict(fast=10, slow=30, ema_trend=200, H=48)


def score(m, params, daily_index):
    cands = ma_cross(m, params, TF_DELTA["H4"])
    for tr in cands:
        tr["session_end"] = pd.Timestamp(tr["session_end"]).tz_convert("UTC") if pd.Timestamp(tr["session_end"]).tz else pd.Timestamp(tr["session_end"]).tz_localize("UTC")
        tr["entry_time"] = pd.Timestamp(tr["entry_time"]).tz_convert("UTC") if pd.Timestamp(tr["entry_time"]).tz else pd.Timestamp(tr["entry_time"]).tz_localize("UTC")
    trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=COST_BPS))
    if trades.empty:
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
    print(f"NAS100 H4 bars: {len(m):,}, {m.index[0]} -> {m.index[-1]}\n")

    rows = []
    for k_atr in K_ATRS:
        for R in RS:
            is_baseline = (k_atr == 2.0 and R == 2.0)
            params = dict(BASE_PARAMS, k_atr=k_atr, R=R)
            res = score(m, params, daily_index)
            label = f"k_atr{k_atr}_R{R}" + (" [BASELINE, repro-only]" if is_baseline else "")
            if res is None:
                print(f"{label}: 0 trades\n")
                continue
            yr_log = np.log1p(res["daily_ret"]).groupby(res["daily_ret"].index.year).sum()
            top_yr = float(np.expm1(yr_log).abs().max() / np.expm1(yr_log).sum()) if np.expm1(yr_log).sum() != 0 else float("nan")
            rows.append(dict(label=label, k_atr=k_atr, R=R, is_baseline=is_baseline,
                              n_trades=res["n_trades"], guard=res["guard"],
                              gross_pf=res["gross_pf"], net_pf=res["net_pf"], sharpe=res["sharpe"],
                              max_dd=res["max_dd"], win_rate=res["win_rate"], top_year_share=top_yr))
            print(f"--- {label} ---")
            print(f"  n={res['n_trades']} guard={res['guard']} grossPF={res['gross_pf']:.3f} "
                  f"netPF={res['net_pf']:.3f} Sharpe={res['sharpe']:+.3f} maxDD={res['max_dd']*100:.1f}% "
                  f"win={res['win_rate']*100:.1f}% topyr={top_yr*100:.1f}%\n")

    df = pd.DataFrame(rows)
    new_rows = df[~df["is_baseline"]]
    sharpes = new_rows["sharpe"].tolist()
    print(f"=== Deflated Sharpe (structural pool: family=macross_h4_stop_target, N={len(sharpes)} new trials) ===")
    for _, r in new_rows.iterrows():
        d = deflated_sharpe(r["sharpe"], sharpes, n_obs=r["n_trades"], ann_factor=BARS_PER_YEAR)
        print(f"  {r['label']}: Sharpe={r['sharpe']:+.3f}  DSR={d['dsr']:.4f}  pool_n={d['pool_n']}")

    out = RESULTS / "macross_h4_stop_target_grid.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved {out}")
    print(f"Trial count: {NEW_TRIALS} new. Cumulative N={PRIOR_TRIALS} -> {PRIOR_TRIALS + NEW_TRIALS}")


if __name__ == "__main__":
    main()
