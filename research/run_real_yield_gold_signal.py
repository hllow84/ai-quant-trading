"""
run_real_yield_gold_signal.py — First test of a NEW data source after
abandoning the COT-positioning thread (Sec71-Sec74, killed on both gold and
EUR): real (inflation-adjusted) US interest rates.

ALPHA STORY (stated a priori, before any result is seen):
    Gold pays no yield or dividend. Its opportunity cost is the REAL
    (inflation-adjusted) interest rate available on a safe alternative
    (TIPS). When real rates RISE, holding gold becomes more expensive
    relative to earning that real yield -> bearish for gold. When real
    rates FALL (or go negative), the opportunity cost shrinks or reverses
    -> bullish for gold. This is one of the most widely-documented macro
    relationships in commodities research (unlike the COT hypotheses tested
    in Sec71-Sec74, which turned out not to hold empirically).

    Signal: trend-following on the DIRECTION of real rates, not their level
    (a level-based mean-reversion signal would need an arbitrary lookback
    window the way COT's percentile did; a pure trend/momentum read of the
    rate itself needs no such window choice beyond one lookback, and matches
    how this relationship is actually discussed in practice -- "real yields
    are falling/rising", not "real yields are at an X-year extreme"):
        20-trading-day (~1 calendar month) change in DFII10.
        change < 0 (real yields falling) -> LONG gold.
        change > 0 (real yields rising)   -> SHORT gold.
        change == 0 (exact tie, negligible) -> flat.
    Always-in-market by construction (no dead zone) -- kept deliberately
    simple as the FIRST test of this mechanism, fixed a priori, no tuning.

DATA:
    - FRED DFII10 (10yr TIPS real yield), daily since 2003, free, no key
      (scripts/download_real_yield.py, data/DFII10_real_yield_fred.csv).
    - Real spot XAUUSD daily bars 2013-2025 (existing Dukascopy data, same
      window used for every gold test in this project).

PUBLICATION LAG: FRED publishes DFII10 the SAME trading day (Treasury H.15
release, ~16:15 ET) -- materially different from COT's multi-day lag. Applied
1 full calendar day of lag before use (conservative: treats it as unusable
until the NEXT trading day) via merge_asof(direction='backward') on
(date - 1 day), on top of research/backtest.py's own mandatory 1-bar shift.

COSTS: identical $/oz cost model to every other gold test in this project
(research/ftmo_engine.py's commission/slippage figures + real per-bar spread).
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
from research.backtest import run as run_backtest
from research.dsr import deflated_sharpe

RATE_PATH = _ROOT / "data" / "DFII10_real_yield_fred.csv"
LOOKBACK_DAYS = 20         # ~1 calendar month of trading days
PUBLICATION_LAG_DAYS = 1   # same-day FRED release -> usable next trading day


def build_rate_signal(daily_gold: pd.DataFrame) -> pd.Series:
    rate = pd.read_csv(RATE_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    rate["change"] = rate["dfii10"].diff(LOOKBACK_DAYS)
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
    sig[merged["change"] < 0] = 1.0   # real yields falling -> long gold
    sig[merged["change"] > 0] = -1.0  # real yields rising -> short gold
    return sig


def main() -> None:
    daily = load_full_daily_gold()
    print(f"Daily gold bars: {len(daily):,}  ({daily.index[0].date()} -> {daily.index[-1].date()})")

    signal = build_rate_signal(daily)
    asset_ret = daily["mid_close"].pct_change()

    avg_spread_bps = float((daily["spread_close"] / daily["mid_close"]).mean() * 1e4)
    avg_price = float(daily["mid_close"].mean())
    commission_bps = (COMMISSION_PER_OZ / avg_price) * 1e4
    slip_bps = (SLIP_PER_SIDE_OZ / avg_price) * 1e4
    cost_bps_per_side = avg_spread_bps / 2.0 + commission_bps / 2.0 + slip_bps
    print(f"Per-side cost charged: {cost_bps_per_side:.2f} bps")

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
    print(f"REAL-YIELD TREND SIGNAL — 20d change in DFII10, gold")
    print(f"{'='*70}")
    print(f"Obs (daily bars): {n_obs:,}   Position switches: {n_switches}")
    print(f"Days long/short/flat: {long_days}/{short_days}/{flat_days} "
          f"({100*long_days/n_obs:.1f}%/{100*short_days/n_obs:.1f}%/{100*flat_days/n_obs:.1f}%)")
    print(f"\n{'Metric':<22}{'Strategy':>15}{'Buy&Hold':>15}")
    print(f"{'Sharpe (net)':<22}{sharpe_net:>15.3f}{bh_sharpe:>15.3f}")
    print(f"{'Sharpe (gross)':<22}{sharpe_gross:>15.3f}{'':>15}")
    print(f"{'Total return':<22}{total_return*100:>14.1f}%{bh_total*100:>14.1f}%")
    print(f"{'Max drawdown':<22}{dd*100:>14.1f}%{bh_dd*100:>14.1f}%")

    yearly = net_ret.groupby(net_ret.index.year).apply(lambda r: (1 + r).prod() - 1)
    bh_yearly = bh_ret.groupby(bh_ret.index.year).apply(lambda r: (1 + r).prod() - 1)
    print(f"\n{'Year':<8}{'Strategy':>12}{'Buy&Hold':>12}")
    for yr in yearly.index:
        print(f"{yr:<8}{yearly[yr]*100:>11.1f}%{bh_yearly.get(yr, float('nan'))*100:>11.1f}%")
    n_pos_years = int((yearly > 0).sum())
    print(f"\nYears net-positive: {n_pos_years}/{len(yearly)}")

    dsr_result = deflated_sharpe(sr_best=sharpe_net, sr_trials=[sharpe_net], n_obs=n_obs)
    print(f"\nDSR (reference only, single-trial pool, brand-new family): {dsr_result['dsr']:.4f}")

    print(f"\nLookback={LOOKBACK_DAYS} trading days, publication lag={PUBLICATION_LAG_DAYS}d — "
          "fixed a priori, no tuning.")


if __name__ == "__main__":
    main()
