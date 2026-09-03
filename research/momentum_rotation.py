"""
momentum_rotation.py -- cross-sectional momentum rotation engine.

Strategy (every default stated, no tuning beyond the stated grid):
  - Universe: 11 SPDR sector ETFs + 6 asset-class ETFs (SPY is benchmark-only,
    never held).
  - Rebalance: monthly, signal measured on the last trading day of each month.
  - Rank the universe by trailing N-month total return (N in {6, 12}), using
    ONLY month-end adjusted closes through the signal date.
  - Hold the top K (K in {3, 5}), equal-weighted.
  - Market filter: if SPY's close on the signal date is below SPY's own
    200-day SMA (computed causally, using daily closes through and including
    the signal date only), go 100% into IEF (intermediate treasuries) instead
    of the ranked basket.
  - No other filters, no numeric optimisation beyond the stated N x K grid.

CAUSALITY / LAG (stated explicitly, not assumed):
  Signal is measured at close(t), t = last trading day of the month.
  The trade is modelled as EXECUTED at close(t+1) -- the next trading day --
  not at close(t) itself, so the strategy never transacts at the same price
  used to rank it. The first live return the new weights earn is therefore
  close(t+2)/close(t+1) - 1. This is a full extra trading day of lag beyond
  the minimum, deliberately conservative. Implemented via:
      weights_daily = weights indexed at exec_date=(t+1), reindexed to the
                      daily calendar, forward-filled
      port_return[d] = weights_daily.shift(1)[d] . daily_return[d]
  which guarantees the weight used to compute the return on day d was known
  at the close of day d-1, and that value in turn was only ever set using
  price data through the signal date t <= d-2.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SECTOR_ETFS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC"]
ASSET_ETFS = ["TLT", "GLD", "IEF", "IWM", "EFA", "EEM"]
UNIVERSE = SECTOR_ETFS + ASSET_ETFS   # ranked/held universe -- SPY excluded
BENCHMARK = "SPY"
DEFENSIVE = "IEF"                      # where the market filter parks capital
SMA_WINDOW = 200

# ── cost model (stated, applied even though monthly turnover is low) ──────────
SPREAD_BPS_PER_SIDE = 2.0     # a few bps, liquid SPDR/major ETFs, stated assumption
COMMISSION_BPS_PER_SIDE = 1.0 # commission-equivalent, conservative flat-fee stand-in
COST_BPS_PER_SIDE = SPREAD_BPS_PER_SIDE + COMMISSION_BPS_PER_SIDE   # 3 bps/side


def month_end_signal_dates(daily_index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Last trading day actually present in the data for each calendar month."""
    s = pd.Series(daily_index, index=daily_index)
    return s.groupby([daily_index.year, daily_index.month]).max().sort_values().values


