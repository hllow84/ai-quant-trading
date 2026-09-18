"""
run_google_trends_gold_signal.py — NEW DATA SOURCE #3 of 3 (VIX was #1,
Sec79; Fed balance sheet was #2, Sec80): Google Trends retail search
interest in "buy gold" — a genuinely different signal TYPE from every prior
test in this project (attention/sentiment data, not price, positioning, or
macro-policy data).

ALPHA STORY (stated a priori, before any result is seen):
    Contrarian "crowded retail attention" hypothesis, the same family of
    reasoning as the classic "In Search of Attention" retail-attention
    literature and this project's own Sec72 COT fade-the-crowd test (but
    on a completely different, non-futures-market data source): a SPIKE in
    "buy gold" search interest reflects retail FOMO/panic-buying, which
    historically tends to cluster near LOCAL TOPS (retail is a lagging,
    not leading, indicator) -> FADE it, go SHORT. Depressed/apathetic
    search interest reflects an ignored, undervalued asset -> go LONG.

    Signal: z-score of monthly "buy gold" (US) search interest over a
    trailing 24-month window (chosen because Google Trends returns only
    156 monthly observations total for this project's 2013-2025 span --
    a 3yr/36mo window as used for COT would leave too short a live history
    to test; 24mo is the largest common a priori choice, e.g. "2yr lookback",
    that still leaves a usable multi-year backtest). z >= +1.5 -> SHORT;
    z <= -1.5 -> LONG; else flat. Fixed a priori, no tuning, no grid.

    STATED CAVEAT (before running, not after): Google Trends' monthly
    resolution means this signal only updates ~12 times/year -- a much
    lower-frequency data source than every other test in this project. A
    weak or noisy result here could reflect the data's low information
    density as much as the hypothesis being wrong; this is a stated
    limitation of the FREE data available, not a result-dependent excuse.

DATA:
    - Google Trends "buy gold" (US), monthly, 2013-2025, via pytrends
      (unofficial free wrapper, no key) — scripts/download_google_trends_
      gold.py, data/google_trends_buy_gold_us.csv. Google Trends' own
      0-100 index is RELATIVE TO THE PULLED WINDOW (stated in the
      downloader's docstring).
    - Real spot XAUUSD daily bars 2013-2025 (existing Dukascopy data).

LAG: Google Trends monthly data for a given month is available within the
first few days of the FOLLOWING month. Modeled conservatively as usable
starting 7 calendar days after that month's end, merged via merge_asof
(direction='backward'), plus backtest.py's own mandatory 1-bar shift.

COSTS: identical $/oz cost model to every other gold test.
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

TRENDS_PATH = _ROOT / "data" / "google_trends_buy_gold_us.csv"
ZSCORE_WINDOW_MONTHS = 24
Z_THRESHOLD = 1.5
PUBLICATION_LAG_DAYS = 7  # month-end data usable ~1wk into the next month


def build_trends_signal(daily_gold: pd.DataFrame) -> pd.Series:
    trends = pd.read_csv(TRENDS_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    mu = trends["search_interest"].rolling(ZSCORE_WINDOW_MONTHS, min_periods=ZSCORE_WINDOW_MONTHS).mean()
    sd = trends["search_interest"].rolling(ZSCORE_WINDOW_MONTHS, min_periods=ZSCORE_WINDOW_MONTHS).std()
    trends["z"] = (trends["search_interest"] - mu) / sd
    # Each row's date is the FIRST of that month; the month's data is only
    # usable after that month has ENDED, so anchor effective_date to next
    # month's start plus the publication lag.
    trends["effective_date"] = trends["date"] + pd.DateOffset(months=1) + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    trends = trends.dropna(subset=["z"])

    price_dates = pd.DataFrame({"date": daily_gold.index.tz_localize(None)})
    merged = pd.merge_asof(
        price_dates.sort_values("date"),
        trends[["effective_date", "z"]].sort_values("effective_date"),
        left_on="date", right_on="effective_date", direction="backward",
    )
    merged["date"] = daily_gold.index
    merged = merged.set_index("date")

    sig = pd.Series(0.0, index=merged.index)
    sig[merged["z"] >= Z_THRESHOLD] = -1.0  # crowded search interest -> fade, SHORT
    sig[merged["z"] <= -Z_THRESHOLD] = 1.0  # apathy -> LONG
    return sig


def main() -> None:
    daily = load_full_daily_gold()
    print(f"Daily gold bars: {len(daily):,}  ({daily.index[0].date()} -> {daily.index[-1].date()})")

    signal = build_trends_signal(daily)
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
    print("GOOGLE TRENDS 'buy gold' FADE SIGNAL")
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

    print(f"\nWindow={ZSCORE_WINDOW_MONTHS}mo, z-threshold=+/-{Z_THRESHOLD}, "
          f"publication lag={PUBLICATION_LAG_DAYS}d — fixed a priori, no tuning.")


if __name__ == "__main__":
    main()
