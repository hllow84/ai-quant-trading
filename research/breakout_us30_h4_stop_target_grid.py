"""
breakout_us30_h4_stop_target_grid.py — US30 H4 breakout-retest: joint
lookback (N) x stop (k_atr) x target (R) x hold (H) grid, fourth candidate
pushed through the same entry/exit/SL/TP refinement method as ORB gold
RETEST (§39), credit-spread SPY (§38/40/41), and NAS100+US30 macross
(§42/43).

BASELINE (2026-07-21 US INDEX CFD SWEEP, results/sweep_indices_scored.csv):
US30 H4 breakout_retest variant 2 (N=20, k_atr=1.5, R=1.5, H=24): grossPF
1.232, netPF 1.183, Sharpe +0.400, maxDD 24.1%, 484 trades. This is the
ONLY cell in the entire breakout family (5 instruments x 5 timeframes x 3
hand-picked variants = 75 cells) with a genuinely positive net Sharpe —
every other breakout cell is net Sharpe <= +0.207, most sharply negative
(confirmed by re-reading results/sweep_indices_scored.csv directly, not
from memory). Chosen as the base for the same reason macross NAS100/US30
were chosen in §42/43: a real, cost-surviving gross edge already exists,
just never had its SL/TP/hold geometry independently searched. Confirmed
by grep: strategies/sweep_families.py FAMILIES["breakout"] has exactly 3
hand-picked (N, k_atr, R, H) combinations, no grid search ever run on this
family in this project.

MECHANISM (a priori, stated before any result seen):
- N (breakout lookback) trades level significance against signal
  frequency: a longer lookback demands a more significant prior high/low
  before triggering (fewer, higher-quality breakouts) at the cost of fewer
  trades; a shorter lookback triggers on noisier, less significant levels.
- k_atr (stop distance) trades noise-absorption against loss size, same
  mechanism as every other family in this project.
- R (target multiple) is a genuinely open question for THIS family, unlike
  macross (trend-following, wide target favored by the timeframe-monotonic
  behavior in §10.6) or ORB (already found wide targets fail, §10.7): a
  breakout-retest entry captures a shorter post-breakout continuation, not
  a persistent multi-day trend, so there is no a priori reason to expect
  either a wide or a narrow target dominates -- worth testing both
  directions rather than assuming.
- H (max hold) could newly bind if R moves far from its baseline value, the
  same invisible-constraint pattern already found in §42's NAS100 grid.

GRID (a priori): N in {10, 20, 30} x k_atr in {1.0, 1.5, 2.0} x R in {1.0,
1.5, 2.0} = 27 cells, H held at the baseline's 24. (N=20, k_atr=1.5, R=1.5)
reproduces the known baseline exactly, not counted. Any edge-hugging result
is followed past the grid edge before being trusted (same discipline as
§39-43), and H is re-swept afterward only if the R/k_atr optimum has moved
enough to plausibly make the fixed H=24 bind (same order of operations as
§42).
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
from strategies.sweep_families import breakout_retest, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
DATA = _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv"
PRIOR_TRIALS = 1448

BASE_PARAMS = dict(H=24)


def score(m, params, daily_index):
    cands = breakout_retest(m, params, TF_DELTA["H4"])
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
    yr_log = np.log1p(daily_ret).groupby(daily_ret.index.year).sum()
    top_yr = float(np.expm1(yr_log).abs().max() / np.expm1(yr_log).sum()) if np.expm1(yr_log).sum() != 0 else float("nan")
    n_pos_years = int((yr_log > 0).sum())
    n_years = len(yr_log)
    return dict(
        n_trades=len(trades), guard=guard,
        gross_pf=profit_factor(trades["gross_R"]), net_pf=profit_factor(trades["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR), max_dd=max_drawdown(equity),
        win_rate=float((trades["net_R"] > 0).mean()), top_year_share=top_yr,
        n_pos_years=n_pos_years, n_years=n_years,
        trades=trades, daily_ret=daily_ret,
    )


def run_cell(m, daily_index, N, k_atr, R, H, label, rows, is_baseline=False):
    params = dict(N=N, k_atr=k_atr, R=R, H=H)
    res = score(m, params, daily_index)
    if res is None:
        print(f"{label}: 0 trades\n")
        return None
    rows.append(dict(label=label, N=N, k_atr=k_atr, R=R, H=H, is_baseline=is_baseline,
                      n_trades=res["n_trades"], guard=res["guard"],
                      gross_pf=res["gross_pf"], net_pf=res["net_pf"], sharpe=res["sharpe"],
                      max_dd=res["max_dd"], win_rate=res["win_rate"],
                      top_year_share=res["top_year_share"],
                      n_pos_years=res["n_pos_years"], n_years=res["n_years"]))
    print(f"--- {label} ---")
    print(f"  n={res['n_trades']} guard={res['guard']} grossPF={res['gross_pf']:.3f} "
          f"netPF={res['net_pf']:.3f} Sharpe={res['sharpe']:+.3f} maxDD={res['max_dd']*100:.1f}% "
          f"win={res['win_rate']*100:.1f}% posyrs={res['n_pos_years']}/{res['n_years']} "
          f"topyr={res['top_year_share']*100:.1f}%\n")
    return res["sharpe"]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    m1 = load_m1_mid(DATA)
    daily_index = aggregate_daily(load_m1_spot(DATA)).index
    m = resample_mid(m1, "4h")
    print(f"US30 H4 bars: {len(m):,}, {m.index[0]} -> {m.index[-1]}\n")

    rows = []
    best_sharpe, best_cell = -1e9, None

    print("=== Grid 1: N x k_atr x R, H=24 fixed (baseline geometry) ===\n")
    for N in (10, 20, 30):
        for k_atr in (1.0, 1.5, 2.0):
            for R in (1.0, 1.5, 2.0):
                is_baseline = (N == 20 and k_atr == 1.5 and R == 1.5)
                label = f"N{N}_katr{k_atr}_R{R}" + (" [BASELINE, repro-only]" if is_baseline else "")
                sh = run_cell(m, daily_index, N, k_atr, R, 24, label, rows, is_baseline)
                if sh is not None and not is_baseline and sh > best_sharpe:
                    best_sharpe, best_cell = sh, dict(N=N, k_atr=k_atr, R=R, H=24)

    print(f"Grid 1 best (excl. baseline): {best_cell}, Sharpe={best_sharpe:+.3f}\n")

    # Grid 1's best (N=10, k_atr=2.0, R=1.0) hit the grid edge on k_atr (high)
    # and R (low) simultaneously -- same edge-follow discipline as §39-43:
    # extend past the edge on both dimensions before trusting it, rather than
    # report the edge-hugging cell as final.
    print("=== Extension: follow the k_atr/R gradient past the grid-1 edge ===\n")
    extension_cells = [
        # round 1: probe wider stop / tighter target around the grid-1 edge
        (5, 2.0, 1.0, 24), (5, 2.5, 1.0, 24), (5, 2.0, 0.75, 24),
        (10, 2.5, 1.0, 24), (10, 3.0, 1.0, 24), (10, 2.0, 0.75, 24), (10, 2.0, 0.5, 24),
        (15, 2.0, 1.0, 24),
        # round 2: k_atr keeps helping, R keeps helping -- push both further
        (10, 3.0, 0.75, 24), (10, 3.0, 0.5, 24), (10, 3.5, 1.0, 24), (10, 3.5, 0.5, 24),
        (10, 4.0, 1.0, 24), (10, 4.0, 0.5, 24), (10, 2.5, 0.5, 24), (10, 2.5, 0.75, 24),
        (20, 3.0, 0.5, 24), (15, 3.0, 0.5, 24),
        # round 3: R=0.5 region strong -- check R=0.25 and k_atr 4.5/5.0, and N sensitivity
        (10, 4.0, 0.25, 24), (10, 4.5, 0.5, 24), (10, 4.5, 0.25, 24), (10, 5.0, 0.5, 24),
        (10, 3.0, 0.25, 24), (15, 4.0, 0.5, 24), (20, 4.0, 0.5, 24), (15, 3.5, 0.5, 24),
        (10, 4.0, 0.75, 24),
        # round 4: R=0.25 is the new peak -- check R<0.25 (reversal test) and N=15/20
        (10, 4.0, 0.15, 24), (10, 4.0, 0.10, 24), (10, 3.5, 0.25, 24), (10, 5.0, 0.25, 24),
        (15, 4.0, 0.25, 24), (20, 4.0, 0.25, 24), (5, 4.0, 0.25, 24),
        # round 5: N=20/k_atr=4.0/R=0.25 is the new peak -- decay-check every direction
        (30, 4.0, 0.25, 24), (25, 4.0, 0.25, 24), (20, 4.5, 0.25, 24), (20, 5.0, 0.25, 24),
        (20, 3.5, 0.25, 24), (20, 4.0, 0.15, 24), (20, 4.0, 0.35, 24),
        # round 6: H sweep at the confirmed N/k_atr/R peak (R shrank a lot from
        # baseline's 1.5 -- check whether the fixed H=24 still fits, same
        # order of operations as §42's NAS100 H-constraint discovery)
        (20, 4.0, 0.25, 12), (20, 4.0, 0.25, 18), (20, 4.0, 0.25, 36), (20, 4.0, 0.25, 48),
        # round 7: H=18 beat H=24 -- fine sweep to find the true H optimum
        (20, 4.0, 0.25, 14), (20, 4.0, 0.25, 16), (20, 4.0, 0.25, 20), (20, 4.0, 0.25, 22),
    ]
    for N, k_atr, R, H in extension_cells:
        label = f"EXT_N{N}_katr{k_atr}_R{R}_H{H}"
        run_cell(m, daily_index, N, k_atr, R, H, label, rows)

    df = pd.DataFrame(rows)
    out = RESULTS / "breakout_us30_h4_stop_target_grid.csv"
    df.to_csv(out, index=False)
    print(f"Saved {out}")

    new_rows = df[~df["is_baseline"]]
    sharpes = new_rows["sharpe"].tolist()
    print(f"\n=== Deflated Sharpe (local grid+extension pool, N={len(sharpes)}) ===")
    for _, r in new_rows.sort_values("sharpe", ascending=False).head(10).iterrows():
        d = deflated_sharpe(r["sharpe"], sharpes, n_obs=r["n_trades"], ann_factor=BARS_PER_YEAR)
        print(f"  {r['label']}: Sharpe={r['sharpe']:+.3f}  DSR={d['dsr']:.4f}  pool_n={d['pool_n']}")

    print(f"\nTrial count: {len(new_rows)} new. Cumulative N={PRIOR_TRIALS} -> {PRIOR_TRIALS + len(new_rows)}")


if __name__ == "__main__":
    main()
