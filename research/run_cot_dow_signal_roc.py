"""
run_cot_dow_signal_roc.py — Rate-of-change / acceleration in commercial
positioning (Sec73's method) applied to CBOT E-mini Dow futures / US30 CFD.

Same two pre-registered variants as Sec73 (reused formula/thresholds, no new
tuning), applied to a THIRD instrument after Sec73 killed both on gold:
    ROC          : week-over-week change in commercial net %OI,
                   z-scored over a trailing 52-week window.
    ACCELERATION : z-score of the second difference of the same 52-week
                   rolling-mean series (Sec30.1's original formula).
Both: long when z >= +1.5, short when z <= -1.5, flat otherwise.

SAME DATA LIMITATION AS Sec77: CFTC's E-mini Dow COT reporting stops at
2022-02-01, so this is necessarily a 2013 -> 2022-02 partial window, not
directly comparable in span to Sec73's full 2013-2025 gold test. Stated
here, not hidden. Uses this project's established US30 CFD cost convention
(0.35bps commission, 0.15bps/side slippage), not gold's $/oz figures.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from research.run_cot_dow_signal import load_full_daily_us30, COT_PATH
from research.run_cot_gold_signal import annualized_sharpe, max_drawdown
from research.run_cot_gold_signal_roc import ROC_WINDOW_WEEKS, Z_THRESHOLD, build_roc_z, build_accel_z
from research.backtest import run as run_backtest
from research.dsr import deflated_sharpe

COMMISSION_BPS_ROUNDTURN = 0.35
SLIP_BPS_PER_SIDE = 0.15
PUBLICATION_LAG_DAYS = 6


def load_comm_net_pct_oi() -> pd.DataFrame:
    cot = pd.read_csv(COT_PATH, parse_dates=["report_date"])
    cot = cot.sort_values("report_date").reset_index(drop=True)
    comm_net_pct_oi = (cot["comm_positions_long_all"] - cot["comm_positions_short_all"]) / cot["open_interest_all"]
    return pd.DataFrame({"report_date": cot["report_date"], "comm_net_pct_oi": comm_net_pct_oi})


def build_signal_from_z(z: pd.Series, report_dates: pd.Series, daily_price: pd.DataFrame) -> pd.Series:
    cot = pd.DataFrame({"report_date": report_dates, "z": z})
    cot["effective_date"] = cot["report_date"] + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    cot = cot.dropna(subset=["z"])

    price_dates = pd.DataFrame({"date": daily_price.index.tz_localize(None)})
    merged = pd.merge_asof(
        price_dates.sort_values("date"),
        cot[["effective_date", "z"]].sort_values("effective_date"),
        left_on="date", right_on="effective_date", direction="backward",
    )
    merged["date"] = daily_price.index
    merged = merged.set_index("date")

    sig = pd.Series(0.0, index=merged.index)
    sig[merged["z"] >= Z_THRESHOLD] = 1.0
    sig[merged["z"] <= -Z_THRESHOLD] = -1.0
    return sig


def evaluate(signal: pd.Series, daily: pd.DataFrame, label: str) -> None:
    asset_ret = daily["mid_close"].pct_change()

    avg_spread_bps = float((daily["spread_close"] / daily["mid_close"]).mean() * 1e4)
    cost_bps_per_side = avg_spread_bps / 2.0 + COMMISSION_BPS_ROUNDTURN / 2.0 + SLIP_BPS_PER_SIDE

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
    print(f"COT DOW SIGNAL -- {label}")
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
    daily = load_full_daily_us30()
    cot = load_comm_net_pct_oi()

    cot_max_effective = cot["report_date"].max() + pd.Timedelta(days=PUBLICATION_LAG_DAYS)
    daily = daily[daily.index.tz_localize(None) <= cot_max_effective]

    print(f"COT DOW coverage: {cot['report_date'].iloc[0].date()} -> {cot['report_date'].iloc[-1].date()} "
          "(CFTC reporting stops here -- same data limitation as Sec77)")
    print(f"US30 window actually tested: {daily.index[0].date()} -> {daily.index[-1].date()} ({len(daily):,} bars)")
    print(f"ROC window={ROC_WINDOW_WEEKS}w, z-threshold=+/-{Z_THRESHOLD} -- fixed a priori, identical to Sec73.")

    roc_z = build_roc_z(cot["comm_net_pct_oi"], ROC_WINDOW_WEEKS)
    sig_roc = build_signal_from_z(roc_z, cot["report_date"], daily)
    evaluate(sig_roc, daily, "RATE-OF-CHANGE (1st difference z-score)")

    accel_z = build_accel_z(cot["comm_net_pct_oi"], ROC_WINDOW_WEEKS)
    sig_accel = build_signal_from_z(accel_z, cot["report_date"], daily)
    evaluate(sig_accel, daily, "ACCELERATION (2nd difference z-score, Sec30.1/Sec73 formula)")


if __name__ == "__main__":
    main()
