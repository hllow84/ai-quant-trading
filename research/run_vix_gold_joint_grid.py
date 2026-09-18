"""
run_vix_gold_joint_grid.py — Sec79 used a single a priori 60-day window and
+/-1.5 z-threshold for the VIX spike signal. User asked to keep sweeping
rather than fixing parameters — this joint-grids BOTH free parameters
(window x threshold) together, since they interact (a short window makes
the z-score noisier, which changes how a given threshold behaves), matching
this project's established joint-grid-over-staged-grid methodology
(Sec39-Sec45's lesson: joint grids catch interaction effects staged/
one-at-a-time search misses).

Grid: WINDOW_DAYS in {20, 30, 40, 60, 90, 120, 180, 252} (trading days,
~1mo to ~1yr) x Z_THRESHOLD in {1.0, 1.25, 1.5, 1.75, 2.0, 2.5} = 48 cells.
Mechanism, cost model, lag handling, instrument all UNCHANGED from Sec79.

48 new trials.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from research.run_cot_gold_signal import (
    load_full_daily_gold, annualized_sharpe, max_drawdown,
    COMMISSION_PER_OZ, SLIP_PER_SIDE_OZ,
)
from research.run_vix_gold_signal import VIX_PATH, PUBLICATION_LAG_DAYS
from research.backtest import run as run_backtest

RESULTS = _ROOT / "results"
WINDOWS = [20, 30, 40, 60, 90, 120, 180, 252]
THRESHOLDS = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5]


def build_signal(daily_gold: pd.DataFrame, window: int, threshold: float) -> pd.Series:
    vix = pd.read_csv(VIX_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    mu = vix["close"].rolling(window, min_periods=window).mean()
    sd = vix["close"].rolling(window, min_periods=window).std()
    vix["z"] = (vix["close"] - mu) / sd
    vix["effective_date"] = vix["date"] + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    vix = vix.dropna(subset=["z"])

    price_dates = pd.DataFrame({"date": daily_gold.index.tz_localize(None)})
    merged = pd.merge_asof(
        price_dates.sort_values("date"),
        vix[["effective_date", "z"]].sort_values("effective_date"),
        left_on="date", right_on="effective_date", direction="backward",
    )
    merged["date"] = daily_gold.index
    merged = merged.set_index("date")

    sig = pd.Series(0.0, index=merged.index)
    sig[merged["z"] >= threshold] = 1.0
    sig[merged["z"] <= -threshold] = -1.0
    return sig


def main() -> None:
    daily = load_full_daily_gold()
    asset_ret = daily["mid_close"].pct_change()

    avg_spread_bps = float((daily["spread_close"] / daily["mid_close"]).mean() * 1e4)
    avg_price = float(daily["mid_close"].mean())
    commission_bps = (COMMISSION_PER_OZ / avg_price) * 1e4
    slip_bps = (SLIP_PER_SIDE_OZ / avg_price) * 1e4
    cost_bps_per_side = avg_spread_bps / 2.0 + commission_bps / 2.0 + slip_bps

    bh_equity = (1 + asset_ret.fillna(0)).cumprod()
    bh_sharpe = annualized_sharpe(asset_ret)
    print(f"Buy-and-hold: Sharpe={bh_sharpe:+.3f}\n")

    rows = []
    grid = np.full((len(WINDOWS), len(THRESHOLDS)), np.nan)
    for i, w in enumerate(WINDOWS):
        for j, t in enumerate(THRESHOLDS):
            signal = build_signal(daily, w, t)
            result = run_backtest(signal=signal, asset_returns=asset_ret, fee_bps=cost_bps_per_side,
                                   slippage_bps=0.0, direction="both", guard=True)
            net_ret = result["net_ret"]
            equity = result["equity"]
            sh = annualized_sharpe(net_ret)
            dd = max_drawdown(equity)
            tot = float(equity.iloc[-1] - 1.0)
            n_switches = int((result["position"].diff().fillna(0) != 0).sum())
            beats_bh = sh > bh_sharpe
            grid[i, j] = sh
            rows.append(dict(window_days=w, z_threshold=t, sharpe=sh, max_dd=dd,
                              total_return=tot, n_switches=n_switches, beats_bh_sharpe=beats_bh))

    df = pd.DataFrame(rows)
    out = RESULTS / "vix_gold_joint_grid.csv"
    df.to_csv(out, index=False)

    print("Sharpe grid (rows=window_days, cols=z_threshold):")
    header = "window\\thr " + "".join(f"{t:>7.2f}" for t in THRESHOLDS)
    print(header)
    for i, w in enumerate(WINDOWS):
        row_str = f"{w:>10d} " + "".join(f"{grid[i,j]:>7.3f}" for j in range(len(THRESHOLDS)))
        print(row_str)

    best = df.loc[df["sharpe"].idxmax()]
    n_beat = int(df["beats_bh_sharpe"].sum())
    print(f"\nBest single cell: window={best['window_days']:.0f}d thr={best['z_threshold']:.2f} "
          f"Sharpe={best['sharpe']:+.3f} maxDD={best['max_dd']*100:.1f}% total_return={best['total_return']*100:+.1f}%")
    print(f"Cells beating B&H Sharpe ({bh_sharpe:+.3f}): {n_beat}/{len(df)}")

    # Simple plateau check: is the best cell's 3x3 (or smaller at edges) neighborhood
    # also positive and reasonably close, or is it an isolated spike?
    bi = WINDOWS.index(int(best["window_days"]))
    bj = THRESHOLDS.index(float(best["z_threshold"]))
    neighbors = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ni, nj = bi + di, bj + dj
            if 0 <= ni < len(WINDOWS) and 0 <= nj < len(THRESHOLDS):
                neighbors.append(grid[ni, nj])
    neighbors = [n for n in neighbors if not np.isnan(n)]
    pos_neighbors = sum(1 for n in neighbors if n > 0)
    print(f"\nBest cell's neighborhood ({len(neighbors)} cells incl. itself): "
          f"{pos_neighbors}/{len(neighbors)} positive, "
          f"{'plausible plateau' if pos_neighbors >= len(neighbors) * 0.6 else '[!] ISOLATED SPIKE -- not a robust plateau'}.")

    print(f"\nSaved {out}")
    print(f"Trial count: {len(WINDOWS) * len(THRESHOLDS)} new (one per grid cell).")


if __name__ == "__main__":
    main()
