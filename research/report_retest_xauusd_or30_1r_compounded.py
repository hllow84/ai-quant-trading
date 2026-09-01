#!/usr/bin/env python3
"""
Reporting only -- NO new backtest. Re-materialises the deterministic trade log
for the ONE cell "RETEST, XAUUSD, OR30, target=1R" (the best-variant cell in
STATE_OF_PLAY section 10.5), then compounds 1% risk per trade from $100,000 over
three date ranges, each next to a buy-and-hold of XAUUSD over the identical range.

The trade list is produced by the exact same objects the section-10.5 run used
(strategies.orb.orb(..., retest=True) + research.ftmo_engine.simulate_trades +
de_overlap), so it is the actual trade log behind results/orb_entry_filters*.csv,
not a re-estimate. A hard check against the scored CSV (n_trades, net_R_total)
asserts it reproduces.

Pre-2018 XAUUSD: there is NO XAUUSD M1 (or spot) on disk before 2018, so the
strategy CANNOT be run 2013-2017 -- stated, not faked. The 2013-2017
buy-and-hold row uses GLD (the gold ETF) daily total price as the gold-return
proxy, flagged as such.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot
from research.ftmo_engine import simulate_trades, de_overlap, RISK_PER_TRADE
from strategies.orb import orb, ET

M1_PATH = _ROOT / "data" / "XAUUSD_M1_2018_2025_spot_dukascopy.csv"
GLD_PATH = _ROOT / "data" / "GLD_daily_yfinance.csv"
SCORED = _ROOT / "results" / "orb_entry_filters_scored.csv"
START_CAP = 100_000.0

ET_SESSION = dict(session_tz=ET, open_min=9 * 60 + 30, close_min=16 * 60, min_sess_bars=300)
PARAMS = dict(or_minutes=30, target="1R", stop_mode="or_range")

PERIODS = [
    ("FULL 2018-01-01..2025-12-31", "2018-01-01", "2025-12-31"),
    ("OUT-OF-REGIME 2013-01-01..2017-12-31", "2013-01-01", "2017-12-31"),
    ("RECENT 2022-01-01..2025-12-31", "2022-01-01", "2025-12-31"),
]


def build_trades() -> pd.DataFrame:
    spot = load_m1_spot(M1_PATH)
    m1 = pd.DataFrame(index=spot.index)
    for c in ("open", "high", "low", "close"):
        m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
    m1["spread"] = spot["spread"]
    m1["volume"] = spot["volume"]

    cands = orb(m1, PARAMS, retest=True, retest_tol_frac=0.10, **ET_SESSION)
    trades = de_overlap(simulate_trades(m1, cands, strictly_after=False,
                                        cost_bps=None, slip_bps_fn=None))
    trades["entry_time"] = pd.to_datetime(trades["entry_time"], utc=True)
    trades["exit_time"] = pd.to_datetime(trades["exit_time"], utc=True)
    trades = trades.sort_values("exit_time").reset_index(drop=True)

    # hard reproduction check against the scored CSV
    row = pd.read_csv(SCORED).query(
        "instrument=='XAUUSD' and or_minutes==30 and target=='1R' and variant=='RETEST'").iloc[0]
    assert len(trades) == int(row["n_trades"]), (len(trades), row["n_trades"])
    assert abs(trades["net_R"].sum() - row["net_R_total"]) < 1e-6, (
        trades["net_R"].sum(), row["net_R_total"])
    print(f"reproduction check OK: {len(trades)} trades, "
          f"net_R total {trades['net_R'].sum():.6f} == scored CSV\n")
    return trades, m1


def compound(net_R: pd.Series) -> float:
    eq = START_CAP
    for r in net_R.to_numpy():
        eq *= (1.0 + RISK_PER_TRADE * r)
    return eq


def bh_xauusd_m1(m1: pd.DataFrame, a: str, b: str):
    seg = m1.loc[(m1.index >= pd.Timestamp(a, tz="UTC")) & (m1.index <= pd.Timestamp(b, tz="UTC"))]
    if seg.empty:
        return None
    p0, p1 = float(seg["mid_close"].iloc[0]), float(seg["mid_close"].iloc[-1])
    return START_CAP * p1 / p0, p0, p1, seg.index[0].date(), seg.index[-1].date()


def bh_gld(a: str, b: str):
    g = pd.read_csv(GLD_PATH, parse_dates=["date"]).set_index("date").sort_index()
    seg = g.loc[a:b]
    p0, p1 = float(seg["close"].iloc[0]), float(seg["close"].iloc[-1])
    return START_CAP * p1 / p0, p0, p1, seg.index[0].date(), seg.index[-1].date()


def main():
    trades, m1 = build_trades()
    # XAUUSD ORB is intraday (force-flat at the cash close), so entry date == exit date.
    tdate = trades["entry_time"].dt.tz_convert(ET).dt.normalize()

    rows = []
    for label, a, b in PERIODS:
        lo = pd.Timestamp(a, tz=ET)
        hi = pd.Timestamp(b, tz=ET) + pd.Timedelta(days=1)
        seg = trades[(tdate >= lo) & (tdate < hi)]

        if len(seg) == 0 and a.startswith("2013"):
            rows.append((label, "STRATEGY (RETEST XAUUSD OR30/1R)", START_CAP, None,
                         None, "no XAUUSD M1 on disk before 2018 -- cannot run"))
        else:
            end_eq = compound(seg["net_R"])
            rows.append((label, "STRATEGY (RETEST XAUUSD OR30/1R)", START_CAP, end_eq,
                         len(seg), f"{seg['entry_time'].dt.date.min()}..{seg['entry_time'].dt.date.max()}"))

        if a.startswith("2013"):
            eq, p0, p1, d0, d1 = bh_gld(a, b)
            rows.append((label, "BUY & HOLD gold (GLD ETF proxy)", START_CAP, eq, None,
                         f"GLD {p0:.2f} ({d0}) -> {p1:.2f} ({d1})"))
        else:
            eq, p0, p1, d0, d1 = bh_xauusd_m1(m1, a, b)
            rows.append((label, "BUY & HOLD XAUUSD (M1 mid)", START_CAP, eq, None,
                         f"${p0:,.2f} ({d0}) -> ${p1:,.2f} ({d1})"))

    W = 118
    print("=" * W)
    print("  RETEST on XAUUSD OR30 / target 1R  --  1% risk/trade compounded from $100,000, vs buy-and-hold XAUUSD")
    print("  Trade log = the actual deterministic output behind results/orb_entry_filters_scored.csv (reproduction-checked).")
    print("  Compounding = equity *= (1 + 0.01 * net_R) per trade, in chronological (exit-time) order. Costs in net_R:")
    print("  real per-bar spread + $0.03/$0.10 per-side slippage + $0.07/oz commission (engine legacy $/oz model).")
    print("=" * W)
    hdr = f"  {'period':<38} {'line':<34} {'start $':>12} {'end $':>14} {'total %':>10} {'trades':>7}"
    print(hdr)
    print("  " + "-" * (W - 4))
    for label, line, s, e, n, note in rows:
        if e is None:
            print(f"  {label:<38} {line:<34} {s:>12,.0f} {'n/a':>14} {'n/a':>10} {'n/a':>7}")
        else:
            print(f"  {label:<38} {line:<34} {s:>12,.0f} {e:>14,.0f} {e/s-1:>+9.1%} "
                  f"{('' if n is None else n):>7}")
        print(f"  {'':<38} {'  -> ' + note}")
    print("=" * W)

    # plain 6-row summary table
    print("\n  SUMMARY TABLE (6 rows: 3 periods x strategy / buy-and-hold)\n")
    print(f"  {'period':<34} {'approach':<32} {'starting':>10} {'ending':>13} {'return %':>10} {'trades':>7}")
    print("  " + "-" * 110)
    for label, line, s, e, n, note in rows:
        per = label.split()[0] + " " + label.split()[1].split("..")[0].replace("2013-01-01", "2013-2017") \
            .replace("2018-01-01", "2018-2025").replace("2022-01-01", "2022-2025")
        appr = "strategy" if line.startswith("STRATEGY") else "buy & hold"
        if e is None:
            print(f"  {per:<34} {appr:<32} {s:>10,.0f} {'--':>13} {'--':>10} {'--':>7}")
        else:
            print(f"  {per:<34} {appr:<32} {s:>10,.0f} {e:>13,.0f} {e/s-1:>+9.1%} "
                  f"{('' if n is None else str(n)):>7}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
