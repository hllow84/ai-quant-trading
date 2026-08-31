"""
signals.py -- live signal generation. Pulls current prices for the 17-ETF
universe + SPY via yfinance (same source/method as
scripts/download_momentum_universe.py, so the live signal is computed on
data consistent with the audited backtest), then reuses
research/momentum_rotation.py::build_weights() UNCHANGED to compute the
target weights for today's rebalance -- the ranking, market-filter, and
causality logic is not reimplemented here.

HOW today's signal is extracted without modifying the audited backtest code:
build_weights() only ever emits a weight row for a signal date `t` if a
trading day exists in the data AFTER `t` (the execution date). On the live
last-trading-day-of-month run, today IS `t`, but tomorrow doesn't exist in
the data yet. So a single placeholder row, dated safely into the following
calendar month (never affecting which real date is "last day of THIS
month"), is appended with NaN prices purely so build_weights() has an
execution-date label to attach today's weights to. The placeholder's price
is never read by build_weights() -- weights are computed from real prices at
the signal date `t` (today), never from the execution-date row.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf

from live.config import MARKET_FILTER, N_MONTHS, SIGNAL_LOOKBACK_DAYS, SMA_WINDOW, TOP_K
from live.risk import validate_weights
from research.momentum_rotation import BENCHMARK, UNIVERSE, build_weights, month_end_signal_dates

FULL_TICKER_LIST = UNIVERSE + [BENCHMARK]


def pull_price_panel(lookback_days: int = SIGNAL_LOOKBACK_DAYS) -> pd.DataFrame:
    """Fresh yfinance pull, adjusted close, wide panel: index=date, columns=tickers."""
    start = (pd.Timestamp.today().normalize() - pd.Timedelta(days=lookback_days)).date()
    panel = {}
    for ticker in FULL_TICKER_LIST:
        df = yf.download(
            ticker, start=start, interval="1d",
            auto_adjust=True, actions=False, progress=False, threads=False,
        )
        if df is None or df.empty:
            raise RuntimeError(f"yfinance returned no data for {ticker}")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        panel[ticker] = df["Close"]
    adjclose = pd.DataFrame(panel).sort_index()
    adjclose.index = pd.DatetimeIndex(adjclose.index.date)
    # Drop trailing rows where EVERY ticker is NaN -- a data-provider artifact
    # (a calendar row exists before Yahoo has posted that day's bar for any
    # ticker), not a real trading day. A row with SOME but not all tickers
    # NaN (e.g. a newer ETF before its inception) is left untouched -- that
    # is real, meaningful missingness build_weights() already handles.
    adjclose = adjclose.dropna(how="all")
    return adjclose


def _append_future_placeholder(adjclose: pd.DataFrame) -> tuple[pd.DataFrame, pd.Timestamp]:
    """
    Appends one NaN row dated 32 calendar days past the last real date --
    guaranteed to fall in a later calendar month, so it never becomes the
    "last trading day of THIS month" in month_end_signal_dates(). Returns the
    extended panel and the placeholder's date label.
    """
    last_real = adjclose.index[-1]
    placeholder = pd.Timestamp(last_real) + pd.Timedelta(days=32)
    ext = adjclose.copy()
    ext.loc[placeholder] = np.nan
    ext = ext.sort_index()
    return ext, placeholder


def generate_signal(as_of: pd.Timestamp | None = None) -> dict:
    """
    Returns a dict:
      target_weights : pd.Series indexed by UNIVERSE ticker, sums to ~1.0
      signal_date     : the date the weights were computed from
      signal_computed : bool -- False if `as_of` was not treated as a valid
                         signal date at all (e.g. insufficient lookback
                         history, or data hasn't caught up to today). This
                         does NOT mean today is the last trading day of the
                         month -- callers must gate on
                         broker.is_last_trading_day_of_month() separately
                         before treating this as a real rebalance signal.
      risk_off        : bool -- True if the market filter parked in IEF
      adjclose_tail   : last 5 rows of the pulled panel, for the order log
    """
    adjclose = pull_price_panel()
    last_real_date = pd.Timestamp(adjclose.index[-1])
    as_of = pd.Timestamp(as_of) if as_of is not None else last_real_date

    if as_of != last_real_date:
        return {
            "target_weights": None,
            "signal_date": as_of,
            "signal_computed": False,
            "risk_off": None,
            "reason": f"as_of {as_of.date()} is not the latest pulled date {last_real_date.date()}",
        }

    ext, placeholder = _append_future_placeholder(adjclose)
    weights_at_exec, _turnover = build_weights(
        ext,
        n_months=N_MONTHS,
        top_k=TOP_K,
        market_filter=MARKET_FILTER,
        sma_window=SMA_WINDOW,
    )

    if weights_at_exec.empty or weights_at_exec.index[-1] != placeholder:
        return {
            "target_weights": None,
            "signal_date": as_of,
            "signal_computed": False,
            "risk_off": None,
            "reason": (
                f"{as_of.date()} did not produce a signal row (not enough lookback "
                "history yet, or the market filter had no valid SMA/price at this date)"
            ),
        }

    target_weights = weights_at_exec.iloc[-1]
    risk_off = float(target_weights.get("IEF", 0.0)) >= 0.99  # market filter parks 100% IEF

    validate_weights(target_weights)  # raises RiskViolation on malformed signal

    return {
        "target_weights": target_weights,
        "signal_date": as_of,
        "signal_computed": True,
        "risk_off": risk_off,
        "adjclose_tail": adjclose.tail(5),
    }
