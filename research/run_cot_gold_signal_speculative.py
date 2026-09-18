"""
run_cot_gold_signal_speculative.py — SECOND, separately pre-registered COT
gold test: fade non-commercial (speculative) positioning extremes.

ALPHA STORY (stated a priori, before any result is seen — a DIFFERENT
mechanism from research/run_cot_gold_signal.py's commercial-following test,
not a post-hoc sign flip of its result):
    "Crowded trade" contrarian hypothesis. Non-commercial (speculative)
    traders are retail/CTA/momentum-driven and, per the classic COT reading,
    tend to be MOST net-long right before local tops and MOST net-short right
    before local bottoms — they are the crowd, not the informed side. Signal:
    when non-commercial net positioning (as % of open interest) is near the
    TOP of its trailing 3-year range (COT Index >= 80 -- specs maximally
    net-long), FADE it -> go SHORT. Near the BOTTOM (<= 20 -- specs maximally
    net-short), go LONG. Same textbook 80/20 thresholds and 156-week lookback
    as the commercial test, fixed a priori, not tuned.

    NOTE ON WHY THIS ISN'T "THE SAME TEST FLIPPED": commercial and
    non-commercial net positions are strongly anti-correlated (they must net
    close to zero against open interest, modulo spreading/non-reportable
    positions) but each series' OWN trailing 3-year percentile is computed
    independently -- a non-commercial extreme does not occur on exactly the
    same dates as a commercial extreme (different vol/range history per
    series), so this is a genuinely separate signal, evaluated on its own
    merits, not the prior test's mirror image by construction.

DATA / COSTS / LAG: identical to run_cot_gold_signal.py (same CFTC source,
same 2013-2025 real-spread gold window, same publication-lag handling, same
$/oz cost model) -- only the POSITIONING SERIES and TRADE DIRECTION differ.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from research.run_cot_gold_signal import (
    COT_PATH, LOOKBACK_WEEKS, UPPER_THRESHOLD, LOWER_THRESHOLD,
    PUBLICATION_LAG_DAYS, load_full_daily_gold, annualized_sharpe, max_drawdown,
)
from research.backtest import run as run_backtest
from research.dsr import deflated_sharpe

COMMISSION_PER_OZ = 0.07
SLIP_PER_SIDE_OZ = 0.03


def build_speculative_cot_index() -> pd.DataFrame:
    cot = pd.read_csv(COT_PATH, parse_dates=["report_date"])
    cot = cot.sort_values("report_date").reset_index(drop=True)

    noncomm_net = cot["noncomm_positions_long_all"] - cot["noncomm_positions_short_all"]
    noncomm_net_pct_oi = noncomm_net / cot["open_interest_all"]
    comm_net_pct_oi = (cot["comm_positions_long_all"] - cot["comm_positions_short_all"]) / cot["open_interest_all"]

    roll_min = noncomm_net_pct_oi.rolling(LOOKBACK_WEEKS, min_periods=LOOKBACK_WEEKS).min()
    roll_max = noncomm_net_pct_oi.rolling(LOOKBACK_WEEKS, min_periods=LOOKBACK_WEEKS).max()
    cot_index = 100.0 * (noncomm_net_pct_oi - roll_min) / (roll_max - roll_min)

    corr = float(noncomm_net_pct_oi.corr(comm_net_pct_oi))
    print(f"Sanity check -- corr(noncomm_net_pct_oi, comm_net_pct_oi) = {corr:.3f} "
          f"(expected strongly negative, not exactly -1 due to spreading/non-reportable positions)")

    out = pd.DataFrame({
        "report_date": cot["report_date"],
        "noncomm_net_pct_oi": noncomm_net_pct_oi,
        "cot_index": cot_index,
    })
    out["effective_date"] = out["report_date"] + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    return out.dropna(subset=["cot_index"]).reset_index(drop=True)


def build_fade_signal(cot: pd.DataFrame, daily_gold: pd.DataFrame) -> pd.Series:
    price_dates = pd.DataFrame({"date": daily_gold.index.tz_localize(None)})
    merged = pd.merge_asof(
        price_dates.sort_values("date"),
        cot[["effective_date", "cot_index"]].sort_values("effective_date"),
        left_on="date", right_on="effective_date", direction="backward",
    )
    merged["date"] = daily_gold.index
    merged = merged.set_index("date")
    sig = pd.Series(0.0, index=merged.index)
    # FADE: specs extremely long (index>=80) -> SHORT; extremely short (index<=20) -> LONG.
    sig[merged["cot_index"] >= UPPER_THRESHOLD] = -1.0
    sig[merged["cot_index"] <= LOWER_THRESHOLD] = 1.0
    return sig


def main() -> None:
    daily = load_full_daily_gold()
    cot = build_speculative_cot_index()

    print(f"Daily gold bars: {len(daily):,}  ({daily.index[0].date()} -> {daily.index[-1].date()})")
    print(f"COT weekly reports: {len(cot):,}  ({cot['report_date'].iloc[0].date()} -> {cot['report_date'].iloc[-1].date()})")

    signal = build_fade_signal(cot, daily)
    asset_ret = daily["mid_close"].pct_change()

    avg_spread_bps = float((daily["spread_close"] / daily["mid_close"]).mean() * 1e4)
    avg_price = float(daily["mid_close"].mean())
    commission_bps = (COMMISSION_PER_OZ / avg_price) * 1e4
    slip_bps = (SLIP_PER_SIDE_OZ / avg_price) * 1e4
    cost_bps_per_side = avg_spread_bps / 2.0 + commission_bps / 2.0 + slip_bps
    print(f"\nAvg round-turn spread: {avg_spread_bps:.2f} bps | per-side cost charged: {cost_bps_per_side:.2f} bps")

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
    print("COT GOLD SIGNAL -- FADE non-commercial (speculative) extremes")
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
    print(f"\nDSR (reference only, N=1 in a 2-trial family so far -- not yet a real "
          f"deflation pool): {dsr_result['dsr']:.4f}")

    print(f"\nThresholds: COT Index >= {UPPER_THRESHOLD} -> SHORT, <= {LOWER_THRESHOLD} -> LONG "
          f"(fade), lookback={LOOKBACK_WEEKS}w, publication lag={PUBLICATION_LAG_DAYS}d -- all fixed a priori.")


if __name__ == "__main__":
    main()
