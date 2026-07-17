"""
gold_data.py — Load real Dukascopy XAUUSD spot data and aggregate to daily bars.

The source file is 1-minute SPOT gold (bid + ask OHLC + per-bar spread), UTC.
This module aggregates it to daily bars and derives the two things a
cost-inclusive backtest needs:

  - mid_close   : (bid_close + ask_close) / 2  — the price series to trade on.
  - spread_close: the ask-bid spread at the daily close, in PRICE units —
                  i.e. the spread you actually cross when you trade the close.

Both bid and ask daily OHLC are retained so downstream strategies can model
entry/exit at the correct side of the book.

Why daily-close spread (not daily mean): a daily SMA strategy transacts at the
close, so the cost that matters is the spread quoted at that moment. Using the
whole-day mean would understate cost at the close (spreads are tighter mid-session).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).parent.parent
DEFAULT_M1_PATH = _ROOT / "data" / "XAUUSD_M1_2018_2025_spot_dukascopy.csv"


def load_m1_spot(path: Path | str = DEFAULT_M1_PATH) -> pd.DataFrame:
    """Load the raw M1 spot CSV with a UTC DatetimeIndex."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"M1 spot file not found: {path}\n"
            "Expected the Dukascopy XAUUSD M1 download (data/XAUUSD_M1_2018_2025_spot_dukascopy.csv)."
        )
    df = pd.read_csv(
        path,
        usecols=[
            "datetime_utc",
            "bid_open", "bid_high", "bid_low", "bid_close",
            "ask_open", "ask_high", "ask_low", "ask_close",
            "spread", "volume",
        ],
        parse_dates=["datetime_utc"],
    )
    df = df.set_index("datetime_utc").sort_index()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    return df


def aggregate_daily(m1: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate M1 bid/ask OHLC to daily bars (UTC calendar day).

    Returns a DataFrame indexed by date (UTC midnight) with:
        bid_open/high/low/close, ask_open/high/low/close,
        mid_open/high/low/close, spread_close, spread_mean, volume, n_bars
    """
    g = m1.groupby(m1.index.normalize())

    daily = pd.DataFrame({
        "bid_open":   g["bid_open"].first(),
        "bid_high":   g["bid_high"].max(),
        "bid_low":    g["bid_low"].min(),
        "bid_close":  g["bid_close"].last(),
        "ask_open":   g["ask_open"].first(),
        "ask_high":   g["ask_high"].max(),
        "ask_low":    g["ask_low"].min(),
        "ask_close":  g["ask_close"].last(),
        "spread_close": g["spread"].last(),
        "spread_mean":  g["spread"].mean(),
        "volume":     g["volume"].sum(),
        "n_bars":     g.size(),
    })

    daily["mid_open"]  = (daily["bid_open"]  + daily["ask_open"])  / 2
    daily["mid_high"]  = (daily["bid_high"]  + daily["ask_high"])  / 2
    daily["mid_low"]   = (daily["bid_low"]   + daily["ask_low"])   / 2
    daily["mid_close"] = (daily["bid_close"] + daily["ask_close"]) / 2

    daily.index.name = "date"
    return daily


def load_daily_spot(path: Path | str = DEFAULT_M1_PATH) -> pd.DataFrame:
    """Convenience: load M1 and return daily aggregated spot bars."""
    return aggregate_daily(load_m1_spot(path))


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    daily = load_daily_spot()
    print(f"Daily bars: {len(daily):,}")
    print(f"Date range: {daily.index[0].date()} -> {daily.index[-1].date()}")
    print(f"Mid close range: ${daily['mid_close'].min():,.2f} - ${daily['mid_close'].max():,.2f}")
    print(f"Spread@close  : median {daily['spread_close'].median():.3f}  "
          f"mean {daily['spread_close'].mean():.3f}  max {daily['spread_close'].max():.3f}")
    print(f"Bars/day      : median {daily['n_bars'].median():.0f}  "
          f"min {daily['n_bars'].min()}  max {daily['n_bars'].max()}")
    # Spread in bps of price (round-turn), for intuition
    rt_bps = (daily["spread_close"] / daily["mid_close"]) * 10_000
    print(f"Round-turn spread (bps of mid): median {rt_bps.median():.2f}  "
          f"mean {rt_bps.mean():.2f}")
    print("\nHead:")
    print(daily[["mid_close", "spread_close", "n_bars"]].head())
    print("\nTail:")
    print(daily[["mid_close", "spread_close", "n_bars"]].tail())
