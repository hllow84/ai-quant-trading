"""
ftmo_check_walkforward_multiplier.py -- SS66: resolves (as far as a single
causal decision rule can) the Sec62/Sec63 open question of whether 6x or
14x standard risk is the better FTMO sizing choice, by testing a THIRD
option neither section tried: a WALK-FORWARD, fully causal multiplier
SELECTION rule, re-chosen at every monthly Challenge start using only
data available before that start (no look-ahead), rather than either
fixed multiplier chosen once from the full pooled sample.

WHY THIS MATTERS: Sec63 found 14x's headline 33.0% funded rate is
front-loaded (43.6% in 2017-2020, only ~26.7% in the two most recent
thirds) while 6x is comparatively stable (28.8% pooled halves range
17.5%-30.8%). Neither fixed choice is causal -- both were picked by
looking at the FULL 2017-2025 sample after the fact. A real trader
choosing sizing in, say, 2019 could not have known 14x would outperform
pooled, nor that its edge would fade later. This section asks: what
funded rate would a SIMPLE, CAUSAL sizing rule (no hindsight) have
actually delivered, walking forward through the same 94 monthly
challenge starts already used throughout Sec58-Sec63?

RULE (a priori, stated before running): at each Challenge start s, take
the trailing (all-history-before-s) daily-return series of the Sec52
rolling-risk-parity book, and pick the LARGEST candidate multiplier from
the same table used in Sec62 (2x-30x) whose TRAILING max drawdown (i.e.
what an allocator could have observed up to that point) does not exceed
a stated risk cap. Two caps tested for sensitivity: 15% and 20% (both
comfortably under FTMO's hard 10% max-total-DD limit at 1x but chosen
against the STRATEGY's own realized drawdown, which is what an allocator
actually watches -- the same logic FTMO traders use informally: "size
until my own equity curve's worst historical drawdown hits my comfort
limit"). Requires >=2 years (730 calendar days) of trailing history
before a multiplier is chosen at all; earlier challenge starts are
excluded from ALL three methods (walk-forward, fixed 6x, fixed 14x) for
a fair apples-to-apples comparison pool.

Zero new backtest trials -- reuses the Sec52 leg returns and Sec62-
corrected simulate_challenge_daily unchanged; this is a portfolio-
construction / sizing-policy check, not a parameter search on the
underlying strategies. Cumulative trial count unaffected by this section
(momentum family work earlier this session, Sec64, already moved N to
1645).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.ftmo_check_best_candidate import gold_leg_daily_returns, us30_breakout_leg_daily_returns
from research.combined_book_risk_parity_rolling import rolling_weight_series
from research.ftmo_challenge_daily import simulate_challenge_daily
from research.ftmo_engine import equity_from_returns
from research.metrics import max_drawdown

RESULTS = _ROOT / "results"
MAX_DAYS = 60
BEST_DAY_CAP = None  # Sec62 correction: 2-Step ruleset has no consistency rule
CANDIDATES = (2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.0, 13.0, 14.0, 15.0, 16.0, 18.0, 20.0, 25.0, 30.0)
MIN_TRAILING_DAYS = 730  # 2 years, calendar days
CAPS = (0.15, 0.20)
FIXED_REFS = (6.0, 14.0)
TRAILING_MODES = ("expanding", "rolling730")


def pick_multiplier(trailing: pd.Series, cap: float) -> float | None:
    """Largest candidate whose trailing (already-observed) maxDD stays
    under `cap`. None if even the smallest candidate breaches it."""
    best = None
    for m in CANDIDATES:
        eq = equity_from_returns(m * trailing)
        dd = max_drawdown(eq)
        if dd <= cap:
            if best is None or m > best:
                best = m
    return best


def chain_one(base: pd.Series, start: pd.Timestamp, multiplier: float, data_end: pd.Timestamp) -> dict:
    scaled = multiplier * base
    p1 = simulate_challenge_daily(scaled, start, target=0.10, max_days=MAX_DAYS, best_day_cap=BEST_DAY_CAP)
    if not p1["passed_consistency"]:
        return dict(start=start, multiplier=multiplier, phase1_pass=False, funded=False, reason=p1["reason"])
    p2_start = start + pd.Timedelta(days=p1["days_used"])
    if p2_start + pd.Timedelta(days=MAX_DAYS) > data_end:
        return dict(start=start, multiplier=multiplier, phase1_pass=True, funded=None, reason="phase2_no_runway")
    p2 = simulate_challenge_daily(scaled, p2_start, target=0.05, max_days=MAX_DAYS, best_day_cap=BEST_DAY_CAP)
    return dict(start=start, multiplier=multiplier, phase1_pass=True,
                funded=bool(p2["passed_consistency"]), reason=p2["reason"])


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    gold = gold_leg_daily_returns()
    us30 = us30_breakout_leg_daily_returns()
    idx = gold.index.union(us30.index)
    gold_a = gold.reindex(idx, fill_value=0.0)
    us30_a = us30.reindex(idx, fill_value=0.0)
    w_roll = rolling_weight_series(gold_a, us30_a)
    base = w_roll * gold_a + (1.0 - w_roll) * us30_a
    data_start, data_end = idx.min(), idx.max()

    starts = pd.date_range(
        start=pd.Timestamp(data_start.year, data_start.month, 1, tz=data_start.tz),
        end=data_end, freq="MS",
    )
    eligible = [s for s in starts
                if s >= data_start + pd.Timedelta(days=MIN_TRAILING_DAYS)
                and s + pd.Timedelta(days=MAX_DAYS) <= data_end]
    print(f"Eligible challenge starts (>= {MIN_TRAILING_DAYS}d trailing history available): "
          f"{len(eligible)} of {len(starts)} total monthly starts\n")

    tz = data_start.tz
    halves = [
        ("2017-2021 (H1)", pd.Timestamp("2017-01-01", tz=tz), pd.Timestamp("2021-06-01", tz=tz)),
        ("2021-2025 (H2)", pd.Timestamp("2021-06-01", tz=tz), pd.Timestamp("2026-01-01", tz=tz)),
    ]

    for mode in TRAILING_MODES:
        for cap in CAPS:
            print(f"=== WALK-FORWARD ({mode}), causal multiplier selection, "
                  f"trailing-maxDD cap = {cap*100:.0f}% ===")
            chosen_rows = []
            for s in eligible:
                if mode == "expanding":
                    trailing = base[base.index < s]
                else:  # rolling730
                    trailing = base[(base.index < s) & (base.index >= s - pd.Timedelta(days=730))]
                m = pick_multiplier(trailing, cap)
                if m is None:
                    m = CANDIDATES[0]  # floor: smallest candidate even if it also breaches (rare)
                chosen_rows.append(chain_one(base, s, m, data_end))
            wf = pd.DataFrame(chosen_rows)
            n = len(wf)
            n_funded = int((wf["funded"] == True).sum())
            mult_used = wf["multiplier"]
            print(f"  n_challenges={n}  multiplier range chosen: {mult_used.min():.0f}x-{mult_used.max():.0f}x "
                  f"(median {mult_used.median():.0f}x, {mult_used.nunique()} distinct values used)")
            print(f"  FUNDED (walk-forward): {n_funded}/{n} = {n_funded/n*100:.1f}%")

            for m_fixed in FIXED_REFS:
                fixed_rows = [chain_one(base, s, m_fixed, data_end) for s in eligible]
                fdf = pd.DataFrame(fixed_rows)
                n_f = int((fdf["funded"] == True).sum())
                print(f"  FUNDED (fixed {m_fixed:.0f}x, same eligible pool): {n_f}/{len(fdf)} = {n_f/len(fdf)*100:.1f}%")

            print("  -- era split (walk-forward) --")
            for name, lo, hi in halves:
                sub = wf[(wf["start"] >= lo) & (wf["start"] < hi)]
                if len(sub) == 0:
                    continue
                n_f = int((sub["funded"] == True).sum())
                print(f"    {name}: n={len(sub)}  funded={n_f}/{len(sub)}={n_f/len(sub)*100:.1f}%  "
                      f"median multiplier used={sub['multiplier'].median():.0f}x")
            print()

            out = RESULTS / f"ftmo_check_walkforward_multiplier_{mode}_cap{int(cap*100)}.csv"
            wf.to_csv(out, index=False)
            print(f"  Saved {out}\n")

    print("Trial count: 0 new (sizing-policy walk-forward check on already-scored "
          "legs, not a parameter search). Cumulative trials unaffected by this section.")


if __name__ == "__main__":
    main()
