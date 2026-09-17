"""
ftmo_check_us30_macross_breakout.py -- SS65: runs the FTMO ruleset check
(same corrected method as Sec58/Sec62 -- no fabricated Best Day/consistency
rule, verified against ftmo.com 2026-09-16) on a SECOND combined-book
candidate, to see whether a different pairing funds better than Sec52's
ORB gold + US30 breakout book (the only one checked so far).

CANDIDATE: US30 macross (Sec43, Sharpe +0.999 standalone) + US30 breakout
(Sec45, Sharpe +1.684 standalone), Sec48's SAME-INSTRUMENT/DIFFERENT-FAMILY
pairing -- picked over the other 8 untested pairings because it is the
STRONGEST of the remaining pairings by standalone-leg quality (both legs
individually beat US30 B&H, Sharpe +0.547) and, being single-instrument,
has no cross-instrument correlation assumption to re-litigate. Sec48 found
its plain 50/50 combined Sharpe was +1.146 (vs ORB gold+US30 breakout's
50/50 Sharpe of ~+1.68, Sec49) -- weaker on Sharpe alone, so the question
here is specifically whether it funds differently despite that gap, since
FTMO's Challenge pass rate depends on path/drawdown shape, not Sharpe
directly.

METHOD: identical machinery to Sec58 (research/ftmo_check_best_candidate.py)
and Sec59 (research/ftmo_check_6x_reference.py) -- reuses
research/combined_book_risk_parity_rolling.rolling_weight_series for the
SAME causal monthly-rebalanced inverse-vol weighting scheme (never
previously applied to this pairing; Sec48 only tested fixed 50/50), then
research/ftmo_challenge_daily.rolling_pass_rate_daily / two_phase_chain
for the Challenge simulation, best_day_cap=None (Sec62's correction).
Reports standalone/fixed/rolling-RP Sharpe for context, then the chained
two-phase funded probability at 1x (project-standard sizing) and at both
of Sec62's reference multipliers (6x, 14x) for direct comparison against
the ORB gold+US30 breakout numbers already on record.

Zero new trials on the underlying legs (both re-run unchanged) -- this is
a portfolio-construction + ruleset check, not a parameter search. 0 new
backtest trials. (The momentum family work earlier this session, Sec64,
already moved cumulative N to 1645; this section adds 0 more.)
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, load_m1_mid, resample_mid, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.ftmo_engine import simulate_trades, de_overlap, build_daily_returns, equity_from_returns, build_position_series
from research.combined_book_risk_parity_rolling import rolling_weight_series
from research.ftmo_challenge_daily import rolling_pass_rate_daily
from research.ftmo_check_6x_reference import two_phase_chain
from research.ftmo_check_best_candidate import us30_breakout_leg_daily_returns
from strategies.sweep_families import ma_cross, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
DATA = _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv"
MAX_DAYS = 60
BEST_DAY_CAP = None
MULTIPLIERS = (1.0, 6.0, 14.0)


def us30_macross_leg_daily_returns():
    m1 = load_m1_mid(DATA)
    daily_index = aggregate_daily(load_m1_spot(DATA)).index
    m = resample_mid(m1, "4h")
    params = dict(fast=10, slow=30, ema_trend=100, k_atr=2.5, R=1.0, H=72)
    cands = ma_cross(m, params, TF_DELTA["H4"])
    for t in cands:
        t["session_end"] = pd.Timestamp(t["session_end"]).tz_convert("UTC") if pd.Timestamp(t["session_end"]).tz else pd.Timestamp(t["session_end"]).tz_localize("UTC")
        t["entry_time"] = pd.Timestamp(t["entry_time"]).tz_convert("UTC") if pd.Timestamp(t["entry_time"]).tz else pd.Timestamp(t["entry_time"]).tz_localize("UTC")
    trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=COST_BPS))
    return build_daily_returns(trades, daily_index)


def report_phase(label, daily_ret, data_start, data_end, phase):
    r = rolling_pass_rate_daily(daily_ret, data_start, data_end, phase=phase, max_days=MAX_DAYS,
                                 best_day_cap=BEST_DAY_CAP)
    print(f"  {label} -- Phase {phase} (target {'10%' if phase==1 else '5%'}):")
    print(f"    n_challenges={r['n_challenges']}  RAW pass rate={r['pass_rate_raw']*100:.1f}%  "
          f"reasons={r['reasons']}")
    return r


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    macross = us30_macross_leg_daily_returns()
    breakout = us30_breakout_leg_daily_returns()
    idx = macross.index.union(breakout.index)
    macross_a = macross.reindex(idx, fill_value=0.0)
    breakout_a = breakout.reindex(idx, fill_value=0.0)

    fixed = 0.5 * macross_a + 0.5 * breakout_a
    w_roll = rolling_weight_series(macross_a, breakout_a)
    rolling_rp = w_roll * macross_a + (1.0 - w_roll) * breakout_a

    data_start, data_end = idx.min(), idx.max()
    print(f"US30 macross + US30 breakout combined data span: {data_start.date()} -> {data_end.date()} "
          f"({len(idx)} days)\n")

    for label, series in [("Fixed 50/50", fixed), ("Rolling risk-parity", rolling_rp)]:
        eq = equity_from_returns(series)
        sh = sharpe(series, BARS_PER_YEAR)
        dd = max_drawdown(eq)
        print(f"{label}: Sharpe={sh:+.3f}  maxDD={dd*100:.1f}%")
    print()

    rows = []
    for m_mult in MULTIPLIERS:
        scaled = m_mult * rolling_rp
        eq = equity_from_returns(scaled)
        sh = sharpe(scaled, BARS_PER_YEAR)
        dd = max_drawdown(eq)
        print(f"=== {m_mult:.0f}x standard risk (rolling risk-parity) ===")
        print(f"  Sharpe: {sh:+.3f} (unchanged from 1x)  maxDD: {dd*100:.1f}%")

        r1 = report_phase("Phase 1", scaled, data_start, data_end, 1)
        r2 = report_phase("Phase 2", scaled, data_start, data_end, 2)

        chain = two_phase_chain(scaled, data_start, data_end)
        n_total = len(chain)
        n_p1 = int(chain["phase1_pass"].sum())
        n_funded = int((chain["funded"] == True).sum())
        print(f"  CHAINED (funded): {n_funded}/{n_total} = {n_funded/n_total*100:.1f}%\n")

        rows.append(dict(multiplier=m_mult, sharpe=sh, max_dd=dd,
                          phase1_indep=r1["pass_rate_raw"], phase2_indep=r2["pass_rate_raw"],
                          n_challenges=n_total, phase1_chain=n_p1 / n_total, funded_chain=n_funded / n_total))

    out = RESULTS / "ftmo_check_us30_macross_breakout.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Saved {out}")
    print("Trial count: 0 new (FTMO-ruleset check on already-scored legs, "
          "not a parameter search). Cumulative trials unchanged by this section.")


if __name__ == "__main__":
    main()
