"""
four_way_combined_book.py — adds a 4th leg to Sec89's 3-way book: US30
macross (Sec43 params: fast=10/slow=30/ema_trend=100/k_atr=2.5/R=1.0/H=72),
already validated as a genuine diversifier for US30 breakout specifically
(Sec48: combined book beats both legs, Sharpe +1.707/+1.755 rolling).

**HONEST CAVEAT STATED UP FRONT, not after seeing results:** US30 macross
FAILED this project's own out-of-regime check (Sec67: Sharpe -1.175 on
2013-2017 data, a real money-loser standalone over that window) — unlike
ORB gold RETEST and US30 breakout, which both have some form of multi-year
out-of-regime confirmation (Sec68). Adding it here tests a SOFTER,
different question than the primary-candidate bar this project normally
applies: can a leg that fails standalone out-of-regime still add
DIVERSIFICATION value in combination, given the established finding
(Sec44-Sec57) that combined-book benefit depends on correlation structure
and quality gaps, not on every leg independently clearing every gate? This
is not a claim that US30 macross is now a rehabilitated standalone
candidate — it explicitly is not, per Sec67's unchanged verdict.

METHOD: rebuilds the US30 macross leg on the FULL 2013-2025 window (same
H1 2013-2017 + M1 2018-2025 concatenation as Sec87's US30 breakout leg
reconstruction), adds it to Sec89's 3-leg book (ORB gold RETEST, US30
breakout, VIX/real-yield sleeve) under the SAME generalized N-leg rolling
risk-parity scheme (research/three_way_combined_book.py's
rolling_weights_n(), unmodified).
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
from research.ftmo_check_headline_vs_new_book_same_window import us30_breakout_leg_daily_returns_full
from research.three_way_combined_book import rolling_weights_n
from research.run_cot_gold_signal import annualized_sharpe, max_drawdown
from research.ftmo_check_6x_reference import two_phase_chain
from strategies.sweep_families import ma_cross, TF_DELTA

RESULTS = _ROOT / "results"
US30_H1_2013_2017 = _ROOT / "data" / "US30_H1_2013_2017_cfd_dukascopy.csv"
US30_M1_2018_2025 = _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv"
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
MACROSS_PARAMS = dict(fast=10, slow=30, ema_trend=100, k_atr=2.5, R=1.0, H=72)


def us30_macross_leg_daily_returns_full() -> pd.Series:
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
    cands = ma_cross(mh4, MACROSS_PARAMS, TF_DELTA["H4"])
    for t in cands:
        t["session_end"] = pd.Timestamp(t["session_end"]).tz_convert("UTC") if pd.Timestamp(t["session_end"]).tz else pd.Timestamp(t["session_end"]).tz_localize("UTC")
        t["entry_time"] = pd.Timestamp(t["entry_time"]).tz_convert("UTC") if pd.Timestamp(t["entry_time"]).tz else pd.Timestamp(t["entry_time"]).tz_localize("UTC")
    trades = de_overlap(simulate_trades(mh4, cands, strictly_after=True, cost_bps=COST_BPS))
    ret = build_daily_returns(trades, daily_index)
    ret.index = ret.index.tz_localize(None)
    return ret


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    gold = orb_gold_leg_daily_returns()
    us30_bo = us30_breakout_leg_daily_returns_full()
    sleeve = build_sleeve_daily_returns()
    us30_mc = us30_macross_leg_daily_returns_full()

    idx = gold.index.union(us30_bo.index).union(sleeve.index).union(us30_mc.index)
    gold = gold.reindex(idx, fill_value=0.0)
    us30_bo = us30_bo.reindex(idx, fill_value=0.0)
    sleeve = sleeve.reindex(idx, fill_value=0.0)
    us30_mc = us30_mc.reindex(idx, fill_value=0.0)

    print(f"US30 macross standalone (full 2013-2025): Sharpe={annualized_sharpe(us30_mc):+.3f} "
          f"maxDD={max_drawdown(equity_from_returns(us30_mc))*100:.1f}%  "
          f"(Sec67 found this leg FAILED out-of-regime on 2013-2017 alone: Sharpe -1.175 -- "
          f"stated here again, not hidden)\n")

    legs4 = {"orb_gold": gold, "us30_breakout": us30_bo, "sleeve": sleeve, "us30_macross": us30_mc}
    w4 = rolling_weights_n(legs4)
    rp4 = sum(w4[n] * legs4[n] for n in legs4)

    legs3 = {"orb_gold": gold, "us30_breakout": us30_bo, "sleeve": sleeve}
    w3 = rolling_weights_n(legs3)
    rp3 = sum(w3[n] * legs3[n] for n in legs3)

    eq3, eq4 = equity_from_returns(rp3), equity_from_returns(rp4)
    print(f"3-way (Sec89 reference, recomputed on this union index): Sharpe={annualized_sharpe(rp3):+.3f} "
          f"maxDD={max_drawdown(eq3)*100:.1f}%")
    print(f"4-way (+ US30 macross): Sharpe={annualized_sharpe(rp4):+.3f} maxDD={max_drawdown(eq4)*100:.1f}%\n")

    data_start, data_end = idx.min(), idx.max()
    print("FTMO chained funded-probability sweep, 4-way rolling risk-parity:")
    rows = []
    for mult in [1.0, 5.0, 8.0, 10.0, 12.0, 13.0, 14.0, 16.0, 18.0, 20.0]:
        scaled = mult * rp4
        eq = equity_from_returns(scaled)
        sh = annualized_sharpe(scaled)
        dd = max_drawdown(eq)
        chain = two_phase_chain(scaled, data_start, data_end)
        n_total = len(chain)
        n_funded = int((chain["funded"] == True).sum())
        print(f"  {mult:>4.0f}x: Sharpe={sh:+.3f} maxDD={dd*100:6.1f}% funded={n_funded}/{n_total} ({n_funded/n_total*100:5.1f}%)")
        rows.append(dict(multiplier=mult, sharpe=sh, max_dd=dd, funded_rate=n_funded / n_total))

    df = pd.DataFrame(rows)
    out = RESULTS / "four_way_combined_book.csv"
    df.to_csv(out, index=False)
    best = df.loc[df["funded_rate"].idxmax()]
    print(f"\n4-way peak: {best['funded_rate']*100:.1f}% at {best['multiplier']:.0f}x "
          f"(vs 3-way's 38.3% at 13x, this-session finer sweep)")
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio construction + FTMO check on four already-scored legs).")


if __name__ == "__main__":
    main()
