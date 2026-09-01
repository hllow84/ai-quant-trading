#!/usr/bin/env python3
"""
Reporting only -- NO new backtest. Same exercise as
report_retest_xauusd_or30_1r_compounded.py, for the two US equity indices:

  US100  = NAS100  -- ORB RETEST OR30/1R runnable in BOTH windows (M1 2018-2025
           + M1RTH 2013-2017), so all three periods have a real strategy number.
  S&P500 = SPX500  -- the repo holds SPX500 at H1 only; a 15/30-minute opening
           range CANNOT be built from hourly bars (STATE_OF_PLAY sec 10), so the
           strategy is NOT runnable on it at any resolution. Buy-and-hold IS
           computable from the H1 mid close and is reported for all three ranges.

The NAS100 trade list is re-materialised from the exact objects the sec 10.5 run
used (strategies.orb.orb(..., retest=True) + ftmo_engine.simulate_trades +
de_overlap) and hard-checked against results/orb_entry_filters_scored.csv
(n_trades and net_R_total per window). Then 1% risk per trade is compounded from
$100,000, equity *= (1 + 0.01 * net_R) per trade, chronological (exit) order.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

import run_orb as ro
from research.gold_data import load_m1_spot
from research.ftmo_engine import simulate_trades, de_overlap, RISK_PER_TRADE
from strategies.orb import orb, ET

D = _ROOT / "data"
SCORED = _ROOT / "results" / "orb_entry_filters_scored.csv"
START_CAP = 100_000.0
ET_SESSION = dict(session_tz=ET, open_min=9 * 60 + 30, close_min=16 * 60, min_sess_bars=300)
PARAMS = dict(or_minutes=30, target="1R", stop_mode="or_range")

NAS_IN = D / "NAS100_M1_2018_2025_cfd_dukascopy.csv"
NAS_OUT = D / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv"
SPX_IN = D / "SPX500_H1_2018_2025_cfd_dukascopy.csv"
SPX_OUT = D / "SPX500_H1_2013_2017_cfd_dukascopy.csv"

PERIODS = [
    ("FULL", "2018-2025", "2018-01-01", "2025-12-31"),
    ("OUT-OF-REGIME", "2013-2017", "2013-01-01", "2017-12-31"),
    ("RECENT", "2022-2025", "2022-01-01", "2025-12-31"),
]


def mid_frame(path):
    spot = load_m1_spot(path)
    m = pd.DataFrame(index=spot.index)
    for c in ("open", "high", "low", "close"):
        m[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
    m["spread"] = spot["spread"]
    m["volume"] = spot["volume"]
    return m


def nas_trades(path, window_key):
    m = mid_frame(path)
    cands = orb(m, PARAMS, retest=True, retest_tol_frac=0.10, **ET_SESSION)
    tr = de_overlap(simulate_trades(m, cands, strictly_after=False,
                                    cost_bps=ro.COST_BPS, slip_bps_fn=ro.slip_bps))
    tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True)
    tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True)
    tr = tr.sort_values("exit_time").reset_index(drop=True)
    row = pd.read_csv(SCORED).query(
        f"instrument=='NAS100' and or_minutes==30 and target=='1R' and variant=='RETEST' and window=='{window_key}'"
    ).iloc[0]
    assert len(tr) == int(row["n_trades"]), (window_key, len(tr), row["n_trades"])
    assert abs(tr["net_R"].sum() - row["net_R_total"]) < 1e-6, (window_key, tr["net_R"].sum(), row["net_R_total"])
    print(f"  repro OK [{window_key}]: {len(tr)} trades, net_R total {tr['net_R'].sum():.6f}")
    return tr, m


def compound(net_R):
    eq = START_CAP
    for r in net_R.to_numpy():
        eq *= (1.0 + RISK_PER_TRADE * r)
    return eq


def bh_from_mid(m, a, b):
    seg = m.loc[(m.index >= pd.Timestamp(a, tz="UTC")) & (m.index <= pd.Timestamp(b, tz="UTC"))]
    if seg.empty:
        return None
    p0, p1 = float(seg["mid_close"].iloc[0]), float(seg["mid_close"].iloc[-1])
    return START_CAP * p1 / p0, p0, p1, seg.index[0].date(), seg.index[-1].date()


def load_h1_mid(path):
    df = pd.read_csv(path, parse_dates=["datetime_utc"]).set_index("datetime_utc").sort_index()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    mid = (df["bid_close"] + df["ask_close"]) / 2
    return mid.to_frame("mid_close")


def emit(title, rows):
    print("\n" + "=" * 112)
    print(f"  {title}")
    print("=" * 112)
    print(f"  {'period':<28} {'approach':<34} {'starting':>10} {'ending':>14} {'return %':>10} {'trades':>7}")
    print("  " + "-" * 108)
    for per, appr, s, e, n, note in rows:
        if e is None:
            print(f"  {per:<28} {appr:<34} {s:>10,.0f} {'--':>14} {'--':>10} {'--':>7}")
        else:
            print(f"  {per:<28} {appr:<34} {s:>10,.0f} {e:>14,.0f} {e/s-1:>+9.1%} "
                  f"{('' if n is None else str(n)):>7}")
        print(f"  {'':<28} -> {note}")
    print("=" * 112)


def main():
    # ---------- US100 / NAS100 ----------
    print("Re-materialising NAS100 RETEST OR30/1R trade log ...")
    tr_in, m_in = nas_trades(NAS_IN, "in")
    tr_out, m_out = nas_trades(NAS_OUT, "out")
    di_in = tr_in["entry_time"].dt.tz_convert(ET).dt.normalize()
    di_out = tr_out["entry_time"].dt.tz_convert(ET).dt.normalize()

    nas_rows = []
    for _, plabel, a, b in PERIODS:
        lo, hi = pd.Timestamp(a, tz=ET), pd.Timestamp(b, tz=ET) + pd.Timedelta(days=1)
        if plabel == "2013-2017":
            seg = tr_out[(di_out >= lo) & (di_out < hi)]
            mbh = m_out
            bh_src = "NAS100 M1RTH mid (RTH close sampling)"
        else:
            seg = tr_in[(di_in >= lo) & (di_in < hi)]
            mbh = m_in
            bh_src = "NAS100 M1 mid"
        end_eq = compound(seg["net_R"])
        span = f"{seg['entry_time'].dt.date.min()}..{seg['entry_time'].dt.date.max()}" if len(seg) else "no trades"
        nas_rows.append((f"{plabel}", "strategy (RETEST NAS100 OR30/1R)", START_CAP, end_eq,
                         len(seg), f"trades {span}"))
        eq, p0, p1, d0, d1 = bh_from_mid(mbh, a, b)
        nas_rows.append((f"{plabel}", "buy & hold NAS100", START_CAP, eq, None,
                         f"{bh_src}: {p0:,.1f} ({d0}) -> {p1:,.1f} ({d1})"))
    emit("US100 = NAS100  --  RETEST OR30/1R, 1% risk/trade compounded from $100,000, vs buy-and-hold", nas_rows)

    # ---------- S&P500 / SPX500 ----------
    spx_in = load_h1_mid(SPX_IN)
    spx_out = load_h1_mid(SPX_OUT)
    spx_rows = []
    for _, plabel, a, b in PERIODS:
        spx_rows.append((plabel, "strategy (RETEST SPX500 OR30/1R)", START_CAP, None, None,
                         "NOT runnable -- SPX500 is H1-only on disk; a 15/30-min opening range "
                         "cannot be built from hourly bars (STATE_OF_PLAY sec 10)"))
        mbh = spx_out if plabel == "2013-2017" else spx_in
        eq, p0, p1, d0, d1 = bh_from_mid(mbh, a, b)
        spx_rows.append((plabel, "buy & hold S&P 500", START_CAP, eq, None,
                         f"SPX500 H1 mid: {p0:,.1f} ({d0}) -> {p1:,.1f} ({d1})"))
    emit("S&P 500 = SPX500  --  strategy NOT runnable (no M1); buy-and-hold from H1 mid", spx_rows)

    # ---------- compact 12-row summary ----------
    print("\n  SUMMARY  (period x approach; 'strategy' = RETEST OR30/1R, 1% risk/trade compounded)\n")
    print(f"  {'instrument':<10} {'period':<20} {'approach':<12} {'starting':>10} {'ending':>13} {'return %':>10} {'trades':>7}")
    print("  " + "-" * 96)
    for inst, rows in [("US100", nas_rows), ("S&P500", spx_rows)]:
        for per, appr, s, e, n, note in rows:
            a = "strategy" if appr.startswith("strategy") else "buy & hold"
            pl = {"FULL": "FULL 2018-2025", "2013-2017": "OUT-REGIME 2013-2017",
                  "2018-2025": "FULL 2018-2025", "2022-2025": "RECENT 2022-2025"}.get(per, per)
            if e is None:
                print(f"  {inst:<10} {pl:<20} {a:<12} {s:>10,.0f} {'--':>13} {'--':>10} {'--':>7}")
            else:
                print(f"  {inst:<10} {pl:<20} {a:<12} {s:>10,.0f} {e:>13,.0f} {e/s-1:>+9.1%} "
                      f"{('' if n is None else str(n)):>7}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
