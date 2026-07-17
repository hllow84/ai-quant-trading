"""
ftmo_engine.py — Event-driven trade simulator for FTMO-shaped gold strategies.

Unlike research/backtest.py (continuous {-1,0,+1} position signals), these
strategies are trade-by-trade with a hard stop and a fixed-R target. This engine
resolves each trade bar-by-bar on M1 mid data and charges REAL costs:

  cost per trade (price units, $/oz):
      spread   : the REAL spread at the entry minute (full round-turn spread)
      slippage : per side, WIDER during news hours (see NEWS_HOURS_UTC)
      commission: $7 / lot round-turn  ->  $0.07 / oz  (1 lot = 100 oz)

Everything (entry, stop, target) is expressed in MID prices; the spread is
charged explicitly, so there is no double-counting versus bid/ask fills.

Risk model: 1% of current equity per trade. stop distance = 1R. A trade's
equity impact is  RISK_PER_TRADE * net_R,  where net_R = gross_R - cost_R and
cost_R = total_cost_price / stop_distance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# ── Cost model (all in $/oz) ───────────────────────────────────────────────────
COMMISSION_PER_OZ   = 0.07     # $7 / lot round-turn, 1 lot = 100 oz
SLIP_NORMAL_PER_SIDE = 0.03    # $/oz per side, normal liquidity
SLIP_NEWS_PER_SIDE   = 0.10    # $/oz per side, news hours (wider)

# News windows (UTC): London open and US session / data releases.
# Slippage is widened when the ENTRY minute falls in these windows.
NEWS_HOURS_UTC = [
    (7, 0, 8, 0),      # 07:00-08:00 London open
    (12, 30, 14, 30),  # 12:30-14:30 US data / NY open
]

RISK_PER_TRADE = 0.01          # 1% of current equity per trade


def _slip_per_side(ts: pd.Timestamp) -> float:
    minute_of_day = ts.hour * 60 + ts.minute
    for h1, m1, h2, m2 in NEWS_HOURS_UTC:
        if h1 * 60 + m1 <= minute_of_day < h2 * 60 + m2:
            return SLIP_NEWS_PER_SIDE
    return SLIP_NORMAL_PER_SIDE


def simulate_trades(m1_mid: pd.DataFrame, trades: list[dict]) -> pd.DataFrame:
    """
    Resolve each candidate trade on M1 mid data.

    Each trade dict must have:
        entry_time  : pd.Timestamp (decision/execution time; resolution scans M1 bars >= this)
        side        : 'long' | 'short'
        entry_mid   : float  (mid price at entry)
        stop        : float  (mid stop level)
        target      : float  (mid target level)
        session_end : pd.Timestamp (force-flat time; time-exit at mid_close of that bar)

    Returns a DataFrame (one row per executed trade) with realized R and returns.
    Same-bar stop+target ambiguity is resolved conservatively as STOP first.
    """
    idx    = m1_mid.index
    # tz-naive int64 ns for fast, warning-free searchsorted (index is UTC-sorted)
    ts_ns  = idx.tz_localize(None).values.astype("datetime64[ns]").view("int64")
    lows   = m1_mid["mid_low"].to_numpy()
    highs  = m1_mid["mid_high"].to_numpy()
    closes = m1_mid["mid_close"].to_numpy()
    spreads = m1_mid["spread"].to_numpy()
    n = len(idx)

    rows = []
    for tr in trades:
        entry_time = tr["entry_time"]
        side       = tr["side"]
        entry_mid  = float(tr["entry_mid"])
        stop       = float(tr["stop"])
        target     = float(tr["target"])
        sess_end   = tr["session_end"]

        risk = (entry_mid - stop) if side == "long" else (stop - entry_mid)
        if risk <= 0:
            continue  # malformed (stop on wrong side); skip

        entry_ns = pd.Timestamp(entry_time).tz_convert(None).value
        end_ns   = pd.Timestamp(sess_end).tz_convert(None).value
        start = int(np.searchsorted(ts_ns, entry_ns, side="left"))
        end   = int(np.searchsorted(ts_ns, end_ns,   side="right"))
        if start >= n or start >= end:
            continue  # no forward data

        exit_mid = None
        reason   = None
        exit_i   = None
        for i in range(start, min(end, n)):
            if side == "long":
                if lows[i] <= stop:
                    exit_mid, reason, exit_i = stop, "stop", i
                    break
                if highs[i] >= target:
                    exit_mid, reason, exit_i = target, "target", i
                    break
            else:  # short
                if highs[i] >= stop:
                    exit_mid, reason, exit_i = stop, "stop", i
                    break
                if lows[i] <= target:
                    exit_mid, reason, exit_i = target, "target", i
                    break
        if exit_mid is None:
            # time exit at the last in-session bar
            exit_i   = min(end, n) - 1
            exit_mid = float(closes[exit_i])
            reason   = "time"

        gross_R = ((exit_mid - entry_mid) if side == "long"
                   else (entry_mid - exit_mid)) / risk

        # Cost in price units: real spread (round-turn) + 2x per-side slip + commission
        spread_at_entry = float(spreads[start])
        slip_rt = 2.0 * _slip_per_side(entry_time)
        cost_price = spread_at_entry + slip_rt + COMMISSION_PER_OZ
        cost_R = cost_price / risk
        net_R  = gross_R - cost_R

        rows.append({
            "entry_time": entry_time,
            "exit_time":  idx[exit_i],
            "side":       side,
            "reason":     reason,
            "entry_mid":  entry_mid,
            "exit_mid":   exit_mid,
            "risk_price": risk,
            "gross_R":    gross_R,
            "cost_R":     cost_R,
            "net_R":      net_R,
            "ret_frac":   RISK_PER_TRADE * net_R,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("exit_time").reset_index(drop=True)
    return df


def build_daily_returns(trades_df: pd.DataFrame, daily_index: pd.DatetimeIndex) -> pd.Series:
    """
    Aggregate trade P&L into a calendar-daily return series (fraction of equity),
    reindexed onto `daily_index` (the trading-day calendar) between the first and
    last trade. No-trade days are 0. Within-day trades are summed (1% risk each,
    few per day -> additive ~ compounded).
    """
    if trades_df.empty:
        return pd.Series(dtype=float)
    exit_day = trades_df["exit_time"].dt.normalize()
    daily = trades_df.groupby(exit_day)["ret_frac"].sum()
    daily.index = daily.index.tz_convert("UTC") if daily.index.tz is not None else daily.index

    first = trades_df["exit_time"].min().normalize()
    last  = trades_df["exit_time"].max().normalize()
    span  = daily_index[(daily_index >= first) & (daily_index <= last)]
    return daily.reindex(span, fill_value=0.0)


def equity_from_returns(daily_ret: pd.Series) -> pd.Series:
    return (1.0 + daily_ret).cumprod()


def de_overlap(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce ONE position at a time. Trades are simulated independently, then this
    greedily keeps a non-overlapping sequence: after keeping a trade, skip any
    candidate whose entry starts before that trade exits. Realistic for a single
    account that cannot hold two positions at once.
    """
    if trades_df.empty:
        return trades_df
    df = trades_df.sort_values("entry_time").reset_index(drop=True)
    keep = []
    free_at = pd.Timestamp.min.tz_localize("UTC")
    for _, r in df.iterrows():
        if r["entry_time"] >= free_at:
            keep.append(r)
            free_at = r["exit_time"]
    return pd.DataFrame(keep).sort_values("exit_time").reset_index(drop=True)


def build_position_series(trades_df: pd.DataFrame, exec_index: pd.DatetimeIndex) -> pd.Series:
    """
    Held-position series on the execution timeframe: +1 while in a long trade,
    -1 while short, 0 flat. Used for the look-ahead guard — a held position must
    not correlate >0.5 with same/next-bar returns (which would betray a future leak
    in trade resolution).
    """
    pos = pd.Series(0.0, index=exec_index)
    if trades_df.empty:
        return pos
    for _, r in trades_df.iterrows():
        mask = (exec_index > r["entry_time"]) & (exec_index <= r["exit_time"])
        pos.loc[mask] = 1.0 if r["side"] == "long" else -1.0
    return pos
