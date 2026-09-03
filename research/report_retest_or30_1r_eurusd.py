#!/usr/bin/env python3
"""
RETEST OR30 / target 1R -- EURUSD, the first forex pair this strategy has ever
been tested on in this project (prior coverage: XAUUSD, NAS100, US30, SPX500 --
STATE_OF_PLAY sec 10.5/10.6). Entry logic, risk management and reporting format
are UNCHANGED from those sections; only the instrument and its cost model are
new. STATE_OF_PLAY trial count: 1041 -> 1043 (2 new cells: EURUSD in + out).

STRATEGY (byte-identical to every other RETEST OR30/1R cell in this project):
  strategies.orb.orb(m1_mid, dict(or_minutes=30, target="1R", stop_mode=
  "or_range"), retest=True, retest_tol_frac=0.10, **ET_SESSION) -> candidates,
  resolved by research.ftmo_engine.simulate_trades + de_overlap. 1% fixed-
  fractional risk per trade (RISK_PER_TRADE), one position per day, no
  pyramiding (de_overlap enforces this).

SESSION ANCHOR -- kept at 09:30 America/New_York, NOT changed for EURUSD.
  EURUSD's own conventional session opens are London (08:00 GMT) or Tokyo
  (00:00 GMT/09:00 JST), not the US cash equity open -- so 09:30 ET is not
  EURUSD's "natural" anchor. It is kept anyway, deliberately: this task tests
  whether RETEST OR30/1R GENERALIZES to a new instrument with the SAME rule
  set, not whether a EURUSD-tuned session anchor can be found. Changing the
  anchor would confound two different questions (does this exact strategy
  generalize? vs. does a different, EURUSD-specific breakout window work?) and
  the second one is a new, untested hypothesis with its own trial cost, out of
  scope here. If a future study wants a London/Tokyo-anchored EURUSD ORB, that
  is a DIFFERENT strategy and must be logged as such.

DATA -- pulled fresh this session via Dukascopy (scripts/download_eurusd_
  backfill.sh -> scripts/merge_eurusd_backfill.py, bid+ask separately, real
  spread column), covering the SAME two windows every other ORB instrument in
  this project uses: 2013-2017 (out-of-regime) and 2018-2025 (in-regime).
  EURUSD is Dukascopy's flagship pair with continuous history well before
  2013 -- unlike XAUUSD/SPX500 (STATE_OF_PLAY sec 10.6), there was no
  earliest-availability question to probe; 2013-01-01 was chosen to match the
  window already used for NAS100/US30 (sec 10.5), not because the archive
  requires it. This gives EURUSD a full 5-year out-of-regime window, deeper
  than the single 2017 year available for XAUUSD/SPX500.

COSTS -- real spread from the data (median/mean measured and printed below,
  not assumed) + a stated commission grounded in FTMO's own published EURUSD
  conditions (fetched live, sec 10.7-style fact-check): FTMO charges $3 per
  round lot (100,000 units) commission on forex, which at EURUSD's ~1.05-1.10
  price level over this test's span is ~0.27-0.29 bps of notional -- used here
  as EURUSD_COST_BPS.commission = 0.3 bps, i.e. NOT rounded down, a slightly
  conservative (harsher) reading of FTMO's own number. Slippage keeps the
  project's existing ET-anchored convention (run_orb.slip_bps: 1.00 bps/side
  09:30-10:30 ET, 0.15 bps/side after) UNCHANGED from the index cells --
  deliberately not tightened for EURUSD's deeper liquidity, so the comparison
  is not flattered by an instrument-specific slippage assumption.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

import run_orb as ro
from research.gold_data import aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe
from research.ftmo_engine import (
    simulate_trades, de_overlap, RISK_PER_TRADE,
    build_daily_returns, equity_from_returns, build_position_series,
)
from strategies.orb import orb, ET
from research.report_retest_or30_1r_all4_compounded import (
    mid_frame, compound, bh, period_trades, START_CAP, BARS_PER_YEAR,
)

D = _ROOT / "data"
PRIOR_TRIALS = 1041   # STATE_OF_PLAY sec 1, after sec 10.7

IN_FILE = D / "EURUSD_M1_2018_2025_spot_dukascopy.csv"
OUT_FILE = D / "EURUSD_M1_2013_2017_spot_dukascopy.csv"

ET_SESSION = dict(session_tz=ET, open_min=9 * 60 + 30, close_min=16 * 60, min_sess_bars=300)
PARAMS = dict(or_minutes=30, target="1R", stop_mode="or_range")

# FTMO's published forex commission ($3/100k-unit round lot) converted to bps
# at EURUSD's typical 1.05-1.10 level over this test's span -- see module
# docstring. Slippage: UNCHANGED from the index convention (run_orb), not
# tightened for EURUSD.
EURUSD_COMMISSION_BPS = 0.30
EURUSD_COST_BPS = dict(commission=EURUSD_COMMISSION_BPS,
                        slip_normal=ro.SLIP_NORMAL_BPS, slip_news=ro.SLIP_OPEN_BPS)

PERIODS = [
    ("FULL",          "2018-01-01", "2025-12-31"),
    ("OUT-OF-REGIME", "2013-01-01", "2017-12-31"),
    ("RECENT",        "2022-01-01", "2025-12-31"),
]


def build_trades(m: pd.DataFrame) -> pd.DataFrame:
    cands = orb(m, PARAMS, retest=True, retest_tol_frac=0.10, **ET_SESSION)
    tr = de_overlap(simulate_trades(m, cands, strictly_after=False,
                                    cost_bps=EURUSD_COST_BPS, slip_bps_fn=ro.slip_bps))
    tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True)
    tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True)
    return tr.sort_values("exit_time").reset_index(drop=True)


def gate_stats(m: pd.DataFrame, tr: pd.DataFrame, daily_index) -> dict:
    if tr.empty:
        return dict(guard="N/A", gross_pf=np.nan, net_pf=np.nan, sharpe=np.nan, max_dd=np.nan,
                    top_year_share=np.nan, n_obs=0, skew=0.0, ekurt=0.0)
    pos = build_position_series(tr, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"
    daily_ret = build_daily_returns(tr, daily_index)
    equity = equity_from_returns(daily_ret)
    yr = tr["exit_time"].dt.year
    agg = tr.groupby(yr)["net_R"].sum()
    tot = float(agg.sum())
    top_share = (float(agg.max()) / tot) if tot > 0 else float("nan")
    return dict(
        guard=guard, gross_pf=profit_factor(tr["gross_R"]), net_pf=profit_factor(tr["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR), max_dd=max_drawdown(equity),
        top_year_share=top_share, n_years=int(len(agg)), n_pos_years=int((agg > 0).sum()),
        n_obs=int(len(daily_ret)),
        skew=float(daily_ret.skew()) if len(daily_ret) > 2 else 0.0,
        ekurt=float(daily_ret.kurtosis()) if len(daily_ret) > 3 else 0.0,
    )


def three_bucket_breakdown(tr: pd.DataFrame) -> str:
    """Same target/stop/time breakdown reported for XAUUSD (sec 10.6/10.7)."""
    if tr.empty:
        return "no trades"
    n = len(tr)
    parts = []
    for reason in ["target", "stop", "time"]:
        sub = tr[tr["reason"] == reason]
        if len(sub):
            parts.append(f"{reason}={len(sub)} ({100*len(sub)/n:.0f}%, avg net R={sub['net_R'].mean():+.3f})")
        else:
            parts.append(f"{reason}=0")
    return " | ".join(parts)


def main():
    print("=" * 130)
    print("  RETEST OR30/1R -- EURUSD (first forex pair tested with this strategy)")
    print("=" * 130)

    m_in, spot_in = mid_frame(IN_FILE)
    di_in = aggregate_daily(spot_in).index
    m_out, spot_out = mid_frame(OUT_FILE)
    di_out = aggregate_daily(spot_out).index
    print(f"  IN  window: {IN_FILE.name}  {m_in.index[0].date()} -> {m_in.index[-1].date()}  ({len(m_in):,} bars)")
    print(f"  OUT window: {OUT_FILE.name}  {m_out.index[0].date()} -> {m_out.index[-1].date()}  ({len(m_out):,} bars)")

    # measured cost stats, not assumed
    for label, m in [("IN", m_in), ("OUT", m_out)]:
        med_px = m["mid_close"].median()
        med_sp = m["spread"].median()
        print(f"  [{label}] measured spread: median {med_sp:.5f} ({1e4*med_sp:.2f} pips, "
              f"{1e4*med_sp/med_px:.3f} bps) | commission {EURUSD_COMMISSION_BPS} bps | "
              f"slippage {ro.SLIP_NORMAL_BPS}/{ro.SLIP_OPEN_BPS} bps normal/opening-hour (unchanged index convention)")

    tr_in = build_trades(m_in)
    tr_out = build_trades(m_out)
    g_in = gate_stats(m_in, tr_in, di_in)
    g_out = gate_stats(m_out, tr_out, di_out)

    print(f"\n  [IN  2018-2025] n={len(tr_in)} guard={g_in['guard']} grossPF={g_in['gross_pf']:.3f} "
          f"netPF={g_in['net_pf']:.3f} SR={g_in['sharpe']:+.2f} maxDD={g_in['max_dd']*100:.1f}% "
          f"topYr={g_in['top_year_share']*100:.0f}% posYrs={g_in['n_pos_years']}/{g_in['n_years']}")
    print(f"      exits: {three_bucket_breakdown(tr_in)}")
    print(f"  [OUT 2013-2017] n={len(tr_out)} guard={g_out['guard']} grossPF={g_out['gross_pf']:.3f} "
          f"netPF={g_out['net_pf']:.3f} SR={g_out['sharpe']:+.2f} maxDD={g_out['max_dd']*100:.1f}% "
          f"topYr={g_out['top_year_share']*100:.0f}% posYrs={g_out['n_pos_years']}/{g_out['n_years']}")
    print(f"      exits: {three_bucket_breakdown(tr_out)}")

    print(f"\n  NEW BACKTESTS this run: 2 (EURUSD in-regime, EURUSD out-of-regime 2013-2017)")
    print(f"  CUMULATIVE PROJECT TRIALS: {PRIOR_TRIALS} + 2 = {PRIOR_TRIALS + 2}")

    # DSR, reference only (per standing instruction) -- 2-cell pool is too
    # small to mean much; printed anyway for the record, explicitly flagged.
    pool = np.array([g_in["sharpe"]])
    if np.isfinite(g_in["sharpe"]) and g_in["n_obs"] >= 4:
        e = expected_max_sharpe(pool)
        d = deflated_sharpe(sr_best=float(g_in["sharpe"]), sr_trials=pool, n_obs=int(g_in["n_obs"]),
                            skewness=g_in["skew"], excess_kurtosis=g_in["ekurt"])["dsr"]
        print(f"\n  DSR REFERENCE ONLY (not a gate; single-cell pool, uninformative by construction, "
              f"printed for completeness): E[max SR] {e[0]:+.3f}, EURUSD-in DSR {d:.3f}")

    # ---- compounding table, same 3-period layout / format as sec 10.6 ----
    W = 122
    rows = []
    print("\n" + "=" * W)
    print("  RETEST OR30/1R, EURUSD -- 1% risk/trade compounded from $100,000, vs buy-and-hold")
    print("=" * W)
    print(f"  {'period':<26} {'approach':<32} {'starting':>10} {'ending':>14} {'return %':>10} {'trades':>7}")
    print("  " + "-" * (W - 4))
    for plabel, a, b in PERIODS:
        if plabel == "OUT-OF-REGIME":
            seg, mbh = period_trades(tr_out, a, b), m_out
        else:
            seg, mbh = period_trades(tr_in, a, b), m_in
        end_eq = compound(seg["net_R"])
        span = f"{seg['entry_time'].dt.date.min()}..{seg['entry_time'].dt.date.max()}" if len(seg) else "no trades"
        note = f"trades {span}"
        rows.append((f"{plabel} {a}..{b}", "strategy (RETEST EURUSD OR30/1R)", START_CAP, end_eq, len(seg), note))
        print(f"  {rows[-1][0]:<26} {rows[-1][1]:<32} {START_CAP:>10,.0f} {end_eq:>14,.0f} "
              f"{end_eq/START_CAP-1:>+9.1%} {len(seg):>7}")
        print(f"  {'':<26} -> {note}")
        eq, p0, p1, d0, d1 = bh(mbh, a, b)
        rows.append((f"{plabel} {a}..{b}", "buy & hold EURUSD (M1 mid)", START_CAP, eq, None,
                     f"{p0:.5f} ({d0}) -> {p1:.5f} ({d1})"))
        print(f"  {rows[-1][0]:<26} {rows[-1][1]:<32} {START_CAP:>10,.0f} {eq:>14,.0f} "
              f"{eq/START_CAP-1:>+9.1%} {'':>7}")
        print(f"  {'':<26} -> {rows[-1][5]}")
    print("=" * W)

    out_csv = _ROOT / "results" / "retest_or30_1r_eurusd_summary.csv"
    df = pd.DataFrame([dict(period=r[0], approach=r[1], start=r[2], end=r[3], trades=r[4], note=r[5]) for r in rows])
    df.to_csv(out_csv, index=False)
    print(f"\n  results -> {out_csv}")

    # ---- consolidated table matching the all-4-instrument format (sec 10.6) ----
    print("\n\n" + "#" * 122)
    print("  EURUSD in the SAME table format as sec 10.6 (XAUUSD/NAS100/US30/SPX500), for direct comparison")
    print("#" * 122)
    print(f"  {'instrument':<8} {'period':<26} {'approach':<12} {'starting':>10} {'ending':>13} {'return %':>10} {'trades':>7}")
    print("  " + "-" * 96)
    for per, appr, s, e, n, note in rows:
        a = "strategy" if appr.startswith("strategy") else "buy & hold"
        print(f"  {'EURUSD':<8} {per:<26} {a:<12} {s:>10,.0f} {e:>13,.0f} {e/s-1:>+9.1%} "
              f"{('' if n is None else str(n)):>7}")

    # ---- verdict ----
    full_strat = next(r for r in rows if r[0].startswith("FULL") and r[1].startswith("strategy"))
    full_bh = next(r for r in rows if r[0].startswith("FULL") and r[1].startswith("buy"))
    out_strat = next(r for r in rows if r[0].startswith("OUT") and r[1].startswith("strategy"))
    out_bh = next(r for r in rows if r[0].startswith("OUT") and r[1].startswith("buy"))
    print("\n  VERDICT:")
    print(f"  FULL 2018-2025:  strategy ${full_strat[3]:,.0f} ({full_strat[3]/START_CAP-1:+.1%}) vs "
          f"buy-and-hold ${full_bh[3]:,.0f} ({full_bh[3]/START_CAP-1:+.1%})  -> "
          f"{'BEATS' if full_strat[3] > full_bh[3] else 'LOSES TO'} buy-and-hold")
    print(f"  OUT-OF-REGIME 2013-2017:  strategy ${out_strat[3]:,.0f} ({out_strat[3]/START_CAP-1:+.1%}) vs "
          f"buy-and-hold ${out_bh[3]:,.0f} ({out_bh[3]/START_CAP-1:+.1%})  -> "
          f"{'BEATS' if out_strat[3] > out_bh[3] else 'LOSES TO'} buy-and-hold")
    print(f"  Net PF in/out: {g_in['net_pf']:.3f} / {g_out['net_pf']:.3f}   "
          f"Net Sharpe in/out: {g_in['sharpe']:+.2f} / {g_out['sharpe']:+.2f}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
