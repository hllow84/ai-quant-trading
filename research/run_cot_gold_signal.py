"""
run_cot_gold_signal.py — First test of a genuinely new information category for
this project: CFTC Commitment of Traders (COT) positioning, applied to gold.

ALPHA STORY (stated a priori, before any result is seen):
    Classic "COT Index" hypothesis (Larry Williams / "smart money" reading):
    COMEX Gold commercial traders (miners, refiners, bullion banks — mostly
    hedgers with a genuine physical-market information edge) tend to increase
    their net-long hedge exposure ahead of price strength and reduce it ahead
    of weakness, RELATIVE TO THEIR OWN RECENT HISTORY. Non-commercial
    (speculative) positioning is the classic contra-indicator at extremes.
    Signal: when commercial net positioning (as % of open interest) is near
    the TOP of its trailing 3-year range (COT Index >= 80), go long; near the
    BOTTOM (COT Index <= 20), go short; otherwise flat. Thresholds (80/20,
    156-week/3yr lookback) are the standard textbook COT Index parameters,
    fixed a priori — not tuned on this data.

DATA:
    - CFTC Legacy Futures-Only Combined report, COMEX Gold, weekly since 1986
      (scripts/download_cot_gold.py, data/COT_GOLD_legacy_futures_only.csv).
    - Real spot XAUUSD daily bars 2013-2025 (both Dukascopy M1 files this
      project already has, aggregated to daily via research/gold_data.py) —
      this is the window with real bid/ask spread data, so it is also the
      window tested here, NOT the full 40-year COT history.

PUBLICATION LAG (the causal-integrity-critical part):
    CFTC states each Tuesday's report is published the FOLLOWING FRIDAY at
    15:30 ET. A report dated Tuesday is therefore NOT knowable until that
    Friday afternoon. This script treats a report as usable starting the
    NEXT Monday after its report_date (report_date + 6 calendar days is
    always >= the Friday release, with a 3-day safety margin) and merges it
    onto price dates via merge_asof(direction='backward') — a price bar can
    only see COT data whose effective (usable) date has already passed.
    research/backtest.run() then applies its OWN mandatory 1-bar lag on top
    (stacking, deliberately conservative, not a bug).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from research import gold_data
from research.backtest import run as run_backtest
from research.dsr import deflated_sharpe

COT_PATH = _ROOT / "data" / "COT_GOLD_legacy_futures_only.csv"
GOLD_PATHS = [
    _ROOT / "data" / "XAUUSD_M1_2013_2017_spot_dukascopy.csv",
    _ROOT / "data" / "XAUUSD_M1_2018_2025_spot_dukascopy.csv",
]

LOOKBACK_WEEKS = 156     # 3 years, standard COT Index window
UPPER_THRESHOLD = 80.0   # go long
LOWER_THRESHOLD = 20.0   # go short
PUBLICATION_LAG_DAYS = 6  # report_date -> next Monday, safely past the Friday release

COMMISSION_PER_OZ = 0.07     # $/oz round-turn (matches research/ftmo_engine.py)
SLIP_PER_SIDE_OZ = 0.03      # $/oz per side, normal liquidity (matches ftmo_engine.py)

TRADING_DAYS_PER_YEAR = 252


def load_full_daily_gold() -> pd.DataFrame:
    frames = [gold_data.aggregate_daily(gold_data.load_m1_spot(p)) for p in GOLD_PATHS]
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


def build_signal(cot: pd.DataFrame, daily_gold: pd.DataFrame) -> pd.Series:
    price_dates = pd.DataFrame({"date": daily_gold.index.tz_localize(None)})
    merged = pd.merge_asof(
        price_dates.sort_values("date"),
        cot[["effective_date", "cot_index"]].sort_values("effective_date"),
        left_on="date", right_on="effective_date", direction="backward",
    )
    merged["date"] = daily_gold.index
    merged = merged.set_index("date")
    sig = pd.Series(0.0, index=merged.index)
    sig[merged["cot_index"] >= UPPER_THRESHOLD] = 1.0
    sig[merged["cot_index"] <= LOWER_THRESHOLD] = -1.0
    return sig


def annualized_sharpe(net_ret: pd.Series) -> float:
    r = net_ret.dropna()
    if r.std() == 0 or len(r) < 2:
        return 0.0
    return float(r.mean() / r.std() * np.sqrt(TRADING_DAYS_PER_YEAR))


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min())


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        sys.stdout.reconfigure(encoding="utf-8", errors="replace") if hasattr(sys.stdout, "reconfigure") else None

    daily = load_full_daily_gold()
    cot = build_cot_index()

    print(f"Daily gold bars: {len(daily):,}  ({daily.index[0].date()} -> {daily.index[-1].date()})")
    print(f"COT weekly reports (post-1955 filter): {len(cot):,}  "
          f"({cot['report_date'].iloc[0].date()} -> {cot['report_date'].iloc[-1].date()})")

    signal = build_signal(cot, daily)
    asset_ret = daily["mid_close"].pct_change()

    # Real per-bar spread -> bps, PLUS commission/slippage, all matching
    # research/ftmo_engine.py's stated $/oz figures. Cost is charged per unit
    # of turnover (see research/backtest.py docstring: one full round-turn's
    # worth of cost per unit of position change), so halve the round-turn
    # spread and commission to get a per-side, per-turnover-unit cost.
    avg_spread_bps = float((daily["spread_close"] / daily["mid_close"]).mean() * 1e4)
    avg_price = float(daily["mid_close"].mean())
    commission_bps = (COMMISSION_PER_OZ / avg_price) * 1e4
    slip_bps = (SLIP_PER_SIDE_OZ / avg_price) * 1e4
    cost_bps_per_side = avg_spread_bps / 2.0 + commission_bps / 2.0 + slip_bps

    print(f"\nAvg round-turn spread: {avg_spread_bps:.2f} bps | "
          f"per-side cost charged: {cost_bps_per_side:.2f} bps")

    result = run_backtest(
        signal=signal,
        asset_returns=asset_ret,
        fee_bps=cost_bps_per_side,
        slippage_bps=0.0,
        direction="both",
        guard=True,
    )

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
    print("COT GOLD SIGNAL — Commercial COT Index extremes (>=80 long, <=20 short)")
    print(f"{'='*70}")
    print(f"Obs (daily bars): {n_obs:,}   Position switches: {n_switches}")
    print(f"Days long/short/flat: {long_days}/{short_days}/{flat_days} "
          f"({100*long_days/n_obs:.1f}%/{100*short_days/n_obs:.1f}%/{100*flat_days/n_obs:.1f}%)")
    print(f"\n{'Metric':<22}{'Strategy':>15}{'Buy&Hold':>15}")
    print(f"{'Sharpe (net)':<22}{sharpe_net:>15.3f}{bh_sharpe:>15.3f}")
    print(f"{'Sharpe (gross)':<22}{sharpe_gross:>15.3f}{'':>15}")
    print(f"{'Total return':<22}{total_return*100:>14.1f}%{bh_total*100:>14.1f}%")
    print(f"{'Max drawdown':<22}{dd*100:>14.1f}%{bh_dd*100:>14.1f}%")

    # Year-by-year (proxy for regime robustness within the one window we have
    # real spread data for — 2013-2017 bear/chop AND 2018-2025 mostly-bull).
    yearly = net_ret.groupby(net_ret.index.year).apply(lambda r: (1 + r).prod() - 1)
    bh_yearly = bh_ret.groupby(bh_ret.index.year).apply(lambda r: (1 + r).prod() - 1)
    print(f"\n{'Year':<8}{'Strategy':>12}{'Buy&Hold':>12}")
    for yr in yearly.index:
        print(f"{yr:<8}{yearly[yr]*100:>11.1f}%{bh_yearly.get(yr, float('nan'))*100:>11.1f}%")
    n_pos_years = int((yearly > 0).sum())
    print(f"\nYears net-positive: {n_pos_years}/{len(yearly)}")

    # DSR — first trial in a brand-new family ("positioning-cot"). Reference
    # only: a one-trial pool cannot support a real deflation estimate, this is
    # stated explicitly per CLAUDE.md rule 9, not silently omitted.
    dsr_result = deflated_sharpe(sr_best=sharpe_net, sr_trials=[sharpe_net], n_obs=n_obs)
    print(f"\nDSR (reference only, N=1 trial in a brand-new family — NOT a real deflation "
          f"estimate, single-trial pools cannot produce one): {dsr_result['dsr']:.4f}")

    print(f"\nThresholds: COT Index >= {UPPER_THRESHOLD} long, <= {LOWER_THRESHOLD} short, "
          f"lookback={LOOKBACK_WEEKS}w, publication lag={PUBLICATION_LAG_DAYS}d — all fixed a priori.")


if __name__ == "__main__":
    main()
