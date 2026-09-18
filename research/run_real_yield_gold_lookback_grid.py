"""
run_real_yield_gold_lookback_grid.py — Sec75 used a single a priori 20-
trading-day lookback for the real-yield trend signal (the strongest gross/
net edge found in today's new-data-source push). User asked for parameters
to be swept properly rather than fixed to one arbitrary choice — this grids
the ONE free parameter (lookback window) across a wide range and applies
this project's plateau-selection convention (spec §8.1: pick the interior of
a contiguous run of good cells, never the lucky single-cell argmax; a
one-cell "plateau" is a red flag, not a result).

Grid: LOOKBACK_DAYS in {5, 10, 15, 20, 30, 40, 60, 90, 120, 150, 200, 252}
trading days — spans from ~1 week to ~1 year, covering short-term noise
through to a full-year real-rate trend read. Signal mechanism, cost model,
lag handling, and instrument are UNCHANGED from Sec75 (sign of the change in
DFII10 over the lookback -> long/short gold, always in market). Every cell
is scored the same way; the grid itself is not the same as re-running Sec75
with the "right" number found after the fact — every cell is reported.

This is 12 new trials (each cell), not one.
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
from research.run_real_yield_gold_signal import RATE_PATH, PUBLICATION_LAG_DAYS
from research.backtest import run as run_backtest

RESULTS = _ROOT / "results"
LOOKBACKS = [5, 10, 15, 20, 30, 40, 60, 90, 120, 150, 200, 252]


def build_rate_signal_for_lookback(daily_gold: pd.DataFrame, lookback: int) -> pd.Series:
    rate = pd.read_csv(RATE_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    rate["change"] = rate["dfii10"].diff(lookback)
    rate["effective_date"] = rate["date"] + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    rate = rate.dropna(subset=["change"])

    price_dates = pd.DataFrame({"date": daily_gold.index.tz_localize(None)})
    merged = pd.merge_asof(
        price_dates.sort_values("date"),
        rate[["effective_date", "change"]].sort_values("effective_date"),
        left_on="date", right_on="effective_date", direction="backward",
    )
    merged["date"] = daily_gold.index
    merged = merged.set_index("date")

    sig = pd.Series(0.0, index=merged.index)
    sig[merged["change"] < 0] = 1.0
    sig[merged["change"] > 0] = -1.0
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
    bh_total = float(bh_equity.iloc[-1] - 1.0)
    print(f"Buy-and-hold: Sharpe={bh_sharpe:+.3f}  total_return={bh_total*100:+.1f}%\n")

    rows = []
    for lb in LOOKBACKS:
        signal = build_rate_signal_for_lookback(daily, lb)
        result = run_backtest(signal=signal, asset_returns=asset_ret, fee_bps=cost_bps_per_side,
                               slippage_bps=0.0, direction="both", guard=True)
        net_ret = result["net_ret"]
        equity = result["equity"]
        sh = annualized_sharpe(net_ret)
        dd = max_drawdown(equity)
        tot = float(equity.iloc[-1] - 1.0)
        n_switches = int((result["position"].diff().fillna(0) != 0).sum())
        beats_bh = sh > bh_sharpe
        rows.append(dict(lookback_days=lb, sharpe=sh, max_dd=dd, total_return=tot,
                          n_switches=n_switches, beats_bh_sharpe=beats_bh))
        print(f"lookback={lb:>4}d  Sharpe={sh:+.3f}  maxDD={dd*100:6.1f}%  "
              f"total_return={tot*100:+7.1f}%  switches={n_switches:4d}  "
              f"{'BEATS B&H' if beats_bh else ''}")

    df = pd.DataFrame(rows)
    out = RESULTS / "real_yield_gold_lookback_grid.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved {out}")

    # Plateau check: contiguous runs of lookbacks that beat B&H on Sharpe.
    beats = df["beats_bh_sharpe"].to_numpy()
    runs = []
    start = None
    for i, b in enumerate(beats):
        if b and start is None:
            start = i
        elif not b and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(beats) - 1))

    print(f"\nContiguous runs beating B&H Sharpe ({bh_sharpe:+.3f}):")
    if not runs:
        print("  NONE — no lookback in this grid beats buy-and-hold Sharpe. Confirms Sec75's "
              "single-lookback result was not a lucky/unlucky pick; the mechanism itself tops "
              "out below B&H across the whole tested range.")
    else:
        for s, e in runs:
            lbs = df["lookback_days"].iloc[s:e + 1].tolist()
            size = e - s + 1
            flag = "  [!] ONE-CELL PLATEAU -- treat as overfit, do not select" if size == 1 else ""
            print(f"  lookbacks {lbs} ({size} cell{'s' if size > 1 else ''}){flag}")

    print(f"\nTrial count: {len(LOOKBACKS)} new (one per grid cell).")


if __name__ == "__main__":
    main()