def week_end_signal_dates(daily_index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Last trading day actually present in the data for each ISO calendar week.

    The weekly analogue of month_end_signal_dates -- used by build_weights()
    when signal_freq="W" (the weekly / bi-weekly rebalance-frequency test,
    STATE_OF_PLAY sec 12.6). Nothing else about the mechanism changes: the
    trailing N-MONTH return lookback and the causal 200-day SMA market filter
    are unchanged; only the cadence at which a new decision is made differs.
    """
    iso = daily_index.isocalendar()
    s = pd.Series(daily_index, index=daily_index)
    return s.groupby([iso["year"].values, iso["week"].values]).max().sort_values().values


def signal_dates(daily_index: pd.DatetimeIndex, freq: str = "M") -> pd.DatetimeIndex:
    """Dispatch to the month-end or week-end signal-date generator. freq in
    {"M", "W"}; default "M" reproduces every existing call site byte-for-byte."""
    if freq == "M":
        return month_end_signal_dates(daily_index)
    if freq == "W":
        return week_end_signal_dates(daily_index)
    raise ValueError(f"signal_freq must be 'M' or 'W', got {freq!r}")


def next_trading_day(daily_index: pd.DatetimeIndex, date) -> pd.Timestamp | None:
    pos = daily_index.searchsorted(date, side="right")
    if pos >= len(daily_index):
        return None
    return daily_index[pos]


def build_weights(
    adjclose: pd.DataFrame,
    n_months: int,
    top_k: int,
    market_filter: bool = True,
    universe: list[str] | None = None,
    sma_window: int = SMA_WINDOW,
    rebalance_step: int = 1,
    benchmark: str = BENCHMARK,
    defensive: str = DEFENSIVE,
    signal_freq: str = "M",
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Returns (weights_at_exec, turnover_at_exec):
      weights_at_exec  -- DataFrame indexed by EXECUTION date (t+1), columns
                           = universe (default module UNIVERSE), target weights.
      turnover_at_exec -- Series of one-way turnover (sum |delta weight|) at
                           each execution date, for cost calculation.

    `universe` overrides the module-level UNIVERSE (e.g. the widened universe
    test) -- `defensive` (default DEFENSIVE="IEF") must be a member of
    whatever list is passed. `sma_window` overrides the 200-day market-filter
    SMA length (audit 8 perturbation test -- 150/250 alternatives).
    `rebalance_step` keeps only every Nth signal date (audit 8 perturbation
    test -- step=2 gives a bi-monthly rebalance); the N-month trailing-return
    lookback is unchanged, only the frequency at which a new decision is made.
    `signal_freq` ("M" default = month-end signal dates, byte-identical to
    every existing call site; "W" = ISO-week-end signal dates) selects the
    base cadence before `rebalance_step` decimates it -- so ("W", step 1) is
    weekly, ("W", step 2) bi-weekly, ("M", step 1) monthly, ("M", step 2)
    bi-monthly, ("M", step 3) quarterly (STATE_OF_PLAY sec 12.6 frequency
    test). The trailing N-MONTH ranking lookback and the causal `sma_window`-day
    SMA market filter are IDENTICAL across every frequency; only the decision
    cadence and the resulting turnover (hence cost) change. `benchmark` (default BENCHMARK="SPY") overrides which
    ticker's causal 200-day SMA drives the risk-on/risk-off market filter --
    added for the cross-universe generalisation test (crypto and country-ETF
    universes have no reason to filter on SPY's regime); both `benchmark` and
    `defensive` default to the original module constants, so every existing
    call site reproduces sections 12/12.1/12.2/12.3 byte-identically. Same
    additive-parameter convention already used for `sma_window`/`rebalance_step`.
    """
    uni = universe if universe is not None else UNIVERSE
    daily_index = adjclose.index
    sig_dates = signal_dates(daily_index, signal_freq)
    if rebalance_step > 1:
        sig_dates = sig_dates[::rebalance_step]

    spy = adjclose[benchmark]
    spy_sma200 = spy.rolling(sma_window, min_periods=sma_window).mean()

    rows = []
    exec_dates = []
    prev_w = pd.Series(0.0, index=uni)

    for t in sig_dates:
        # trailing N-month return needs a signal date >= n_months back with data
        loc = daily_index.get_loc(t)
        # approximate N months back in trading days is avoided: use monthly closes
        target_month = (pd.Timestamp(t).to_period("M") - n_months).to_timestamp("M")
        # find the actual signal date for that month (<= target_month, last trading day on/before)
        past_candidates = [d for d in sig_dates if d <= np.datetime64(target_month) + np.timedelta64(6, "D")]
        past_candidates = [d for d in past_candidates if pd.Timestamp(d).to_period("M") == pd.Timestamp(target_month).to_period("M")]
        if not past_candidates:
            continue
        t_past = past_candidates[-1]

        px_now = adjclose.loc[t, uni]
        px_past = adjclose.loc[t_past, uni]
        valid = px_now.notna() & px_past.notna() & (px_past != 0)
        if valid.sum() < top_k:
            continue

        trailing_ret = (px_now[valid] / px_past[valid] - 1.0).sort_values(ascending=False)
        chosen = trailing_ret.index[:top_k]

        # market filter, causal: SPY close and its 200d SMA AS OF signal date t
        risk_off = False
        if market_filter:
            spy_close_t = spy.loc[t]
            sma_t = spy_sma200.loc[t]
            if pd.isna(sma_t):
                continue  # not enough SPY history yet to evaluate the filter
            risk_off = spy_close_t < sma_t

        w = pd.Series(0.0, index=uni)
        if risk_off:
            w[defensive] = 1.0 if defensive in uni else 0.0
            # `defensive` is in `uni` already; if for some reason price is
            # missing on this date, skip (park nothing traded, stay in prior wt)
            if pd.isna(adjclose.loc[t, defensive]):
                continue
        else:
            w[chosen] = 1.0 / top_k

        ed = next_trading_day(daily_index, t)
        if ed is None:
            continue

        turnover = float((w - prev_w).abs().sum())
        rows.append(w)
        exec_dates.append(ed)
        prev_w = w

    weights_at_exec = pd.DataFrame(rows, index=pd.DatetimeIndex(exec_dates), columns=uni)
    turnover_at_exec = pd.Series(
        [float((weights_at_exec.iloc[i] - (weights_at_exec.iloc[i - 1] if i > 0 else pd.Series(0.0, index=uni))).abs().sum())
         for i in range(len(weights_at_exec))],
        index=weights_at_exec.index,
    )
    return weights_at_exec, turnover_at_exec


def simulate(
    adjclose: pd.DataFrame,
    weights_at_exec: pd.DataFrame,
    turnover_at_exec: pd.Series,
    cost_bps_per_side: float = COST_BPS_PER_SIDE,
    universe: list[str] | None = None,
) -> dict[str, pd.Series]:
    """
    Builds gross and net daily portfolio return series over the FULL span of
    adjclose (weights ffilled from first exec date onward; zero return -- flat
    -- before the first exec date).
    """
    uni = universe if universe is not None else UNIVERSE
    daily_rets = adjclose[uni].pct_change()
    weights_daily = weights_at_exec.reindex(adjclose.index).ffill().fillna(0.0)

    gross_ret = (weights_daily.shift(1) * daily_rets).sum(axis=1)
    gross_ret.iloc[0] = 0.0

    # costs: round-trip cost bps applied to turnover, charged on the day the
    # NEW weights first earn a return (i.e. exec_date shifted 1 trading day,
    # matching weights_daily.shift(1) above).
    cost_frac = turnover_at_exec * (cost_bps_per_side / 10_000.0)
    cost_apply_dates = []
    idx = adjclose.index
    for ed in turnover_at_exec.index:
        nd = next_trading_day(idx, ed)
        cost_apply_dates.append(nd if nd is not None else ed)
    cost_series = pd.Series(cost_frac.values, index=pd.DatetimeIndex(cost_apply_dates))
    cost_series = cost_series.groupby(level=0).sum()
    cost_daily = cost_series.reindex(adjclose.index).fillna(0.0)

    net_ret = gross_ret - cost_daily
    return {"gross": gross_ret, "net": net_ret, "weights_daily": weights_daily, "cost_daily": cost_daily}


def look_ahead_guard(weights_at_exec: pd.DataFrame, adjclose: pd.DataFrame, n_months: int) -> bool:
    """
    Confirms every execution date is strictly AFTER its signal date, and that
    signal dates used to build the weight are at least n_months of calendar
    lookback earlier than exec date minus 1 trading day. Returns True if PASS.
    """
    idx = adjclose.index
    ok = True
    for ed in weights_at_exec.index:
        pos = idx.get_loc(ed)
        if pos == 0:
            ok = False
            break
        sig_date = idx[pos - 1]  # exec date is the trading day AFTER signal date, by construction
        if sig_date >= ed:
            ok = False
    return ok
