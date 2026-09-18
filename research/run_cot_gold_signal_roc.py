"""
run_cot_gold_signal_roc.py — THIRD, separately pre-registered COT gold test:
rate-of-change / acceleration in commercial positioning, not level.

WHY THIS IS GENUINELY DIFFERENT FROM §71/§72 (not another view of the same
mirror-image bet): §71 and §72 both read the LEVEL of positioning against its
own 3-year range, and turned out to be structurally the same bet from two
sides (corr -0.977 between the two series' levels, confirmed in §72). Rate of
change asks a different question: does a FRESH SHIFT in commercial hedging
behavior over the last few weeks predict price, independent of where the
level currently sits in its 3-year range? A commercial book can be near a
multi-year net-long extreme (stale, per §71) while still accelerating further
long (fresh, this test) — the two are not redundant by construction the way
level-vs-level was.

ALPHA STORY (stated a priori, before any result is seen):
    A RAPID recent increase in commercial net long exposure reflects hedgers
    actively reducing short hedges / adding long exposure right now — a fresh
    signal of anticipated price strength, as opposed to a level that may have
    been sitting unchanged for months. Two pre-registered variants, mirroring
    this project's own established on-chain acceleration methodology
    (research/run_onchain_signal_ext.py Part 2, Sec30.1) for consistency
    rather than re-deriving new conventions ad hoc:

      ROC          : week-over-week change in commercial net %OI,
                     z-scored over a trailing 52-week (1yr) window.
      ACCELERATION : z-score of the SECOND difference
                     (RA_t - 2*RA_{t-1} + RA_{t-2}) of the same 52-week
                     rolling-mean series -- exact formula reused from Sec30.1.

    Both: long when z >= +1.5, short when z <= -1.5, flat otherwise.
    Window (52w) and threshold (1.5) are fixed a priori -- the SAME threshold
    already used in Sec30.1's on-chain acceleration test, not hand-picked for
    gold. No grid, no tuning -- one shot each, reported honestly either way.

DATA / COSTS / LAG: identical to run_cot_gold_signal.py (same CFTC source,
same 2013-2025 real-spread gold window, same publication-lag handling, same
$/oz cost model).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from research.run_cot_gold_signal import (
    COT_PATH, PUBLICATION_LAG_DAYS, load_full_daily_gold, annualized_sharpe, max_drawdown,
)
from research.backtest import run as run_backtest
from research.dsr import deflated_sharpe

COMMISSION_PER_OZ = 0.07
SLIP_PER_SIDE_OZ = 0.03

ROC_WINDOW_WEEKS = 52
Z_THRESHOLD = 1.5


def load_comm_net_pct_oi() -> pd.DataFrame:
    cot = pd.read_csv(COT_PATH, parse_dates=["report_date"])
    cot = cot.sort_values("report_date").reset_index(drop=True)
    comm_net_pct_oi = (cot["comm_positions_long_all"] - cot["comm_positions_short_all"]) / cot["open_interest_all"]
    return pd.DataFrame({"report_date": cot["report_date"], "comm_net_pct_oi": comm_net_pct_oi})


def build_roc_z(series: pd.Series, window: int) -> pd.Series:
    roc = series.diff()
    mu = roc.rolling(window, min_periods=window).mean()
    sd = roc.rolling(window, min_periods=window).std()
    return (roc - mu) / sd


def build_accel_z(series: pd.Series, window: int) -> pd.Series:
    ra = series.rolling(window, min_periods=window).mean()
    accel = ra - 2 * ra.shift(1) + ra.shift(2)
    mu = accel.rolling(window, min_periods=window).mean()
    sd = accel.rolling(window, min_periods=window).std()
    return (accel - mu) / sd


def build_signal_from_z(z: pd.Series, report_dates: pd.Series, daily_gold: pd.DataFrame) -> pd.Series:
    cot = pd.DataFrame({"report_date": report_dates, "z": z})
    cot["effective_date"] = cot["report_date"] + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    cot = cot.dropna(subset=["z"])

    price_dates = pd.DataFrame({"date": daily_gold.index.tz_localize(None)})
    merged = pd.merge_asof(
        price_dates.sort_values("date"),
        cot[["effective_date", "z"]].sort_values("effective_date"),
        left_on="date", right_on="effective_date", direction="backward",
    )
    merged["date"] = daily_gold.index
    merged = merged.set_index("date")

    sig = pd.Series(0.0, index=merged.index)
    sig[merged["z"] >= Z_THRESHOLD] = 1.0
    sig[merged["z"] <= -Z_THRESHOLD] = -1.0
    return sig


def evaluate(signal: pd.Series, daily: pd.DataFrame, label: str) -> None:
    asset_ret = daily["mid_close"].pct_change()

    avg_spread_bps = float((daily["spread_close"] / daily["mid_close"]).mean() * 1e4)
    avg_price = float(daily["mid_close"].mean())
    commission_bps = (COMMISSION_PER_OZ / avg_price) * 1e4
    slip_bps = (SLIP_PER_SIDE_OZ / avg_price) * 1e4
    cost_bps_per_side = avg_spread_bps / 2.0 + commission_bps / 2.0 + slip_bps

    result = run_backtest(signal=signal, asset_returns=asset_ret, fee_bps=cost_bps_per_side,
                           slippage_bps=0.0, direction="both", guard=True)

    net_ret = result["net_ret"]
    gross_ret = result["gross_ret"]
    equity = result["equity"]
    n_obs = int(net_ret.notna().sum())
    n_switches = int((result["position"].diff().fillna(0) != 0).sum())

    sharpe_net = annualized_sharpe(net_ret)
    sharpe_gross = annualized_sharpe(gross_ret)
    total_return = float(equity.iloc[-1] - 1.0)
    dd = max_drawdown(equity)

    bh_ret = asset_ret
    bh_equity = (1 + bh_ret.fillna(0)).cumprod()
    bh_sharpe = annualized_sharpe(bh_ret)
    bh_total = float(bh_equity.iloc[-1] - 1.0)
    bh_dd = max_drawdown(bh_equity)

    pos = result["position"]
    long_days = int((pos == 1).sum())
    short_days = int((pos == -1).sum())
    flat_days = int((pos == 0).sum())

    print(f"\n{'='*70}")
    print(f"COT GOLD SIGNAL -- {label}")
    print(f"{'='*70}")
    print(f"Obs (daily bars): {n_obs:,}   Position switches: {n_switches}")
    print(f"Days long/short/flat: {long_days}/{short_days}/{flat_days} "
          f"({100*long_days/n_obs:.1f}%/{100*short_days/n_obs:.1f}%/{100*flat_days/n_obs:.1f}%)")
    print(f"{'Metric':<22}{'Strategy':>15}{'Buy&Hold':>15}")
    print(f"{'Sharpe (net)':<22}{sharpe_net:>15.3f}{bh_sharpe:>15.3f}")
    print(f"{'Sharpe (gross)':<22}{sharpe_gross:>15.3f}{'':>15}")
    print(f"{'Total return':<22}{total_return*100:>14.1f}%{bh_total*100:>14.1f}%")
    print(f"{'Max drawdown':<22}{dd*100:>14.1f}%{bh_dd*100:>14.1f}%")

    yearly = net_ret.groupby(net_ret.index.year).apply(lambda r: (1 + r).prod() - 1)
    n_pos_years = int((yearly > 0).sum())
    print(f"Years net-positive: {n_pos_years}/{len(yearly)}")

    dsr_result = deflated_sharpe(sr_best=sharpe_net, sr_trials=[sharpe_net], n_obs=n_obs)
    print(f"DSR (reference only, single-trial pool): {dsr_result['dsr']:.4f}")


def main() -> None:
    daily = load_full_daily_gold()
    cot = load_comm_net_pct_oi()
    print(f"Daily gold bars: {len(daily):,}  ({daily.index[0].date()} -> {daily.index[-1].date()})")
    print(f"COT weekly reports: {len(cot):,}  ({cot['report_date'].iloc[0].date()} -> {cot['report_date'].iloc[-1].date()})")
    print(f"ROC window={ROC_WINDOW_WEEKS}w, z-threshold=+/-{Z_THRESHOLD} -- fixed a priori, no tuning.")

    roc_z = build_roc_z(cot["comm_net_pct_oi"], ROC_WINDOW_WEEKS)
    sig_roc = build_signal_from_z(roc_z, cot["report_date"], daily)
    evaluate(sig_roc, daily, "RATE-OF-CHANGE (1st difference z-score)")

    accel_z = build_accel_z(cot["comm_net_pct_oi"], ROC_WINDOW_WEEKS)
    sig_accel = build_signal_from_z(accel_z, cot["report_date"], daily)
    evaluate(sig_accel, daily, "ACCELERATION (2nd difference z-score, Sec30.1 formula)")


if __name__ == "__main__":
    main()
