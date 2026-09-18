"""
ftmo_check_headline_vs_new_book_same_window.py — apples-to-apples check:
research/ftmo_check_orb_gold_vix_real_yield.py found the NEW book (ORB gold
RETEST + VIX/real-yield sleeve) funds at 35.7% (6x-7x), apparently beating
the project's existing headline book (Sec52/Sec62: ORB gold + US30
breakout, peak 33.0% at 14x) — BUT that comparison used two DIFFERENT
calendar windows: the new book was scored on the full 2013-2025 span (13yr,
including the 2013-2017 out-of-regime period where gold performed
exceptionally, Sec68), while every existing headline-book FTMO number
(Sec58-Sec66) was computed on 2017-2025 only (~9yr, US30 CFD data's
availability floor at the time). This is a real, stated caveat, not
swept aside — before concluding the new book is genuinely better, the
headline book must be re-scored on the SAME full 2013-2025 window using
its own already-established, unchanged parameters (Sec48/Sec52's ORB gold
RETEST + US30 breakout, rolling risk-parity).

METHOD: rebuilds the US30 breakout leg (Sec45's unchanged N=20/k_atr=4.0/
R=0.25/H=20 params) on the FULL 2013-2025 window by concatenating the
existing H1 2013-2017 and M1 2018-2025 Dukascopy files (resampled to H4
together, avoiding a discontinuity at the file boundary), combined with
research/orb_gold_real_yield_combined_book.py's already-full-window ORB
gold RETEST leg, under the SAME rolling (causal) risk-parity scheme as
Sec52. Then applies the identical multiplier sweep/two_phase_chain check
as the new book, on the SAME 2013-2025 span, for a genuinely comparable
number.

Zero new backtest trials on the underlying legs -- both engines reused
unchanged; this is a window-alignment + FTMO-ruleset check, not a
parameter search.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, load_m1_mid, resample_mid, aggregate_daily
from research.ftmo_engine import simulate_trades, de_overlap, build_daily_returns, equity_from_returns
from research.orb_gold_real_yield_combined_book import orb_gold_leg_daily_returns
from research.orb_gold_vix_real_yield_combined_book import build_sleeve_daily_returns
from research.combined_book_risk_parity_rolling import rolling_weight_series
from research.ftmo_check_6x_reference import two_phase_chain
from research.metrics import max_drawdown, sharpe
from strategies.sweep_families import breakout_retest, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
MULTIPLIERS = [1.0, 3.0, 5.0, 6.0, 7.0, 8.0, 10.0, 14.0]

US30_H1_2013_2017 = _ROOT / "data" / "US30_H1_2013_2017_cfd_dukascopy.csv"
US30_M1_2018_2025 = _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv"
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)


def us30_breakout_leg_daily_returns_full() -> pd.Series:
    m1_13_17 = load_m1_mid(US30_H1_2013_2017)
    m1_18_25 = load_m1_mid(US30_M1_2018_2025)
    m1 = pd.concat([m1_13_17, m1_18_25]).sort_index()
    m1 = m1[~m1.index.duplicated(keep="first")]

    spot_13_17 = load_m1_spot(US30_H1_2013_2017)
    spot_18_25 = load_m1_spot(US30_M1_2018_2025)
    spot = pd.concat([spot_13_17, spot_18_25]).sort_index()
    spot = spot[~spot.index.duplicated(keep="first")]
    daily_index = aggregate_daily(spot).index

    mh4 = resample_mid(m1, "4h")
    cands = breakout_retest(mh4, dict(N=20, k_atr=4.0, R=0.25, H=20), TF_DELTA["H4"])
    for t in cands:
        t["session_end"] = pd.Timestamp(t["session_end"]).tz_convert("UTC") if pd.Timestamp(t["session_end"]).tz else pd.Timestamp(t["session_end"]).tz_localize("UTC")
        t["entry_time"] = pd.Timestamp(t["entry_time"]).tz_convert("UTC") if pd.Timestamp(t["entry_time"]).tz else pd.Timestamp(t["entry_time"]).tz_localize("UTC")
    trades = de_overlap(simulate_trades(mh4, cands, strictly_after=True, cost_bps=COST_BPS))
    ret = build_daily_returns(trades, daily_index)
    ret.index = ret.index.tz_localize(None)
    return ret


def run_chain_sweep(series: pd.Series, data_start, data_end, label: str) -> pd.DataFrame:
    rows = []
    for mult in MULTIPLIERS:
        scaled = mult * series
        eq = equity_from_returns(scaled)
        sh = sharpe(scaled, BARS_PER_YEAR)
        dd = max_drawdown(eq)
        chain = two_phase_chain(scaled, data_start, data_end)
        n_total = len(chain)
        n_funded = int((chain["funded"] == True).sum())
        print(f"  {label} @ {mult:.0f}x: Sharpe={sh:+.3f} maxDD={dd*100:.1f}% "
              f"funded={n_funded}/{n_total} ({n_funded/n_total*100:.1f}%)")
        rows.append(dict(book=label, multiplier=mult, sharpe=sh, max_dd=dd,
                          n_challenges=n_total, funded_rate=n_funded / n_total))
    return pd.DataFrame(rows)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    gold = orb_gold_leg_daily_returns()
    us30 = us30_breakout_leg_daily_returns_full()
    sleeve = build_sleeve_daily_returns()

    idx = gold.index.union(us30.index).union(sleeve.index)
    gold = gold.reindex(idx, fill_value=0.0)
    us30 = us30.reindex(idx, fill_value=0.0)
    sleeve = sleeve.reindex(idx, fill_value=0.0)

    w = rolling_weight_series(gold, us30)
    headline_rp = w * gold + (1.0 - w) * us30
    new_book_fixed = 0.5 * gold + 0.5 * sleeve

    data_start, data_end = idx.min(), idx.max()
    print(f"Common window: {data_start.date()} -> {data_end.date()} ({len(idx)} days)\n")

    print("Standalone (1x) reference:")
    print(f"  Headline (ORB gold + US30 breakout, rolling RP): Sharpe={sharpe(headline_rp, BARS_PER_YEAR):+.3f} "
          f"maxDD={max_drawdown(equity_from_returns(headline_rp))*100:.1f}%")
    print(f"  New book (ORB gold + VIX/real-yield sleeve, fixed 50/50): Sharpe={sharpe(new_book_fixed, BARS_PER_YEAR):+.3f} "
          f"maxDD={max_drawdown(equity_from_returns(new_book_fixed))*100:.1f}%\n")

    print("FTMO chained funded-probability sweep, SAME 2013-2025 window for both books:")
    df1 = run_chain_sweep(headline_rp, data_start, data_end, "Headline")
    df2 = run_chain_sweep(new_book_fixed, data_start, data_end, "New book")

    df = pd.concat([df1, df2], ignore_index=True)
    out = RESULTS / "ftmo_check_headline_vs_new_book_same_window.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved {out}")

    peak1 = df1.loc[df1["funded_rate"].idxmax()]
    peak2 = df2.loc[df2["funded_rate"].idxmax()]
    print(f"\nHeadline peak: {peak1['funded_rate']*100:.1f}% at {peak1['multiplier']:.0f}x")
    print(f"New book peak: {peak2['funded_rate']*100:.1f}% at {peak2['multiplier']:.0f}x")
    print("\nTrial count: 0 new (window-alignment + FTMO-ruleset check). Cumulative trials: N=1717 unchanged.")


if __name__ == "__main__":
    main()
