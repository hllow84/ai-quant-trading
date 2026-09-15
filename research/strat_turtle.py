#!/usr/bin/env python3
"""
STRATEGY 5 -- TURTLE TRADING SYSTEM, the classic documented rules (Faith,
"The Original Turtle Trading Rules"), daily bars, all 7 instruments.

RULE, stated before running, every parameter from the ORIGINAL documented
system, none re-tuned:
  N (volatility unit)   = ATR(20), Wilder-style true range average (the
                          Turtles' own "N", 20-day, not the more common
                          14-day ATR -- this IS the documented value).
  SYSTEM 1 ENTRY        = 20-day Donchian breakout (close > 20-day high ->
                          long; close < 20-day low -> short).
  SYSTEM 1 SKIP FILTER  = the documented "skip the last breakout if it was
                          a winner" whipsaw filter is included as originally
                          specified (a System-1 breakout is skipped if the
                          IMMEDIATELY PRIOR System-1 trade in the same
                          direction was a winner; System-2 signals are
                          always taken regardless). Per the documented rule,
                          only ONE breakout is skipped after a winner -- the
                          NEXT breakout in that direction is taken
                          unconditionally, so a single winning trade cannot
                          permanently lock a direction out (a bug found and
                          fixed during this run: an earlier version left the
                          "last was a winner" flag set on a skipped
                          breakout, which silently blocked all future
                          entries in that direction -- confirmed on ETHUSDT
                          System 1, which flat-lined for 8 straight years
                          after its one 2018 trade until this fix).
  SYSTEM 2 ENTRY        = 55-day Donchian breakout, ALWAYS taken (no skip
                          filter -- documented System 2 rule).
  BOTH TESTED, reported separately, per the task's explicit instruction.
  POSITION SIZE (1 UNIT)= 1% of account equity risked per N, i.e.
                          unit_size = (0.01 * equity) / (N * dollar_per_point).
                          For a directly-tradeable index/FX/crypto price
                          series (not futures contracts with a stated point
                          value), dollar_per_point is treated as 1 unit of
                          the underlying per "N" of price movement -- this
                          is the standard adaptation of Turtle sizing to a
                          CFD/spot instrument (documented Turtle sizing was
                          built for futures contracts; the $-per-N logic is
                          preserved, the contract-multiplier specifics are
                          not applicable here and are stated as an honest
                          adaptation, not a hidden assumption).
  PYRAMIDING             = add 1 unit every 0.5N of favorable movement, up
                          to a documented MAX of 4 units total per market.
  STOP                   = 2N from the unit's own entry price (documented
                          value), trailing per-unit; the WHOLE position
                          exits when the FIRST (oldest) unit's 2N stop is
                          hit (simplification of the original's per-unit
                          stop-adjustment rule, stated).
  EXIT (non-stop)         = System 1 exits on a 10-day Donchian
                          countertrend breach; System 2 exits on a 20-day
                          countertrend breach (documented values).

LOOK-AHEAD: all Donchian/ATR values use .shift(1) (yesterday's completed
channel), so day t's entry decision never uses day t's own high/low/close.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.six_strategies_engine import (
    load_daily, ALL_INSTRUMENTS, REAL_OOS_SPLIT, drawdown_with_recovery, year_table,
    top_year_concentration, bh_stats, START_CAP, BARS_PER_YEAR, RISK_PER_TRADE,
)
from research.metrics import sharpe, max_drawdown, profit_factor

N_LEN = 20
MAX_UNITS = 4
PYRAMID_STEP_N = 0.5
STOP_N = 2.0
UNIT_RISK_PCT = 0.01


def atr_n(daily: pd.DataFrame, length: int = N_LEN) -> pd.Series:
    high, low, close = daily["high"], daily["low"], daily["close"]
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / length, adjust=False, min_periods=length).mean()


def run_system(daily: pd.DataFrame, entry_len: int, exit_len: int, skip_filter: bool) -> dict:
    close, high, low = daily["close"], daily["high"], daily["low"]
    n_val = atr_n(daily).shift(1)  # yesterday's completed N
    entry_hi = high.rolling(entry_len).max().shift(1)
    entry_lo = low.rolling(entry_len).min().shift(1)
    exit_hi = high.rolling(exit_len).max().shift(1)
    exit_lo = low.rolling(exit_len).min().shift(1)
    idx = daily.index

    equity = START_CAP
    equity_path = np.full(len(idx), START_CAP)
    units = []  # list of dicts: entry_price, side
    side = 0
    last_signal_was_winner = {"long": None, "short": None}
    entry_price_first = None

    for i in range(len(idx)):
        c, h, l = close.iloc[i], high.iloc[i], low.iloc[i]
        n = n_val.iloc[i]
        day_pnl_frac = 0.0

        if units:
            # mark-to-market all units at today's close vs yesterday's close
            prev_c = close.iloc[i - 1] if i > 0 else c
            for u in units:
                move = (c - prev_c) if u["side"] == "long" else (prev_c - c)
                day_pnl_frac += (move / n if n and np.isfinite(n) and n > 0 else 0.0) * UNIT_RISK_PCT

            stop_price = units[0]["entry_price"] - STOP_N * n if units[0]["side"] == "long" else units[0]["entry_price"] + STOP_N * n
            hit_stop = (l <= stop_price) if units[0]["side"] == "long" else (h >= stop_price)
            hit_exit = (c <= exit_lo.iloc[i]) if units[0]["side"] == "long" else (c >= exit_hi.iloc[i])

            if np.isfinite(stop_price) and (hit_stop or (np.isfinite(exit_lo.iloc[i]) and hit_exit)):
                winner = c > units[0]["entry_price"] if units[0]["side"] == "long" else c < units[0]["entry_price"]
                last_signal_was_winner[units[0]["side"]] = bool(winner)
                units = []
                side = 0
            elif np.isfinite(n) and n > 0:
                last_add = units[-1]["entry_price"]
                if side == "long" and len(units) < MAX_UNITS and c >= last_add + PYRAMID_STEP_N * n:
                    units.append(dict(entry_price=c, side="long"))
                elif side == "short" and len(units) < MAX_UNITS and c <= last_add - PYRAMID_STEP_N * n:
                    units.append(dict(entry_price=c, side="short"))

        if not units and np.isfinite(n) and n > 0 and np.isfinite(entry_hi.iloc[i]):
            go_long = c > entry_hi.iloc[i]
            go_short = c < entry_lo.iloc[i]
            if go_long or go_short:
                d = "long" if go_long else "short"
                take = True
                if skip_filter and last_signal_was_winner[d] is True:
                    take = False
                    # documented rule: skip ONE breakout after a winner, then the
                    # NEXT breakout in that direction is taken regardless of
                    # outcome -- otherwise a lone winner would lock the direction
                    # out forever, which is not the Turtle rule.
                    last_signal_was_winner[d] = None
                if take:
                    units = [dict(entry_price=c, side=d)]
                    side = 1 if d == "long" else -1

        equity *= (1.0 + day_pnl_frac)
        equity_path[i] = equity

    equity_s = pd.Series(equity_path, index=idx)
    daily_ret = equity_s.pct_change().fillna(0.0)
    return dict(equity=equity_s, daily_ret=daily_ret)


def report(label: str, daily: pd.DataFrame, entry_len: int, exit_len: int, skip_filter: bool, oos_split=None) -> dict:
    out = run_system(daily, entry_len, exit_len, skip_filter)
    equity, daily_ret = out["equity"], out["daily_ret"]
    dd = drawdown_with_recovery(equity)
    yt = year_table(daily_ret, equity)
    conc = top_year_concentration(yt)
    bh = bh_stats(daily)
    end_bal = float(equity.iloc[-1])
    r = dict(label=label, start=daily.index[0], end=daily.index[-1],
             end_balance=end_bal, total_return=end_bal / START_CAP - 1,
             sharpe=sharpe(daily_ret, BARS_PER_YEAR), net_pf=profit_factor(daily_ret),
             max_dd=dd["max_dd"], peak_date=dd["peak_date"], trough_date=dd["trough_date"],
             recovery_date=dd["recovery_date"], top_year_conc=conc,
             concentrated=bool(np.isfinite(conc) and conc > 0.60),
             bh_ending=bh["ending"], bh_total_ret=bh["total_ret"], bh_sharpe=bh["sharpe"], bh_max_dd=bh["max_dd"],
             beats_bh=bool(end_bal > bh["ending"]), yearly=yt)
    if oos_split is not None:
        split = pd.Timestamp(oos_split, tz=daily_ret.index.tz)
        is_ret = daily_ret.loc[daily_ret.index < split]
        oos_ret = daily_ret.loc[daily_ret.index >= split]
        r["oos_sharpe"] = sharpe(oos_ret, BARS_PER_YEAR) if len(oos_ret) > 20 else float("nan")
        r["oos_pf"] = profit_factor(oos_ret) if len(oos_ret) > 5 else float("nan")
        r["oos_holds"] = bool(r["oos_pf"] > 1 and r["oos_sharpe"] > 0) if np.isfinite(r["oos_pf"]) else False

    W = 116
    print("=" * W)
    print(f"  {label}")
    print("=" * W)
    for _, row in yt.iterrows():
        print(f"  {int(row['year']):<6} {row['start_equity']:>14,.0f} {row['end_equity']:>14,.0f} "
              f"{row['year_return_pct']:>+13.1f}%")
    print(f"\n  FULL-PERIOD: ${START_CAP:,.0f} -> ${end_bal:,.0f} ({r['total_return']*100:+.1f}%)   "
          f"Sharpe {r['sharpe']:+.2f}   net PF {r['net_pf']:.3f}")
    print(f"  MAX DRAWDOWN: {r['max_dd']*100:.1f}%  (peak {dd['peak_date'].date()}, trough {dd['trough_date'].date()}"
          + (f", recovered {dd['recovery_date'].date()})" if dd["recovery_date"] is not None else ", NOT recovered)"))
    conc_str = f"{conc*100:.0f}%" if np.isfinite(conc) else "n/a (total<=0)"
    print(f"  TOP-YEAR CONCENTRATION: {conc_str}  -> {'FLAG: concentrated' if r['concentrated'] else 'not concentrated'}")
    print(f"  BUY-AND-HOLD: ${bh['ending']:,.0f} ({bh['total_ret']*100:+.1f}%)  -> strategy "
          f"{'BEATS' if r['beats_bh'] else 'loses to'} B&H")
    if "oos_sharpe" in r:
        print(f"  OUT-OF-REGIME: OOS Sharpe {r['oos_sharpe']:+.2f}  OOS PF {r['oos_pf']:.3f}  -> "
              f"{'HOLDS' if r['oos_holds'] else 'fails'}")
    print()
    return r


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("STRATEGY 5 -- TURTLE TRADING SYSTEM (System 1: 20d entry/10d exit + skip-winner filter; "
          "System 2: 55d entry/20d exit, no filter), N=ATR(20), 2N stop, pyramid to 4 units @ 0.5N\n")
    results = []
    for inst in ALL_INSTRUMENTS:
        daily = load_daily(inst)
        oos = REAL_OOS_SPLIT.get(inst)
        r1 = report(f"TURTLE SYSTEM 1 (20d entry/10d exit, skip-winner filter) -- {inst}", daily, 20, 10, True, oos)
        r2 = report(f"TURTLE SYSTEM 2 (55d entry/20d exit, no filter) -- {inst}", daily, 55, 20, False, oos)
        results.append((inst, "sys1", r1))
        results.append((inst, "sys2", r2))
    return results


if __name__ == "__main__":
    main()
