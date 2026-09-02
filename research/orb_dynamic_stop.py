#!/usr/bin/env python3
"""
orb_dynamic_stop.py -- bar-by-bar resolution for exit rules research.ftmo_engine
.simulate_trades CANNOT express: a stop that MOVES during the trade (breakeven,
trailing). simulate_trades is vectorized around a FIXED stop + FIXED target
(searchsorted over the whole [entry, session_end) window in one shot) -- there is
no way to feed it a stop that changes mid-trade, so a genuine bar-by-bar loop is
required here. Candidates are the SAME orb(..., retest=True) output used
everywhere else in sec 10.5/10.6 (entry_time, side, entry_mid, stop, session_end
-- the `target` field is ignored by both modes below, since neither uses a fixed
target).

CAUSALITY / CONSERVATIVE-TIE convention (matches research/ftmo_engine.py exactly):
  On each bar, the OLD (pre-this-bar) stop is checked FIRST. Only if it is not
  hit does the bar's own high/low get used to (a) decide whether the stop should
  now move (breakeven activation / trailing update) for bars AFTER this one, and
  such a move never retroactively saves a trade that hit the old stop in the same
  bar. This is the identical "stop-first, same-bar ties resolved conservatively"
  rule research/ftmo_engine.simulate_trades already uses -- no look-ahead is
  introduced by moving the stop with information available strictly at or before
  the bar being evaluated.

MODE "breakeven": once price first moves RISK (1R) in the trade's favor (checked
  via that bar's high/low), the stop moves to entry_mid exactly once and never
  moves again. No fixed target -- the trade rides to session close or the
  (possibly breakeven) stop.

MODE "trailing": tracks the best favorable excursion (running high for a long,
  running low for a short) from entry. Once that excursion first reaches RISK
  (1R) in favor, trailing activates; from then on the stop is
  max(current_stop, excursion - TRAIL_FRAC*RISK) for a long (min/+ for a short),
  i.e. it only ever tightens toward price, never loosens. No fixed target.

Cost model: byte-identical to research.ftmo_engine.simulate_trades -- real spread
at the entry minute + commission + per-side slippage (legacy $/oz XAUUSD model
when cost_bps is None, or the bps-of-price model otherwise), so net_R here is
directly comparable to every other cell in STATE_OF_PLAY sec 10/10.5/10.6.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.ftmo_engine import COMMISSION_PER_OZ, _slip_per_side, _in_news

TRAIL_FRAC_DEFAULT = 0.5   # trailing stop distance behind the extreme, in R


def resolve_dynamic_stop_trades(
    m1_mid: pd.DataFrame,
    trades: list[dict],
    mode: str,
    trail_frac: float = TRAIL_FRAC_DEFAULT,
    cost_bps: dict | None = None,
    slip_bps_fn=None,
) -> pd.DataFrame:
    """mode: 'breakeven' or 'trailing'. Returns the same schema as
    research.ftmo_engine.simulate_trades (entry_time, exit_time, side, reason,
    entry_mid, exit_mid, risk_price, gross_R, cost_R, net_R, ret_frac), plus
    `reason` values 'stop' (never activated, hit the original OR stop),
    'breakeven' / 'trail' (hit the MOVED stop), 'time' (session close).
    """
    assert mode in ("breakeven", "trailing")
    idx = m1_mid.index
    ts_ns = idx.tz_localize(None).values.astype("datetime64[ns]").view("int64")
    lows = m1_mid["mid_low"].to_numpy()
    highs = m1_mid["mid_high"].to_numpy()
    closes = m1_mid["mid_close"].to_numpy()
    spreads = m1_mid["spread"].to_numpy()
    n = len(idx)

    rows = []
    for tr in trades:
        entry_time = tr["entry_time"]
        side = tr["side"]
        entry_mid = float(tr["entry_mid"])
        stop0 = float(tr["stop"])
        sess_end = tr["session_end"]

        risk = (entry_mid - stop0) if side == "long" else (stop0 - entry_mid)
        if risk <= 0:
            continue

        entry_ns = pd.Timestamp(entry_time).tz_convert(None).value
        end_ns = pd.Timestamp(sess_end).tz_convert(None).value
        start = int(np.searchsorted(ts_ns, entry_ns, side="left"))
        end = int(np.searchsorted(ts_ns, end_ns, side="right"))
        if start >= n or start >= end:
            continue

        stop = stop0
        activated = False
        extreme = entry_mid           # only meaningful once trailing is activated
        exit_i = exit_mid = reason = None

        for i in range(start, end):
            lo, hi = lows[i], highs[i]
            # 1) OLD stop, checked FIRST (conservative, matches simulate_trades).
            if side == "long":
                if lo <= stop:
                    exit_i, exit_mid = i, stop
                    reason = "stop" if not activated else ("breakeven" if mode == "breakeven" else "trail")
                    break
            else:
                if hi >= stop:
                    exit_i, exit_mid = i, stop
                    reason = "stop" if not activated else ("breakeven" if mode == "breakeven" else "trail")
                    break

            # 2) update stop for FUTURE bars only, from THIS bar's own range.
            if mode == "breakeven":
                if not activated:
                    if side == "long" and hi >= entry_mid + risk:
                        stop, activated = entry_mid, True
                    elif side == "short" and lo <= entry_mid - risk:
                        stop, activated = entry_mid, True
            else:  # trailing
                if side == "long":
                    if hi > extreme:
                        extreme = hi
                    if not activated and extreme >= entry_mid + risk:
                        activated = True
                    if activated:
                        cand = extreme - trail_frac * risk
                        if cand > stop:
                            stop = cand
                else:
                    if lo < extreme:
                        extreme = lo
                    if not activated and extreme <= entry_mid - risk:
                        activated = True
                    if activated:
                        cand = extreme + trail_frac * risk
                        if cand < stop:
                            stop = cand
        else:
            exit_i = end - 1
            exit_mid = float(closes[exit_i])
            reason = "time"

        gross_R = ((exit_mid - entry_mid) if side == "long"
                   else (entry_mid - exit_mid)) / risk

        spread_at_entry = float(spreads[start])
        if cost_bps is None:
            cost_price = spread_at_entry + 2.0 * _slip_per_side(entry_time) + COMMISSION_PER_OZ
        else:
            slip_side = (slip_bps_fn(entry_time) if slip_bps_fn is not None
                         else (cost_bps["slip_news"] if _in_news(entry_time)
                               else cost_bps["slip_normal"]))
            total_bps = (spread_at_entry / entry_mid) * 1e4 + cost_bps["commission"] + 2.0 * slip_side
            cost_price = total_bps / 1e4 * entry_mid
        cost_R = cost_price / risk
        net_R = gross_R - cost_R

        rows.append({
            "entry_time": entry_time, "exit_time": idx[exit_i], "side": side,
            "reason": reason, "entry_mid": entry_mid, "exit_mid": exit_mid,
            "risk_price": risk, "gross_R": gross_R, "cost_R": cost_R,
            "net_R": net_R, "ret_frac": 0.01 * net_R,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("exit_time").reset_index(drop=True)
    return df
