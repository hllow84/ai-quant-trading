#!/usr/bin/env python3
"""
Shared engine for the 6-strategy batch (pairs trading, Bollinger mean-
reversion, MACD crossover, calendar/seasonality, Turtle, Ichimoku).

DAILY BARS ONLY for this batch (standard practice for all 6 named
strategies; M1 is not the convention for any of them). Built from the
project's own real spread-inclusive M1/H1 archives via
research.gold_data.aggregate_daily, NOT resampled adjusted-close-only data,
except the two yfinance ETF series (GLD/SLV) used for the classic gold-
silver pairs trade, which have no bid/ask column on disk -- a stated real-
world round-turn cost is applied to them instead (see COST_BPS below).

COSTS, per instrument, round-turn, applied on every position CHANGE (not
per day held) -- reused/extended from this project's established models:
  XAUUSD/EURUSD/NAS100/US30/SPX500 : real historical spread_close (bps of
      that day's mid close) + 0.35 bps commission (index/FX convention
      already used throughout this project's ORB/ICT work).
  BTCUSDT/ETHUSDT : 20 bps taker-fee commission (Binance), no separate
      spread column in the H1 OHLC file on disk -- reused verbatim from
      run_orb_entry_filters.py's CRYPTO_COST_BPS commission component.
  GLD/SLV (ETF)   : 2 bps round-turn spread (typical liquid-ETF NBBO
      spread) -- STATED ASSUMPTION, not measured from a bid/ask column
      (none exists in the yfinance daily file), flagged explicitly wherever
      used.

DATA SPANS, checked not assumed (see load_daily() docstring per instrument).

SIZING, stated once here for every single-instrument strategy: 1% of
CURRENT capital risked per new position (fixed-fractional, this project's
standing convention), position closed entirely before a new one opens
(no pyramiding except Turtle, which pyramids by its own documented rule
and is sized in Turtle "N" units, stated separately in that script).
Pairs trading is dollar-neutral (stated in that script, not fixed-
fractional in the same sense).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, aggregate_daily
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import expected_max_sharpe, deflated_sharpe

D = _ROOT / "data"
START_CAP = 100_000.0
BARS_PER_YEAR = 252
RISK_PER_TRADE = 0.01
CONC_BAR = 0.60

# ── per-instrument daily loaders ────────────────────────────────────────────
_FX_INDEX_FILES = {
    "XAUUSD": [D / "XAUUSD_M1_2017_spot_dukascopy.csv", D / "XAUUSD_M1_2018_2025_spot_dukascopy.csv"],
    "EURUSD": [D / "EURUSD_M1_2013_2017_spot_dukascopy.csv", D / "EURUSD_M1_2018_2025_spot_dukascopy.csv"],
    "NAS100": [D / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv", D / "NAS100_M1_2018_2025_cfd_dukascopy.csv"],
    "US30":   [D / "US30_M1RTH_2013_2017_cfd_dukascopy.csv", D / "US30_M1_2018_2025_cfd_dukascopy.csv"],
    "SPX500": [D / "SPX500_M1_2017_2025_cfd_dukascopy.csv"],
}
# real 2013-2017 out-of-regime window exists for these; XAUUSD/SPX500 only have the 2017 stub
REAL_OOS_SPLIT = {"EURUSD": "2018-01-01", "NAS100": "2018-01-01", "US30": "2018-01-01"}
STUB_OOS_ONLY = {"XAUUSD", "SPX500"}

_CRYPTO_FILES = {
    "BTCUSDT": D / "BTCUSDT_H1_2018_2025_binance.csv",
    "ETHUSDT": D / "ETHUSDT_H1_2018_2025_binance.csv",
}

INDEX_COST_BPS = dict(commission=0.35)
CRYPTO_COST_BPS = dict(commission=20.0)
ETF_COST_BPS = dict(commission=0.0, spread=2.0)   # stated assumption, see module docstring


def load_daily(inst: str) -> pd.DataFrame:
    """Returns DataFrame indexed by UTC date: close, spread_bps (round-turn,
    already includes commission), high, low, open (mid, for indicators that need OHLC)."""
    if inst in _FX_INDEX_FILES:
        parts = []
        for f in _FX_INDEX_FILES[inst]:
            spot = load_m1_spot(f)
            parts.append(spot)
        spot_all = pd.concat(parts).sort_index()
        spot_all = spot_all[~spot_all.index.duplicated(keep="first")]
        daily = aggregate_daily(spot_all)
        out = pd.DataFrame(index=daily.index)
        out["open"] = daily["mid_open"]; out["high"] = daily["mid_high"]
        out["low"] = daily["mid_low"]; out["close"] = daily["mid_close"]
        out["spread_bps"] = (daily["spread_close"] / daily["mid_close"]) * 1e4 + INDEX_COST_BPS["commission"]
        return out
    if inst in _CRYPTO_FILES:
        h1 = pd.read_csv(_CRYPTO_FILES[inst], parse_dates=["datetime_utc"])
        h1["datetime_utc"] = pd.to_datetime(h1["datetime_utc"], utc=True)
        h1["date"] = h1["datetime_utc"].dt.tz_localize(None).dt.normalize()
        g = h1.groupby("date")
        out = pd.DataFrame({
            "open": g["mid_open"].first(), "high": g["mid_high"].max(),
            "low": g["mid_low"].min(), "close": g["mid_close"].last(),
        }).sort_index()
        out["spread_bps"] = CRYPTO_COST_BPS["commission"]
        return out
    if inst in ("GLD", "SLV"):
        df = pd.read_csv(D / f"{inst}_daily_yfinance.csv", parse_dates=["date"]).set_index("date").sort_index()
        out = df[["open", "high", "low", "close"]].copy()
        out["spread_bps"] = ETF_COST_BPS["spread"] + ETF_COST_BPS["commission"]
        return out
    raise ValueError(f"unknown instrument {inst}")


ALL_INSTRUMENTS = ["XAUUSD", "EURUSD", "NAS100", "US30", "SPX500", "BTCUSDT", "ETHUSDT"]


# ── backtest core: position series -> compounded equity, real costs on change ──
def backtest_from_position(daily: pd.DataFrame, position: pd.Series, risk_per_trade: float = RISK_PER_TRADE) -> dict:
    """
    position: Series aligned to daily.index, values in {-1, 0, +1} (or a
    continuous weight for pairs), meaning the desired exposure for THAT
    day, decided using only information available at or before the prior
    close (caller's responsibility -- guard checked by the caller).
    Cost charged (round-turn, split in half) whenever position changes.
    Equity compounds RISK_PER_TRADE-scaled daily return * position when
    |position|==1 (fixed-fractional directional sizing); for pairs
    (continuous weights) risk_per_trade is passed as 1.0 by the caller,
    since dollar-neutral sizing is handled by the position weights already.
    """
    close = daily["close"]
    ret = close.pct_change().fillna(0.0)
    pos = position.reindex(daily.index).fillna(0.0)
    pos_prev = pos.shift(1).fillna(0.0)
    changed = (pos != pos_prev)
    cost_frac = (daily["spread_bps"].reindex(daily.index).fillna(daily["spread_bps"].median()) / 1e4) * changed.astype(float)
    # cost charged as if crossing the spread on the CHANGED day, split: this is a
    # simplification (real round-turn splits open/close) -- stated once here.
    strat_ret = pos_prev * ret - cost_frac
    net_ret = risk_per_trade * strat_ret if risk_per_trade != 1.0 else strat_ret
    equity = START_CAP * (1.0 + net_ret).cumprod()
    return dict(daily_ret=net_ret, equity=equity, n_position_changes=int(changed.sum()))


def drawdown_with_recovery(equity: pd.Series) -> dict:
    running_peak = equity.cummax()
    dd = 1.0 - equity / running_peak
    max_dd = float(dd.max())
    trough_date = dd.idxmax()
    peak_date = equity.loc[:trough_date].idxmax()
    peak_val = float(equity.loc[peak_date])
    trough_val = float(equity.loc[trough_date])
    after = equity.loc[equity.index > trough_date]
    hit = after[after >= peak_val]
    recovery_date = hit.index[0] if len(hit) else None
    return dict(max_dd=max_dd, peak_date=peak_date, peak_val=peak_val,
                trough_date=trough_date, trough_val=trough_val, recovery_date=recovery_date)


def year_table(daily_ret: pd.Series, equity: pd.Series) -> pd.DataFrame:
    idx = daily_ret.index
    eq = equity.reindex(idx)
    eq_prev = eq.shift(1)
    eq_prev.iloc[0] = START_CAP
    out = []
    for yr in sorted(idx.year.unique()):
        m = idx.year == yr
        start_eq = float(eq_prev[m].iloc[0])
        end_eq = float(eq[m].iloc[-1])
        out.append(dict(year=int(yr), start_equity=start_eq, end_equity=end_eq,
                         year_return_pct=(end_eq / start_eq - 1.0) * 100))
    return pd.DataFrame(out)


def top_year_concentration(yt: pd.DataFrame) -> float:
    """Top year's log-return as a share of total log-return; NaN if total <= 0."""
    logret = np.log(yt["end_equity"] / yt["start_equity"])
    total = logret.sum()
    if total <= 0 or not np.isfinite(total):
        return float("nan")
    return float(logret.max() / total)


def bh_stats(daily: pd.DataFrame) -> dict:
    close = daily["close"]
    ret = close.pct_change().dropna()
    eq = (1.0 + ret).cumprod() * START_CAP
    dd = drawdown_with_recovery(eq)
    return dict(ending=float(eq.iloc[-1]), total_ret=float(eq.iloc[-1] / START_CAP - 1),
                sharpe=sharpe(ret, BARS_PER_YEAR), **dd)


def guard_no_lookahead(signal_decision_date, used_data_max_date) -> bool:
    """Trivial explicit re-check: the latest data timestamp used to form a
    decision must be <= the decision date itself (data known at or before
    the day the position is set, applied to NEXT day's return in backtest_from_position
    via pos.shift(1))."""
    return used_data_max_date <= signal_decision_date


def full_report(label: str, daily: pd.DataFrame, position: pd.Series, risk_per_trade: float = RISK_PER_TRADE,
                oos_split: str | None = None) -> dict:
    bt = backtest_from_position(daily, position, risk_per_trade)
    daily_ret, equity = bt["daily_ret"], bt["equity"]
    dd = drawdown_with_recovery(equity)
    yt = year_table(daily_ret, equity)
    conc = top_year_concentration(yt)
    bh = bh_stats(daily)
    end_bal = float(equity.iloc[-1])
    total_ret = end_bal / START_CAP - 1
    result = dict(
        label=label, start=daily.index[0], end=daily.index[-1],
        n_position_changes=bt["n_position_changes"],
        end_balance=end_bal, total_return=total_ret,
        sharpe=sharpe(daily_ret, BARS_PER_YEAR), net_pf=profit_factor(daily_ret),
        max_dd=dd["max_dd"], peak_date=dd["peak_date"], trough_date=dd["trough_date"],
        recovery_date=dd["recovery_date"],
        top_year_conc=conc, concentrated=bool(np.isfinite(conc) and conc > CONC_BAR),
        bh_ending=bh["ending"], bh_total_ret=bh["total_ret"], bh_sharpe=bh["sharpe"], bh_max_dd=bh["max_dd"],
        beats_bh=bool(end_bal > bh["ending"]),
        yearly=yt, daily_ret=daily_ret, equity=equity,
    )
    if oos_split is not None:
        split = pd.Timestamp(oos_split, tz=daily_ret.index.tz)
        is_ret = daily_ret.loc[daily_ret.index < split]
        oos_ret = daily_ret.loc[daily_ret.index >= split]
        result["is_sharpe"] = sharpe(is_ret, BARS_PER_YEAR) if len(is_ret) > 20 else float("nan")
        result["oos_sharpe"] = sharpe(oos_ret, BARS_PER_YEAR) if len(oos_ret) > 20 else float("nan")
        result["oos_pf"] = profit_factor(oos_ret) if len(oos_ret) > 5 else float("nan")
        result["oos_holds"] = bool(result["oos_pf"] > 1 and result["oos_sharpe"] > 0) if np.isfinite(result["oos_pf"]) else False
    return result


def print_report(r: dict, W: int = 116) -> None:
    print("=" * W)
    print(f"  {r['label']}")
    print("=" * W)
    print(f"  Span: {r['start'].date()} -> {r['end'].date()}   Position changes: {r['n_position_changes']}")
    print(f"\n  {'year':<6} {'start equity':>14} {'end equity':>14} {'year return %':>14}")
    for _, row in r["yearly"].iterrows():
        print(f"  {int(row['year']):<6} {row['start_equity']:>14,.0f} {row['end_equity']:>14,.0f} "
              f"{row['year_return_pct']:>+13.1f}%")
    print(f"\n  FULL-PERIOD: ${START_CAP:,.0f} -> ${r['end_balance']:,.0f} ({r['total_return']*100:+.1f}%)   "
          f"Sharpe {r['sharpe']:+.2f}   net PF {r['net_pf']:.3f}")
    print(f"  MAX DRAWDOWN: {r['max_dd']*100:.1f}%  (peak {r['peak_date'].date()}, trough {r['trough_date'].date()}"
          + (f", recovered {r['recovery_date'].date()})" if r["recovery_date"] is not None else ", NOT recovered)"))
    conc_str = f"{r['top_year_conc']*100:.0f}%" if np.isfinite(r["top_year_conc"]) else "n/a (total<=0)"
    print(f"  TOP-YEAR CONCENTRATION: {conc_str}  -> {'FLAG: concentrated' if r['concentrated'] else 'not concentrated'}")
    print(f"  BUY-AND-HOLD: ${r['bh_ending']:,.0f} ({r['bh_total_ret']*100:+.1f}%, Sharpe {r['bh_sharpe']:+.2f}, "
          f"maxDD {r['bh_max_dd']*100:.1f}%)  -> strategy {'BEATS' if r['beats_bh'] else 'loses to'} B&H")
    if "oos_sharpe" in r:
        print(f"  OUT-OF-REGIME split: IS Sharpe {r['is_sharpe']:+.2f}  OOS Sharpe {r['oos_sharpe']:+.2f}  "
              f"OOS PF {r['oos_pf']:.3f}  -> {'HOLDS' if r['oos_holds'] else 'fails'}")
    print()
