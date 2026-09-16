"""
ftmo_check_best_candidate.py — §58: FTMO Challenge ruleset check on this
project's honest, deployable best result: ORB gold RETEST + US30 breakout
under ROLLING (causal, walk-forward, no-look-ahead) risk-parity weighting
(§52, Sharpe +1.793, maxDD 3.1%, 9/9 years net-positive on the standalone
metric).

WHY THIS CANDIDATE, NOT credit-spread SPY (§41's raw-Sharpe project-best):
credit-spread SPY is an OPTIONS strategy. FTMO-style prop-trading accounts
are forex/CFD/futures accounts; they do not offer a retail options
overlay in the form this project's credit-spread backtest assumes (short
verticals with real bid/ask option pricing) — running an options income
strategy through an FTMO challenge is not a like-for-like proposition the
way a spot/CFD strategy is. The FOUR B&H-beating candidates that ARE
CFD-tradeable are ORB gold, NAS100 macross, US30 macross, and US30
breakout; among their combined books, §52's ORB gold + US30 breakout
rolling-risk-parity book is the strongest AND most robust (9/9 years
positive on its own daily-return metric) — the natural pick for "the best
FTMO-eligible candidate."

METHOD: reconstructs both legs' own trade-level engines UNCHANGED (ORB
gold via research/orb_retest_entry_stop_grid.build_trades, tol_frac=0.20/
stop_mode='moderate'; US30 breakout via strategies/sweep_families.
breakout_retest, N=20/k_atr=4.0/R=0.25/H=20 — same params as §45/§49/§52),
builds each leg's own daily RET_FRAC series (RISK_PER_TRADE=0.01 fixed-
fractional convention, research/ftmo_engine.py's project-standard, ALREADY
the basis for every Sharpe/maxDD number reported for these two legs
throughout §39-§57), applies the SAME causal monthly-rebalanced inverse-
vol weight from §52 (research/combined_book_risk_parity_rolling.py's
rolling_weight_series, reused unchanged) to produce ONE portfolio-level
daily return series, then runs research/ftmo_challenge_daily.py's
rolling_pass_rate_daily (a daily-return adaptation of
research/ftmo_rules.py's per-trade Challenge simulator, extended with the
Best Day/consistency rule per CLAUDE.md's standing rule 6, which the
original per-trade engine does not implement) across every calendar-month
start date with enough runway, for BOTH Phase 1 (target +10%) and Phase 2
(target +5%).

Also reports the FIXED 50/50 and in-sample risk-parity weightings for
direct comparison against the deployable rolling scheme, since §51/§52
already established how those three compare on Sharpe/maxDD — this
section asks the FTMO-specific question of how that translates into
challenge PASS RATE, which is a different (harder, all-or-nothing, path-
dependent) test than a smooth Sharpe/maxDD summary.

Zero new backtest trials on the underlying legs (both engines reused
unchanged) — the FTMO ruleset itself is not a parameter search, so this
adds 0 to the project's cumulative trial count (N=1570 unchanged).
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
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns, build_position_series,
)
from research.orb_retest_entry_stop_grid import mid_frame, build_trades, FILE_2017, FILE_2018_2025
from research.combined_book_risk_parity_rolling import rolling_weight_series
from research.ftmo_challenge_daily import rolling_pass_rate_daily
from strategies.sweep_families import breakout_retest, TF_DELTA

RESULTS = _ROOT / "results"
US30_DATA = _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv"
MAX_DAYS = 60          # FTMO Challenge/Verification runway, days
BEST_DAY_CAP = 0.30    # assumed consistency threshold, stated in ftmo_challenge_daily.py


def gold_leg_daily_returns():
    m17, spot17 = mid_frame(FILE_2017)
    m18, spot18 = mid_frame(FILE_2018_2025)
    m = pd.concat([m17, m18]).sort_index()
    spot = pd.concat([spot17, spot18]).sort_index()
    daily_index = aggregate_daily(spot).index
    tr = build_trades(m, tol_frac=0.20, stop_mode="moderate")
    return build_daily_returns(tr, daily_index)


def us30_breakout_leg_daily_returns():
    m1 = load_m1_mid(US30_DATA)
    daily_index = aggregate_daily(load_m1_spot(US30_DATA)).index
    m = resample_mid(m1, "4h")
    params = dict(N=20, k_atr=4.0, R=0.25, H=20)
    cands = breakout_retest(m, params, TF_DELTA["H4"])
    for t in cands:
        t["session_end"] = pd.Timestamp(t["session_end"]).tz_convert("UTC") if pd.Timestamp(t["session_end"]).tz else pd.Timestamp(t["session_end"]).tz_localize("UTC")
        t["entry_time"] = pd.Timestamp(t["entry_time"]).tz_convert("UTC") if pd.Timestamp(t["entry_time"]).tz else pd.Timestamp(t["entry_time"]).tz_localize("UTC")
    trades = de_overlap(simulate_trades(m, cands, strictly_after=True,
                                         cost_bps=dict(commission=0.35, slip_normal=0.15, slip_news=0.50)))
    return build_daily_returns(trades, daily_index)


def report_phase(label, daily_ret, data_start, data_end, phase):
    r = rolling_pass_rate_daily(daily_ret, data_start, data_end, phase=phase, max_days=MAX_DAYS,
                                 best_day_cap=BEST_DAY_CAP)
    print(f"  {label} -- Phase {phase} (target {'10%' if phase==1 else '5%'}):")
    print(f"    n_challenges={r['n_challenges']}  "
          f"RAW pass rate={r['pass_rate_raw']*100:.1f}%  "
          f"CONSISTENCY-ADJUSTED pass rate={r['pass_rate_consistency']*100:.1f}%")
    print(f"    median days to pass (consistency-adjusted): {r['median_days_to_pass']:.1f}")
    print(f"    failure reasons: {r['reasons']}\n")
    return r


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    gold = gold_leg_daily_returns()
    us30 = us30_breakout_leg_daily_returns()

    idx = gold.index.union(us30.index)
    gold_a = gold.reindex(idx, fill_value=0.0)
    us30_a = us30.reindex(idx, fill_value=0.0)

    fixed = 0.5 * gold_a + 0.5 * us30_a

    std_gold, std_us30 = gold_a.std(), us30_a.std()
    w_full = (1.0 / std_gold) / (1.0 / std_gold + 1.0 / std_us30)
    insample_rp = w_full * gold_a + (1.0 - w_full) * us30_a

    w_roll = rolling_weight_series(gold_a, us30_a)
    rolling_rp = w_roll * gold_a + (1.0 - w_roll) * us30_a

    data_start, data_end = idx.min(), idx.max()
    print(f"Combined data span: {data_start.date()} -> {data_end.date()} ({len(idx)} days)\n")
    print(f"FTMO Challenge simulation: max_days={MAX_DAYS}, best_day_cap={BEST_DAY_CAP:.0%} "
          f"(assumed consistency threshold, stated explicitly)\n")

    rows = []
    for label, series in [
        ("Fixed 50/50", fixed),
        ("In-sample risk-parity (§51)", insample_rp),
        ("Rolling risk-parity (§52, deployable)", rolling_rp),
    ]:
        for phase in (1, 2):
            r = report_phase(label, series, data_start, data_end, phase)
            rows.append(dict(weighting=label, **r))

    out = RESULTS / "ftmo_check_best_candidate.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"Saved {out}")
    print("Trial count: 0 new (FTMO-ruleset check on already-scored legs, "
          "not a parameter search). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
