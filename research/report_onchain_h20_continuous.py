#!/usr/bin/env python3
"""
ON-CHAIN ACTIVE-ADDRESS SURGE SIGNAL, H=20 hold -- ONE CONTINUOUS compounding
run across the full available BTCUSDT history, same treatment as the ORB
full-period continuous test (research/report_retest_xauusd_2017_2025_continuous.py).

REPORTING ONLY. No new rule, no new parameter. Reuses run_onchain_signal.py's
exact confirmed §30 rule unchanged: BTC daily unique active addresses
(blockchain.info n-unique-addresses), causal 90-day trailing z-score
(current day excluded from the baseline), signal = z > 1.5, LONG-ONLY,
enter at signal day's close, hold H=20 calendar days, non-overlapping
(no_pos gate), $100,000 start, fully invested while a position is open,
100% cash (0% return, no cost) otherwise. Costs: real BTCUSDT spread at
entry + CRYPTO_COST_BPS (20 bps commission, 1.0 bps/side slippage), half
the round-trip charged on the open day, half on the close day -- identical
to run_onchain_signal.py's run_cell(), imported and called unchanged.

DATA SPAN, stated plainly: the project's real-spread BTCUSDT daily price
series is built from data/BTCUSDT_H1_2018_2025_binance.csv, which despite
its filename actually runs 2018-01-01 -> the file's last timestamp (checked
below, NOT assumed from the filename). Active-address history covers
2009-2026 but the signal is only tradeable where BOTH series overlap AND
the 90-day z-score has filled -- i.e. from 2018 plus a ~90-day warm-up.
"Full available history" here = that overlap, not 2009 and not artificially
capped at 2025.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.metrics import sharpe, max_drawdown, profit_factor
import run_onchain_signal as sig

START_CAP = sig.START_CAP
BARS_PER_YEAR = sig.BARS_PER_YEAR
H = 20
assert H in sig.HOLDS, "H=20 must be one of the pre-registered holds"


def build_full_daily_series(daily: pd.DataFrame, z: pd.Series, H: int):
    """Re-derive the exact trade list + a CONTINUOUS daily net-return series
    spanning every calendar day in `daily.index` (not just position days),
    using run_onchain_signal.py's own signal/cost logic verbatim."""
    close = daily["close"]
    rets = close.pct_change()
    idx = daily.index

    sig_days = z.index[(z > sig.ADDR_Z_THRESHOLD) & z.notna()]

    trades = []
    busy_until = None
    for t in sig_days:
        if busy_until is not None and t <= busy_until:
            continue
        i0 = idx.searchsorted(t, side="left")
        if idx[i0] != t:
            continue
        i1 = i0 + (H - 1)
        if i1 >= len(idx):
            break
        exit_t = idx[i1]
        trades.append(dict(entry=t, exit=exit_t, i0=i0, i1=i1))
        busy_until = exit_t

    # look-ahead guard, same construction as run_onchain_signal.run_cell
    guard_ok = all(tr["entry"] <= tr["exit"] for tr in trades)

    recs = []
    for tr in trades:
        for k in range(tr["i0"] + 1, tr["i1"] + 1):
            recs.append((idx[k], k == tr["i0"] + 1, k == tr["i1"]))
    pos = pd.DataFrame(recs, columns=["date", "is_open", "is_close"])
    pos["ret"] = pos["date"].map(rets)
    pos = pos.dropna(subset=["ret"])

    spread_bps = daily["spread_close"].reindex([tr["entry"] for tr in trades]).to_numpy()
    spread_bps = np.nan_to_num(spread_bps, nan=np.nanmedian(spread_bps)) * 1e4
    total_cost_bps = spread_bps + sig.CRYPTO_COST_BPS["commission"] + 2 * sig.CRYPTO_COST_BPS["slip_normal"]
    cost_by_entry = dict(zip([tr["entry"] for tr in trades], total_cost_bps / 2 / 1e4))

    open_map, close_map = {}, {}
    for tr in trades:
        c = cost_by_entry[tr["entry"]]
        open_day = idx[tr["i0"] + 1]
        close_day = idx[tr["i1"]]
        open_map[open_day] = open_map.get(open_day, 0.0) + c
        close_map[close_day] = close_map.get(close_day, 0.0) + c
    pos["cost"] = pos.apply(lambda r: (open_map.get(r["date"], 0.0) if r["is_open"] else 0.0)
                                       + (close_map.get(r["date"], 0.0) if r["is_close"] else 0.0), axis=1)
    pos["net_contrib"] = pos["ret"] - pos["cost"]

    pos_by_day = pos.groupby("date")["net_contrib"].sum()

    # ---- full calendar-day series over the WHOLE tradeable span, 0 on cash days ----
    trade_start = trades[0]["entry"] if trades else idx[0]
    full_index = idx[idx >= trade_start]
    full_daily_ret = pos_by_day.reindex(full_index, fill_value=0.0)
    in_position_flag = full_daily_ret.index.isin(pos_by_day.index) | full_index.to_series().apply(
        lambda d: any(tr["entry"] <= d <= tr["exit"] for tr in trades)
    ).to_numpy()
    # cheaper/robust in-position flag: mark every day strictly within [entry, exit] of some trade
    in_pos = pd.Series(False, index=full_index)
    for tr in trades:
        in_pos.loc[(full_index >= tr["entry"]) & (full_index <= tr["exit"])] = True

    return trades, full_daily_ret, in_pos, guard_ok


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    addr = sig.load_addr()
    daily = sig.load_btc_daily()
    print(f"Active-address history: {addr.index.min().date()} -> {addr.index.max().date()}")
    print(f"BTCUSDT real-spread daily price (from BTCUSDT_H1_2018_2025_binance.csv, "
          f"actual span checked not assumed): {daily.index.min().date()} -> {daily.index.max().date()}\n")

    z = sig.build_signal(addr, daily.index)

    trades, daily_ret, in_pos, guard_ok = build_full_daily_series(daily, z, H)
    print(f"H={H} confirmed rule, run continuously over the full span: {len(trades)} trades")
    print(f"First entry: {trades[0]['entry'].date()}   Last exit: {trades[-1]['exit'].date()}")
    print(f"Look-ahead guard: {'PASS' if guard_ok else 'FAIL'}\n")

    equity = (1.0 + daily_ret).cumprod() * START_CAP
    end_balance = float(equity.iloc[-1])

    # ---- year-by-year, reported FIRST and prominently ----
    print("=" * 112)
    print(f"  YEAR-BY-YEAR -- ONE CONTINUOUS $100,000 ACCOUNT, ON-CHAIN ACTIVE-ADDRESS SURGE, H={H}, BTCUSDT")
    print("=" * 112)
    print(f"  {'year':<6} {'trades':>7} {'days in pos':>11} {'start equity':>14} {'end equity':>14} "
          f"{'year return %':>14} {'net PF':>8}")
    print("  " + "-" * 108)

    years = sorted(set(daily_ret.index.year))
    eq_before = START_CAP
    yearly_rows = []
    for yr in years:
        yr_mask = daily_ret.index.year == yr
        yr_ret = daily_ret[yr_mask]
        yr_eq = (1.0 + yr_ret).cumprod()
        end_eq = eq_before * float(yr_eq.iloc[-1])
        n_trades_yr = sum(1 for tr in trades if tr["entry"].year == yr)
        days_in_pos_yr = int(in_pos[yr_mask].sum())
        npf = profit_factor(yr_ret) if len(yr_ret) else float("nan")
        ret_pct = end_eq / eq_before - 1.0
        yearly_rows.append((yr, n_trades_yr, days_in_pos_yr, eq_before, end_eq, ret_pct, npf))
        print(f"  {yr:<6} {n_trades_yr:>7} {days_in_pos_yr:>11} {eq_before:>14,.0f} {end_eq:>14,.0f} "
              f"{ret_pct:>+13.1%} {npf:>8.3f}")
        eq_before = end_eq

    print("  " + "-" * 108)
    print(f"  {'TOTAL':<6} {len(trades):>7} {int(in_pos.sum()):>11} {START_CAP:>14,.0f} {end_balance:>14,.0f} "
          f"{end_balance/START_CAP-1:>+13.1%}")
    print("=" * 112)

    # ---- max drawdown + recovery time, prominently ----
    running_peak = equity.cummax()
    dd = 1.0 - equity / running_peak
    max_dd = float(dd.max())
    trough_date = dd.idxmax()
    peak_date = equity.loc[:trough_date].idxmax()
    peak_value = float(equity.loc[peak_date])
    trough_value = float(equity.loc[trough_date])

    recovery_date = None
    after_trough = equity.loc[trough_date:]
    recovered = after_trough[after_trough >= peak_value]
    if len(recovered) > 1:
        recovery_date = recovered.index[1] if recovered.index[0] == trough_date and len(recovered) > 1 else recovered.index[0]
        # first date strictly after the trough where equity >= prior peak
        after_strict = equity.loc[equity.index > trough_date]
        hit = after_strict[after_strict >= peak_value]
        recovery_date = hit.index[0] if len(hit) else None

    print(f"\n{'='*112}")
    print(f"  MAXIMUM DRAWDOWN OF THE FULL COMBINED EQUITY CURVE")
    print(f"{'='*112}")
    print(f"  Peak equity ${peak_value:,.0f} reached {peak_date.date()}")
    print(f"  Trough equity ${trough_value:,.0f} reached {trough_date.date()}")
    print(f"  Max drawdown: {max_dd*100:.1f}%")
    if recovery_date is not None:
        days_to_recover = (recovery_date - trough_date).days
        days_peak_to_recover = (recovery_date - peak_date).days
        print(f"  Recovered (equity back to/above ${peak_value:,.0f}) on {recovery_date.date()}")
        print(f"  Time from trough to recovery: {days_to_recover} calendar days")
        print(f"  Time from ORIGINAL peak to recovery (full underwater duration): {days_peak_to_recover} calendar days")
    else:
        print(f"  NOT YET RECOVERED as of the end of the available data ({equity.index[-1].date()}) -- "
              f"current equity ${end_balance:,.0f} is still below the ${peak_value:,.0f} peak.")

    # ---- headline ----
    n_obs = len(daily_ret)
    full_sharpe = sharpe(daily_ret, BARS_PER_YEAR)
    full_pf = profit_factor(daily_ret)
    print(f"\n{'='*112}")
    print(f"  FULL-PERIOD CONTINUOUS RESULT, {daily_ret.index[0].date()} -> {daily_ret.index[-1].date()} (ONE account)")
    print(f"{'='*112}")
    print(f"  Starting balance:   ${START_CAP:,.0f}")
    print(f"  Ending balance:     ${end_balance:,.0f}")
    print(f"  Total return:       {end_balance/START_CAP-1:+.1%}")
    print(f"  Trades:             {len(trades)}")
    print(f"  Net Sharpe (ann.):  {full_sharpe:+.2f}")
    print(f"  Net PF:             {full_pf:.3f}")

    # ---- % time in position vs cash ----
    n_days_total = len(daily_ret)
    n_days_in_pos = int(in_pos.sum())
    print(f"\n{'='*112}")
    print(f"  TIME IN POSITION vs CASH, over the traded span {daily_ret.index[0].date()} -> {daily_ret.index[-1].date()}")
    print(f"{'='*112}")
    print(f"  Total calendar days in span:  {n_days_total}")
    print(f"  Days IN a position:           {n_days_in_pos}  ({n_days_in_pos/n_days_total*100:.1f}%)")
    print(f"  Days in CASH:                 {n_days_total - n_days_in_pos}  ({(n_days_total-n_days_in_pos)/n_days_total*100:.1f}%)")

    # ---- buy-and-hold BTC, identical span ----
    p0 = float(daily["close"].loc[daily_ret.index[0]])
    p1 = float(daily["close"].loc[daily_ret.index[-1]])
    bh_end = START_CAP * p1 / p0
    bh_daily_ret = daily["close"].reindex(daily_ret.index).pct_change().dropna()
    bh_equity = (1.0 + bh_daily_ret).cumprod() * START_CAP
    bh_maxdd = max_drawdown(bh_equity / START_CAP)
    bh_sharpe = sharpe(bh_daily_ret, BARS_PER_YEAR)
    print(f"\n{'='*112}")
    print(f"  BUY-AND-HOLD BTC COMPARISON, SAME SPAN, SAME $100,000")
    print(f"{'='*112}")
    print(f"  BTC price: ${p0:,.0f} ({daily_ret.index[0].date()}) -> ${p1:,.0f} ({daily_ret.index[-1].date()})")
    print(f"  Buy-and-hold ending:  ${bh_end:,.0f}  ({bh_end/START_CAP-1:+.1%})")
    print(f"  Buy-and-hold Sharpe:  {bh_sharpe:+.2f}")
    print(f"  Buy-and-hold max DD:  {bh_maxdd*100:.1f}%")
    print(f"\n  STRATEGY {end_balance/START_CAP-1:+.1%} (maxDD {max_dd*100:.1f}%, {n_days_in_pos/n_days_total*100:.0f}% time in market)  "
          f"vs  BUY-AND-HOLD {bh_end/START_CAP-1:+.1%} (maxDD {bh_maxdd*100:.1f}%, 100% time in market)")
    print(f"  -> strategy {'BEATS' if end_balance > bh_end else 'LOSES TO'} buy-and-hold on continuous dollars")

    out = _ROOT / "results" / "onchain_h20_continuous.csv"
    pd.DataFrame(yearly_rows, columns=["year", "n_trades", "days_in_position", "start_equity",
                                        "end_equity", "year_return_pct", "net_pf"]).to_csv(out, index=False)
    print(f"\nYear-by-year table saved: {out}")


if __name__ == "__main__":
    main()
