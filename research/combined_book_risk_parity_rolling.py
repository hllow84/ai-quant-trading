"""
combined_book_risk_parity_rolling.py — §52: ROLLING (out-of-sample) risk-
parity weighting, closing the caveat flagged explicitly in §51: the
inverse-vol weights there were computed ONCE from each leg's FULL-SAMPLE
standard deviation (an in-sample choice) — not something a live strategy
could actually have known in advance. This section replaces that with a
genuinely causal, walk-forward weighting scheme and re-measures the two
new project-best pairings (§49 ORB gold+US30 breakout, §48 US30
macross+breakout) under it, to see how much of §51's improvement survives
once look-ahead is removed.

SCHEME (stated before any result seen): monthly rebalance. On the last
trading day of each calendar month, compute each leg's trailing 90-
CALENDAR-DAY standard deviation of daily log-returns (a look-back window
long enough to be stable, short enough to adapt to regime change) using
ONLY returns up to and including that day. Apply
w_a = (1/std_a) / (1/std_a + 1/std_b) as the FIXED weight for every day of
the following calendar month (no intra-month rebalancing, no forward
knowledge of that month's realized returns). Before 90 days of history
exist, default to a flat 50/50 weight — never an undefined or forward-
looking value.

This is the standard-model equivalent of the project's own walk-forward
methodology (CLAUDE.md's "rolling walk-forward with purge/embargo" rule,
usually applied to signal parameters, applied here to a PORTFOLIO WEIGHT
instead) — the correct way to ask whether §51's risk-parity benefit is
real for a deployable strategy, not an in-sample artifact.

Reuses the already-saved daily-return CSVs from §48/§49 unchanged. Zero
new backtests (both legs' own trade simulations are untouched) — this
tests only the WEIGHTING rule, so it adds 0 to the project's cumulative
trial count (N=1570 unchanged).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.metrics import sharpe, max_drawdown
from research.ftmo_engine import equity_from_returns

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
VOL_WINDOW_DAYS = 90

PAIRS = [
    dict(name="§48 US30 macross+breakout", file="us30_macross_breakout_combined_book.csv",
         legA="us30_macross_ret", legB="us30_breakout_ret", labA="US30 macross", labB="US30 breakout"),
    dict(name="§49 ORB gold+US30 breakout", file="orb_gold_us30_breakout_combined_book.csv",
         legA="orb_gold_ret", legB="us30_breakout_ret", labA="ORB gold", labB="US30 breakout"),
]


def rolling_weight_series(a: pd.Series, b: pd.Series) -> pd.Series:
    """Causal monthly-rebalanced inverse-vol weight for leg A, indexed like a/b."""
    idx = a.index
    tz = idx.tz
    # positional index of the last observation in each calendar month
    month_key = idx.tz_localize(None).to_period("M") if tz is not None else idx.to_period("M")
    last_pos_per_month = pd.Series(np.arange(len(idx)), index=month_key).groupby(level=0).max()
    rebalance_positions = last_pos_per_month.to_numpy()

    w_a_at_pos = {}
    for pos in rebalance_positions:
        day = idx[pos]
        window_start = day - pd.Timedelta(days=VOL_WINDOW_DAYS)
        mask = (idx <= day) & (idx > window_start)
        hist_a, hist_b = a[mask], b[mask]
        if mask.sum() < VOL_WINDOW_DAYS * 0.5:  # not enough history yet -- default flat
            w_a_at_pos[pos] = 0.5
            continue
        std_a, std_b = hist_a.std(), hist_b.std()
        if std_a == 0 or std_b == 0 or np.isnan(std_a) or np.isnan(std_b):
            w_a_at_pos[pos] = 0.5
            continue
        w_a_at_pos[pos] = (1.0 / std_a) / (1.0 / std_a + 1.0 / std_b)

    # weight decided at month-end position isn't usable until the NEXT day
    # (no look-ahead); hold flat between rebalances; default 50/50 before
    # the first rebalance has enough history.
    w_by_pos = pd.Series(np.nan, index=np.arange(len(idx)))
    for pos, val in w_a_at_pos.items():
        w_by_pos.iloc[pos] = val
    w_by_pos = w_by_pos.shift(1).ffill().fillna(0.5)
    w = pd.Series(w_by_pos.values, index=idx)
    return w


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    rows = []
    for p in PAIRS:
        df = pd.read_csv(RESULTS / p["file"], parse_dates=["date"]).set_index("date")
        a, b = df[p["legA"]], df[p["legB"]]

        w_a = rolling_weight_series(a, b)
        rolling = w_a * a + (1.0 - w_a) * b

        fixed = 0.5 * a + 0.5 * b
        std_a_full, std_b_full = a.std(), b.std()
        w_a_full = (1.0 / std_a_full) / (1.0 / std_a_full + 1.0 / std_b_full)
        insample_rp = w_a_full * a + (1.0 - w_a_full) * b

        sh_fixed, dd_fixed = sharpe(fixed, BARS_PER_YEAR), max_drawdown(equity_from_returns(fixed))
        sh_insample, dd_insample = sharpe(insample_rp, BARS_PER_YEAR), max_drawdown(equity_from_returns(insample_rp))
        sh_roll, dd_roll = sharpe(rolling, BARS_PER_YEAR), max_drawdown(equity_from_returns(rolling))

        yr_log = rolling.groupby(rolling.index.year).sum()
        n_pos, n_years = int((yr_log > 0).sum()), len(yr_log)
        worst_year, worst_year_label = float(yr_log.min()), int(yr_log.idxmin())

        print(f"=== {p['name']} ===")
        print(f"  Fixed 50/50:              Sharpe={sh_fixed:+.3f}  maxDD={dd_fixed*100:.1f}%")
        print(f"  In-sample risk-parity (§51, w_a={w_a_full:.2f}): Sharpe={sh_insample:+.3f}  maxDD={dd_insample*100:.1f}%")
        print(f"  ROLLING risk-parity (causal, monthly rebal): Sharpe={sh_roll:+.3f}  maxDD={dd_roll*100:.1f}%")
        print(f"  Years positive: {n_pos}/{n_years} (worst: {worst_year_label} {worst_year*100:+.1f}%)")
        print(f"  Realized weight range on {p['labA']}: [{w_a.min():.2f}, {w_a.max():.2f}], "
              f"mean {w_a.mean():.2f}\n")

        rows.append(dict(pair=p["name"], sharpe_fixed=sh_fixed, maxdd_fixed=dd_fixed,
                          sharpe_insample_rp=sh_insample, maxdd_insample_rp=dd_insample,
                          sharpe_rolling_rp=sh_roll, maxdd_rolling_rp=dd_roll,
                          years_pos=n_pos, years_total=n_years))

    out = RESULTS / "combined_book_risk_parity_rolling.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Saved {out}")
    print("Trial count: 0 new (re-weighting of already-scored legs with a causal, "
          "walk-forward rule -- no new backtest). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
