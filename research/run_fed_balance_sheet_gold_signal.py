"""
run_fed_balance_sheet_gold_signal.py — NEW DATA SOURCE #2 of 3 (VIX was #1,
Sec79; Google Trends is #3): Federal Reserve balance sheet (FRED WALCL) vs
gold, the "debasement" hypothesis.

ALPHA STORY (stated a priori, before any result is seen):
    Fed balance sheet EXPANSION (QE — the Fed creates reserves to buy
    assets, expanding its own balance sheet) is read by many market
    participants as currency debasement / future inflation risk -> bullish
    for gold, a hard asset with fixed supply. Balance sheet CONTRACTION
    (QT — reducing holdings, effectively withdrawing liquidity) is the
    opposite -> bearish. This is mechanistically DIFFERENT from Sec75's
    real-yield test even though both are "monetary policy" themed: real
    yields capture the PRICE of money (opportunity cost), WALCL captures
    the QUANTITY (balance-sheet size) — the two can and do diverge (e.g.
    the Fed can hold rates high while still running down a balance sheet
    slowly, or vice versa), so this is a genuinely separate mechanism, not
    a relabeled version of Sec75.

    Signal: trend-following on the DIRECTION of WALCL, mirroring Sec75's
    real-yield methodology for consistency (a level-based mean-reversion
    read would need an arbitrary percentile window; a pure trend read
    needs only one lookback choice and matches how the QE/QT narrative is
    actually discussed -- "the Fed is expanding/shrinking its balance
    sheet", not "the balance sheet is at an X-year extreme"):
        8-week (~2 calendar month) change in WALCL (WALCL is a WEEKLY
        series, so this lookback is chosen in the series' own native
        frequency, not converted from Sec75's daily 20-trading-day choice).
        change > 0 (expanding) -> LONG gold.
        change < 0 (contracting) -> SHORT gold.
        change == 0 -> flat. Fixed a priori, no tuning, no grid.

DATA:
    - FRED WALCL (Fed total assets), weekly since 2002, free, no key
      (scripts/download_fed_balance_sheet.py, data/WALCL_fed_balance_
      sheet_fred.csv).
    - Real spot XAUUSD daily bars 2013-2025 (existing Dukascopy data, same
      window used for every gold test in this project).

LAG: the Fed's H.4.1 release publishes Thursdays for the prior Wednesday's
level -- a real ~1-day publication lag, modeled the same conservative way
as every other macro series in this project (usable starting the next
calendar day, merge_asof backward, plus backtest.py's own 1-bar shift).

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

WALCL_PATH = _ROOT / "data" / "WALCL_fed_balance_sheet_fred.csv"
LOOKBACK_WEEKS = 8
PUBLICATION_LAG_DAYS = 1


def build_walcl_signal(daily_gold: pd.DataFrame) -> pd.Series:
    walcl = pd.read_csv(WALCL_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    walcl["change"] = walcl["walcl"].diff(LOOKBACK_WEEKS)
    walcl["effective_date"] = walcl["date"] + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    walcl = walcl.dropna(subset=["change"])

    price_dates = pd.DataFrame({"date": daily_gold.index.tz_localize(None)})
    merged = pd.merge_asof(
        price_dates.sort_values("date"),
        walcl[["effective_date", "change"]].sort_values("effective_date"),
        left_on="date", right_on="effective_date", direction="backward",
    )
    merged["date"] = daily_gold.index
    merged = merged.set_index("date")

    sig = pd.Series(0.0, index=merged.index)
    sig[merged["change"] > 0] = 1.0
    sig[merged["change"] < 0] = -1.0
    return sig


def main() -> None:
    daily = load_full_daily_gold()
    print(f"Daily gold bars: {len(daily):,}  ({daily.index[0].date()} -> {daily.index[-1].date()})")

    signal = build_walcl_signal(daily)
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
    print("FED BALANCE SHEET TREND SIGNAL — 8wk change in WALCL, gold")
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

    print(f"\nLookback={LOOKBACK_WEEKS}wk, publication lag={PUBLICATION_LAG_DAYS}d — fixed a priori, no tuning.")


if __name__ == "__main__":
    main()
