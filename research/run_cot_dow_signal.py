"""
run_cot_dow_signal.py — COT Index tested on a THIRD instrument: CBOT E-mini
Dow ($5) futures, vs the US30 CFD this project already trades (ORB gold's
combined-book partner, Sec48/Sec52).

Same mechanism as Sec71 (gold) and Sec74 (EUR) — the classic commercial-
level-extreme "COT Index" hypothesis, unchanged parameters, no tuning:
commercial net position (%OI) at a 156-week/3yr percentile extreme,
>=80 long / <=20 short, flat otherwise.

**DATA LIMITATION, stated up front (see scripts/download_cot_dow.py's own
docstring for the live verification done before writing this script):**
CFTC's E-mini Dow COT reporting STOPS at 2022-02-01 — it does not run to
the present the way the gold/EUR series do. This test is therefore
NECESSARILY restricted to 2013-01-01 -> 2022-02-01, a partial window, not
a like-for-like match to Sec71/Sec74's full 2013-2025 tests. This is a
genuine data-availability wall, not a methodology choice, and is reported
as such rather than silently using a shorter window without comment.

DATA: existing US30 CFD H1 Dukascopy data (data/US30_H1_2013_2017 and
2018_2025_cfd_dukascopy.csv, same schema as the gold M1 files, reused via
research/gold_data.py's generic OHLC aggregator), truncated to the COT
data's actual coverage. Cost model: this project's established US30 CFD
convention (commission 0.35bps, slippage 0.15bps/side — research/
us30_macross_breakout_combined_book.py), not gold's $/oz figures.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from research import gold_data
from research.run_cot_gold_signal import (
    LOOKBACK_WEEKS, UPPER_THRESHOLD, LOWER_THRESHOLD, PUBLICATION_LAG_DAYS,
    annualized_sharpe, max_drawdown,
)
from research.backtest import run as run_backtest
from research.dsr import deflated_sharpe

COT_PATH = _ROOT / "data" / "COT_DOW_legacy_futures_only.csv"
US30_PATHS = [
    _ROOT / "data" / "US30_H1_2013_2017_cfd_dukascopy.csv",
    _ROOT / "data" / "US30_H1_2018_2025_cfd_dukascopy.csv",
]

COMMISSION_BPS_ROUNDTURN = 0.35
SLIP_BPS_PER_SIDE = 0.15


def load_full_daily_us30() -> pd.DataFrame:
    frames = [gold_data.aggregate_daily(gold_data.load_m1_spot(p)) for p in US30_PATHS]
    daily = pd.concat(frames).sort_index()
    daily = daily[~daily.index.duplicated(keep="first")]
    return daily


def build_cot_index() -> pd.DataFrame:
    cot = pd.read_csv(COT_PATH, parse_dates=["report_date"])
    cot = cot.sort_values("report_date").reset_index(drop=True)

    comm_net = cot["comm_positions_long_all"] - cot["comm_positions_short_all"]
    comm_net_pct_oi = comm_net / cot["open_interest_all"]

    roll_min = comm_net_pct_oi.rolling(LOOKBACK_WEEKS, min_periods=LOOKBACK_WEEKS).min()
    roll_max = comm_net_pct_oi.rolling(LOOKBACK_WEEKS, min_periods=LOOKBACK_WEEKS).max()
    cot_index = 100.0 * (comm_net_pct_oi - roll_min) / (roll_max - roll_min)

    out = pd.DataFrame({
        "report_date": cot["report_date"],
        "comm_net_pct_oi": comm_net_pct_oi,
        "cot_index": cot_index,
    })
    out["effective_date"] = out["report_date"] + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    return out.dropna(subset=["cot_index"]).reset_index(drop=True)


def build_signal(cot: pd.DataFrame, daily_price: pd.DataFrame) -> pd.Series:
    price_dates = pd.DataFrame({"date": daily_price.index.tz_localize(None)})
    merged = pd.merge_asof(
        price_dates.sort_values("date"),
        cot[["effective_date", "cot_index"]].sort_values("effective_date"),
        left_on="date", right_on="effective_date", direction="backward",
    )
    merged["date"] = daily_price.index
    merged = merged.set_index("date")
    sig = pd.Series(0.0, index=merged.index)
    sig[merged["cot_index"] >= UPPER_THRESHOLD] = 1.0
    sig[merged["cot_index"] <= LOWER_THRESHOLD] = -1.0
    return sig


def main() -> None:
    daily = load_full_daily_us30()
    cot = build_cot_index()

    cot_max_effective = cot["effective_date"].max()
    print(f"COT DOW ($5) coverage: {cot['report_date'].iloc[0].date()} -> "
          f"{cot['report_date'].iloc[-1].date()} (CFTC reporting stops here — data limitation, not a bug)")

    # Restrict to the window the COT data can actually inform. Deliberately
    # truncated, not silently mismatched: any daily bar after the last usable
    # COT report would just carry forward the last observed signal forever,
    # which is not a meaningful backtest of a "positioning" strategy.
    daily = daily[daily.index.tz_localize(None) <= cot_max_effective]
    print(f"US30 window actually tested: {daily.index[0].date()} -> {daily.index[-1].date()} "
          f"({len(daily):,} daily bars)")

    signal = build_signal(cot, daily)
    asset_ret = daily["mid_close"].pct_change()

    avg_spread_bps = float((daily["spread_close"] / daily["mid_close"]).mean() * 1e4)
    cost_bps_per_side = avg_spread_bps / 2.0 + COMMISSION_BPS_ROUNDTURN / 2.0 + SLIP_BPS_PER_SIDE
    print(f"Avg round-turn spread: {avg_spread_bps:.2f} bps | per-side cost charged: {cost_bps_per_side:.2f} bps")

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
    print("COT DOW SIGNAL — Commercial COT Index extremes (>=80 long, <=20 short)")
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
    print(f"\nDSR (reference only, single-trial pool): {dsr_result['dsr']:.4f}")

    print(f"\nThresholds: COT Index >= {UPPER_THRESHOLD} long, <= {LOWER_THRESHOLD} short, "
          f"lookback={LOOKBACK_WEEKS}w, publication lag={PUBLICATION_LAG_DAYS}d — all fixed a priori, "
          "identical to the Sec71 gold / Sec74 EUR tests.")
    print("NOTE: window is 2013 -> 2022-02 ONLY due to CFTC's E-mini Dow reporting gap — "
          "not directly comparable in span to the full 2013-2025 gold/EUR tests.")


if __name__ == "__main__":
    main()
