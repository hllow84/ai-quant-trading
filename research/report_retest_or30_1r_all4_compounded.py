#!/usr/bin/env python3
"""
RETEST OR30 / target 1R -- 1% risk/trade compounded from $100,000, ALL FOUR
instruments (XAUUSD, NAS100, US30, SPX500), uniform 3-period layout, each next
to buy-and-hold over the identical range.

  FULL           2018-01-01 .. 2025-12-31
  OUT-OF-REGIME  2017-01-01 .. 2017-12-31  -- ONE bull year, not a real regime
                 test (flagged explicitly; see the note printed with every
                 OUT-OF-REGIME row). It is what the archive supports: XAUUSD
                 and SPX500 M1 both start 2017-01, so this is the deepest
                 out-of-regime window available for a 4-instrument uniform
                 comparison. NAS100/US30 could go back to 2013 (M1RTH files
                 on disk) but are sliced to 2017-only here so all four rows
                 use the SAME window -- a longer NAS100/US30-only window is
                 already reported in STATE_OF_PLAY sec 10.5 / research_log.
  RECENT         2022-01-01 .. 2025-12-31

NEW BACKTESTS in this run (not a re-report -- adds to the project trial count,
STATE_OF_PLAY sec 1 table, N=1030 -> 1033):
  1. SPX500 RETEST OR30/1R, FULL/2018-2025 window        -- SPX500 had NO M1 on
     disk before this session (H1-only); the sec 10.5 batch could not run it.
  2. SPX500 RETEST OR30/1R, OUT-OF-REGIME/2017 window    -- same reason.
  3. XAUUSD RETEST OR30/1R, OUT-OF-REGIME/2017 window    -- XAUUSD had NO
     pre-2018 M1 on disk before this session; sec 10.5 explicitly stated "no
     pre-2018 out-of-regime window exists for XAUUSD."
Each of these three is ONE fully-specified cell (instrument x window x OR30 x
target=1R x variant=RETEST) -- fresh backtests, not the same trade log re-run.
Gross/net PF, Sharpe and a look-ahead guard are computed for each so the new
cells carry the same honesty gates as every other cell in this project; they
are NOT run through the full DSR structural pool (that would need re-running
the section-10.5-scale grid on SPX500, which is out of scope for this task).

NOT new (reslice of an existing cell's trade log by exit date; no re-backtest,
no new trial):
  - XAUUSD / NAS100 / US30 FULL and RECENT (subsets of the existing 2018-2025
    "in" window trade log, reproduction-checked against
    results/orb_entry_filters_scored.csv).
  - NAS100 / US30 OUT-OF-REGIME/2017 (a 2017-only slice of the existing
    2013-2017 "out" window trade log, itself reproduction-checked against the
    scored CSV).
  - SPX500 RECENT (a slice of the new SPX500 FULL-window trade log above).

Compounding = equity *= (1 + 0.01 * net_R) per trade, chronological (exit-
time) order, 1% fixed-fractional risk (research/ftmo_engine.RISK_PER_TRADE).
Costs already in net_R: XAUUSD legacy $/oz model; NAS100/US30/SPX500 real
per-bar spread + 0.35 bps commission + ET-anchored 1.00/0.15 bps slippage
(run_orb.COST_BPS / run_orb.slip_bps -- SPX500 is a Dukascopy index CFD like
NAS100/US30, so it gets the identical cost model, not a new one).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

import run_orb as ro
from research.gold_data import load_m1_spot, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.ftmo_engine import (
    simulate_trades, de_overlap, RISK_PER_TRADE,
    build_daily_returns, equity_from_returns, build_position_series,
)
from strategies.orb import orb, ET

D = _ROOT / "data"
SCORED = _ROOT / "results" / "orb_entry_filters_scored.csv"
START_CAP = 100_000.0
BARS_PER_YEAR = 252

ET_SESSION = dict(session_tz=ET, open_min=9 * 60 + 30, close_min=16 * 60, min_sess_bars=300)
PARAMS = dict(or_minutes=30, target="1R", stop_mode="or_range")

PERIODS = [
    ("FULL",          "2018-01-01", "2025-12-31"),
    ("OUT-OF-REGIME",  "2017-01-01", "2017-12-31"),
    ("RECENT",        "2022-01-01", "2025-12-31"),
]

FILES = {
    "XAUUSD": dict(cost_bps=None, slip_fn=None,
                   in_=D / "XAUUSD_M1_2018_2025_spot_dukascopy.csv",
                   out=D / "XAUUSD_M1_2017_spot_dukascopy.csv"),
    "NAS100": dict(cost_bps=ro.COST_BPS, slip_fn=ro.slip_bps,
                   in_=D / "NAS100_M1_2018_2025_cfd_dukascopy.csv",
                   out=D / "NAS100_M1RTH_2013_2017_cfd_dukascopy.csv"),
    "US30":   dict(cost_bps=ro.COST_BPS, slip_fn=ro.slip_bps,
                   in_=D / "US30_M1_2018_2025_cfd_dukascopy.csv",
                   out=D / "US30_M1RTH_2013_2017_cfd_dukascopy.csv"),
    "SPX500": dict(cost_bps=ro.COST_BPS, slip_fn=ro.slip_bps,
                   in_=D / "SPX500_M1_2017_2025_cfd_dukascopy.csv",
                   out=None),   # single continuous file, sliced below
}


def mid_frame(path: Path) -> pd.DataFrame:
    spot = load_m1_spot(path)
    m = pd.DataFrame(index=spot.index)
    for c in ("open", "high", "low", "close"):
        m[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
    m["spread"] = spot["spread"]
    m["volume"] = spot["volume"]
    return m, spot


def build_trades(m: pd.DataFrame, cost_bps, slip_fn) -> pd.DataFrame:
    cands = orb(m, PARAMS, retest=True, retest_tol_frac=0.10, **ET_SESSION)
    tr = de_overlap(simulate_trades(m, cands, strictly_after=False,
                                    cost_bps=cost_bps, slip_bps_fn=slip_fn))
    tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True)
    tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True)
    return tr.sort_values("exit_time").reset_index(drop=True)


def reproduction_check(tr: pd.DataFrame, instrument: str, window: str) -> bool:
    row = pd.read_csv(SCORED).query(
        f"instrument=='{instrument}' and or_minutes==30 and target=='1R' "
        f"and variant=='RETEST' and window=='{window}'"
    )
    if row.empty:
        return False
    row = row.iloc[0]
    assert len(tr) == int(row["n_trades"]), (instrument, window, len(tr), row["n_trades"])
    assert abs(tr["net_R"].sum() - row["net_R_total"]) < 1e-6, \
        (instrument, window, tr["net_R"].sum(), row["net_R_total"])
    print(f"    repro OK vs orb_entry_filters_scored.csv: {len(tr)} trades, "
          f"net_R total {tr['net_R'].sum():.6f}")
    return True


def score_new_cell(label: str, m: pd.DataFrame, tr: pd.DataFrame, daily_index) -> None:
    """Honesty gates for a genuinely NEW cell: guard, gross/net PF, Sharpe, maxDD."""
    if tr.empty:
        print(f"    [{label}] NO TRADES")
        return
    pos = build_position_series(tr, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"
    daily_ret = build_daily_returns(tr, daily_index)
    equity = equity_from_returns(daily_ret)
    print(f"    [NEW BACKTEST] {label}: n={len(tr)} guard={guard} "
          f"grossPF={profit_factor(tr['gross_R']):.3f} netPF={profit_factor(tr['net_R']):.3f} "
          f"SR={sharpe(daily_ret, BARS_PER_YEAR):+.2f} maxDD={max_drawdown(equity)*100:.1f}% "
          f"cost_R={tr['cost_R'].mean()*100:.1f}%")


def compound(net_R: pd.Series) -> float:
    eq = START_CAP
    for r in net_R.to_numpy():
        eq *= (1.0 + RISK_PER_TRADE * r)
    return eq


def bh(m: pd.DataFrame, a: str, b: str):
    seg = m.loc[(m.index >= pd.Timestamp(a, tz="UTC")) & (m.index <= pd.Timestamp(b, tz="UTC") + pd.Timedelta(days=1))]
    if seg.empty:
        return None
    p0, p1 = float(seg["mid_close"].iloc[0]), float(seg["mid_close"].iloc[-1])
    return START_CAP * p1 / p0, p0, p1, seg.index[0].date(), seg.index[-1].date()


def period_trades(tr: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    lo = pd.Timestamp(a, tz=ET)
    hi = pd.Timestamp(b, tz=ET) + pd.Timedelta(days=1)
    tdate = tr["entry_time"].dt.tz_convert(ET)
    return tr[(tdate >= lo) & (tdate < hi)]


def emit(title: str, rows: list) -> None:
    W = 122
    print("\n" + "=" * W)
    print(f"  {title}")
    print("=" * W)
    print(f"  {'period':<26} {'approach':<32} {'starting':>10} {'ending':>14} {'return %':>10} {'trades':>7}")
    print("  " + "-" * (W - 4))
    for per, appr, s, e, n, note in rows:
        if e is None:
            print(f"  {per:<26} {appr:<32} {s:>10,.0f} {'--':>14} {'--':>10} {'--':>7}")
        else:
            print(f"  {per:<26} {appr:<32} {s:>10,.0f} {e:>14,.0f} {e/s-1:>+9.1%} "
                  f"{('' if n is None else str(n)):>7}")
        print(f"  {'':<26} -> {note}")
    print("=" * W)


def main():
    all_rows = {}
    for inst, cfg in FILES.items():
        print(f"\n### {inst} ###")
        rows = []

        if inst == "SPX500":
            m, spot = mid_frame(cfg["in_"])
            daily_index = aggregate_daily(spot).index
            print(f"  loaded {cfg['in_'].name}: {len(m):,} M1 bars {m.index[0].date()} -> {m.index[-1].date()}")
            tr = build_trades(m, cfg["cost_bps"], cfg["slip_fn"])
            print(f"  built {len(tr)} RETEST OR30/1R trades over the full pull, net_R total {tr['net_R'].sum():.6f}")
            for plabel, a, b in PERIODS:
                seg = period_trades(tr, a, b)
                if plabel != "RECENT":  # RECENT is a subset of FULL, not a fresh cell
                    score_new_cell(f"SPX500 {plabel} {a}..{b}", m, seg, daily_index)
                end_eq = compound(seg["net_R"])
                span = f"{seg['entry_time'].dt.date.min()}..{seg['entry_time'].dt.date.max()}" if len(seg) else "no trades"
                note = f"trades {span}"
                if plabel == "OUT-OF-REGIME":
                    note += "  [ONE bull year -- not a real regime test, see header note]"
                rows.append((f"{plabel} {a}..{b}", "strategy (RETEST SPX500 OR30/1R)", START_CAP, end_eq, len(seg), note))
                eqv = bh(m, a, b)
                eq, p0, p1, d0, d1 = eqv
                rows.append((f"{plabel} {a}..{b}", "buy & hold SPX500 (M1 mid)", START_CAP, eq, None,
                             f"${p0:,.1f} ({d0}) -> ${p1:,.1f} ({d1})"))
            emit("SPX500  --  RETEST OR30/1R, 1% risk/trade compounded from $100,000, vs buy-and-hold "
                 "[NEW instrument -- SPX500 had no M1 on disk before this session]", rows)
            all_rows[inst] = rows
            continue

        m_in, spot_in = mid_frame(cfg["in_"])
        di_in = aggregate_daily(spot_in).index
        print(f"  loaded {cfg['in_'].name}: {len(m_in):,} M1 bars {m_in.index[0].date()} -> {m_in.index[-1].date()}")
        tr_in = build_trades(m_in, cfg["cost_bps"], cfg["slip_fn"])
        is_new_in = not reproduction_check(tr_in, inst, "in")
        if is_new_in:
            score_new_cell(f"{inst} FULL (in window)", m_in, tr_in, di_in)

        m_out, spot_out = mid_frame(cfg["out"])
        di_out = aggregate_daily(spot_out).index
        print(f"  loaded {cfg['out'].name}: {len(m_out):,} M1 bars {m_out.index[0].date()} -> {m_out.index[-1].date()}")
        tr_out = build_trades(m_out, cfg["cost_bps"], cfg["slip_fn"])
        is_new_out = not reproduction_check(tr_out, inst, "out")
        if is_new_out:
            score_new_cell(f"{inst} OUT-OF-REGIME (out window)", m_out, tr_out, di_out)

        for plabel, a, b in PERIODS:
            if plabel == "OUT-OF-REGIME":
                seg, mbh = period_trades(tr_out, a, b), m_out
            else:
                seg, mbh = period_trades(tr_in, a, b), m_in
            end_eq = compound(seg["net_R"])
            span = f"{seg['entry_time'].dt.date.min()}..{seg['entry_time'].dt.date.max()}" if len(seg) else "no trades"
            note = f"trades {span}"
            if plabel == "OUT-OF-REGIME":
                note += "  [ONE bull year -- not a real regime test, see header note]"
            rows.append((f"{plabel} {a}..{b}", f"strategy (RETEST {inst} OR30/1R)", START_CAP, end_eq, len(seg), note))
            eq, p0, p1, d0, d1 = bh(mbh, a, b)
            rows.append((f"{plabel} {a}..{b}", f"buy & hold {inst} (M1 mid)", START_CAP, eq, None,
                         f"${p0:,.1f} ({d0}) -> ${p1:,.1f} ({d1})"))
        tag = " [NEW: out-of-regime/2017 cell]" if is_new_out else ""
        emit(f"{inst}  --  RETEST OR30/1R, 1% risk/trade compounded from $100,000, vs buy-and-hold{tag}", rows)
        all_rows[inst] = rows

    # ---------- consolidated summary ----------
    print("\n\n" + "#" * 122)
    print("  SUMMARY -- RETEST OR30/1R, 1% risk/trade compounded from $100,000, ALL 4 INSTRUMENTS x 3 PERIODS x 2 APPROACHES")
    print("#" * 122)
    print(f"  {'instrument':<8} {'period':<26} {'approach':<12} {'starting':>10} {'ending':>13} {'return %':>10} {'trades':>7}")
    print("  " + "-" * 96)
    for inst, rows in all_rows.items():
        for per, appr, s, e, n, note in rows:
            a = "strategy" if appr.startswith("strategy") else "buy & hold"
            if e is None:
                print(f"  {inst:<8} {per:<26} {a:<12} {s:>10,.0f} {'--':>13} {'--':>10} {'--':>7}")
            else:
                print(f"  {inst:<8} {per:<26} {a:<12} {s:>10,.0f} {e:>13,.0f} {e/s-1:>+9.1%} "
                      f"{('' if n is None else str(n)):>7}")
    print("\n  NEW BACKTESTS this run (add to project trial count): SPX500 FULL(2018-2025), "
          "SPX500 OUT-OF-REGIME(2017), XAUUSD OUT-OF-REGIME(2017) -- 3 cells. All other rows are")
    print("  reslices (by exit/entry date) of an already-scored cell's trade log -- no new trial.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
