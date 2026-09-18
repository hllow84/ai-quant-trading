"""
run_vix_gold_signal.py — Second new data source after abandoning COT
(Sec71-Sec78): VIX (CBOE equity-market fear gauge) vs gold.

ALPHA STORY (stated a priori, before any result is seen):
    "Flight to safety" hypothesis: when equity-market stress spikes (VIX
    jumps well above its recent range), capital rotates into safe-haven
    assets including gold -> bullish. When markets are unusually calm
    (VIX well below its recent range, complacency), risk appetite is high
    and the safe-haven bid is weak -> bearish/neutral for gold. UNLIKE the
    real-yield test (Sec75), this is a MEAN-REVERSION-STYLE spike read on
    VIX's LEVEL relative to its own recent range, not a directional trend
    read -- VIX itself is strongly mean-reverting (spikes and decays), so a
    trend-following read on VIX would not match how the mechanism is
    actually described in practice.

    CAVEAT stated a priori, not after seeing the result: this relationship
    is more theoretically mixed than real rates. In acute liquidity crunches
    (e.g. 2008, March 2020) gold has HISTORICALLY SOLD OFF ALONGSIDE
    equities first (margin calls force liquidation of liquid winners,
    including gold) before recovering as a hedge later -- so a same-day/
    next-day VIX-spike-to-long-gold signal could plausibly fail exactly
    when the "flight to safety" story would seem most obviously true. This
    is flagged before running anything, not as a post-hoc excuse.

    Signal: 60-trading-day (~3 month) rolling z-score of VIX close.
    z >= +1.5 (VIX spiking) -> LONG gold.
    z <= -1.5 (VIX unusually calm) -> SHORT gold.
    else -> flat. Window and threshold fixed a priori (the same +/-1.5
    threshold used throughout this project's z-score-based signals, e.g.
    Sec30.1/Sec73), not tuned on this data.

DATA:
    - CBOE's own public VIX history CSV, daily since 1990, free, no key
      (scripts/download_vix.py, data/VIX_history_cboe.csv).
    - Real spot XAUUSD daily bars 2013-2025 (existing Dukascopy data, same
      window used for every gold test in this project).

LAG: VIX closes ~16:15 ET, gold trades continuously — a same-day read would
risk look-ahead relative to gold's own daily close. Treated conservatively
as usable starting the NEXT calendar day, merged via merge_asof(direction=
'backward'), plus research/backtest.py's own mandatory 1-bar shift on top
(same conservative-stacking convention as every other test in this project).

COSTS: identical $/oz cost model to every other gold test (research/
ftmo_engine.py's commission/slippage figures + real per-bar spread).
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

VIX_PATH = _ROOT / "data" / "VIX_history_cboe.csv"
ZSCORE_WINDOW_DAYS = 60
Z_THRESHOLD = 1.5
PUBLICATION_LAG_DAYS = 1


def build_vix_signal(daily_gold: pd.DataFrame) -> pd.Series:
    vix = pd.read_csv(VIX_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    mu = vix["close"].rolling(ZSCORE_WINDOW_DAYS, min_periods=ZSCORE_WINDOW_DAYS).mean()
    sd = vix["close"].rolling(ZSCORE_WINDOW_DAYS, min_periods=ZSCORE_WINDOW_DAYS).std()
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
    sig[merged["z"] >= Z_THRESHOLD] = 1.0
    sig[merged["z"] <= -Z_THRESHOLD] = -1.0
    return sig


def main() -> None:
    daily = load_full_daily_gold()
    print(f"Daily gold bars: {len(daily):,}  ({daily.index[0].date()} -> {daily.index[-1].date()})")

    signal = build_vix_signal(daily)
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
    print("VIX SPIKE SIGNAL — flight-to-safety gold (>=+1.5z long, <=-1.5z short)")
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

    print(f"\nWindow={ZSCORE_WINDOW_DAYS}d, z-threshold=+/-{Z_THRESHOLD}, publication lag={PUBLICATION_LAG_DAYS}d — "
          "fixed a priori, no tuning.")


if __name__ == "__main__":
    main()
