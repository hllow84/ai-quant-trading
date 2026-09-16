"""
orb_gold_nas100_breakout_combined_book.py — ORB gold RETEST + NAS100
BREAKOUT combined book (§57), the tenth and final pairing, completing
ALL C(5,2)=10 possible combinations from this project's 5-leg candidate
pool (NAS100 macross, NAS100 breakout, US30 macross, US30 breakout, ORB
gold).

Legs:
- ORB gold RETEST (§39): XAUUSD, retest_tol_frac=0.20/stop_mode=
  'moderate'/target=1R, Sharpe +1.488 standalone, beats gold B&H.
- NAS100 breakout (§46): N=70/k_atr=1.0/R=1.75/H=90, Sharpe +0.526
  standalone — does NOT beat NAS100 buy-and-hold, the weakest candidate
  in the project.

Quality gap ~2.8x (1.488/0.526) — the SECOND-largest gap tested (behind
only §47's 3.2x, which failed under fixed 50/50). Pairs this project's
single strongest leg with its single weakest leg, across the widest
asset-class divide (gold vs equity index) — a genuine stress test of
whether even the lowest correlations found in this project (gold pairings
have consistently been the lowest, §49/§54/§55) can overcome a gap this
large, or whether gap size dominates once it gets large enough regardless
of correlation.

Method: identical to every prior pairing — both legs' own unchanged
engines/params (ORB gold reuses research/orb_gold_us30_breakout_combined_
book.py's run_orb_gold_leg() unchanged; NAS100 breakout reuses strategies/
sweep_families.py's breakout_retest() unchanged), daily log-returns
aligned on the union of trading days, tested at both fixed 50/50 and
in-sample risk-parity weight.

Zero new trials — a portfolio-construction check on two already-scored
cells, no parameter search. Cumulative trial count (N=1570) unchanged.
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
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns, build_position_series,
)
from research.orb_gold_us30_breakout_combined_book import run_orb_gold_leg
from strategies.sweep_families import breakout_retest, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
NAS100_DATA = _ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv"


def run_nas100_breakout_leg():
    m1 = load_m1_mid(NAS100_DATA)
    daily_index = aggregate_daily(load_m1_spot(NAS100_DATA)).index
    m = resample_mid(m1, "4h")
    params = dict(N=70, k_atr=1.0, R=1.75, H=90)
    cands = breakout_retest(m, params, TF_DELTA["H4"])
    for t in cands:
        t["session_end"] = pd.Timestamp(t["session_end"]).tz_convert("UTC") if pd.Timestamp(t["session_end"]).tz else pd.Timestamp(t["session_end"]).tz_localize("UTC")
        t["entry_time"] = pd.Timestamp(t["entry_time"]).tz_convert("UTC") if pd.Timestamp(t["entry_time"]).tz else pd.Timestamp(t["entry_time"]).tz_localize("UTC")
    trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=COST_BPS))
    pos = build_position_series(trades, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"
    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    sh = sharpe(daily_ret, BARS_PER_YEAR)
    dd = max_drawdown(equity)
    print("--- NAS100 breakout standalone (leg re-run, unchanged params) ---")
    print(f"  n={len(trades)} guard={guard} grossPF={profit_factor(trades['gross_R']):.3f} "
          f"netPF={profit_factor(trades['net_R']):.3f} Sharpe={sh:+.3f} maxDD={dd*100:.1f}%\n")
    return daily_ret, sh, dd


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    gold_ret, gold_sh, gold_dd = run_orb_gold_leg()
    nas_ret, nas_sh, nas_dd = run_nas100_breakout_leg()

    idx = gold_ret.index.union(nas_ret.index)
    gold = gold_ret.reindex(idx, fill_value=0.0)
    nas = nas_ret.reindex(idx, fill_value=0.0)

    corr = float(np.corrcoef(gold.values, nas.values)[0, 1])
    print(f"Correlation of daily log-returns (aligned, {len(idx)} days): {corr:+.3f}\n")

    fixed = 0.5 * gold + 0.5 * nas
    sh_fixed, dd_fixed = sharpe(fixed, BARS_PER_YEAR), max_drawdown(equity_from_returns(fixed))

    std_gold, std_nas = gold.std(), nas.std()
    w_gold = (1.0 / std_gold) / (1.0 / std_gold + 1.0 / std_nas)
    rp = w_gold * gold + (1.0 - w_gold) * nas
    sh_rp, dd_rp = sharpe(rp, BARS_PER_YEAR), max_drawdown(equity_from_returns(rp))

    yr_fixed = fixed.groupby(fixed.index.year).sum()
    yr_rp = rp.groupby(rp.index.year).sum()

    print("=== Combined book: ORB gold RETEST + NAS100 breakout ===")
    print(f"  Fixed 50/50:            Sharpe={sh_fixed:+.3f}  maxDD={dd_fixed*100:.1f}%  "
          f"years_pos={int((yr_fixed>0).sum())}/{len(yr_fixed)}")
    print(f"  Risk-parity ({w_gold:.2f}/{1-w_gold:.2f}):   Sharpe={sh_rp:+.3f}  maxDD={dd_rp*100:.1f}%  "
          f"years_pos={int((yr_rp>0).sum())}/{len(yr_rp)}")
    print()
    print("=== Comparison ===")
    print(f"  ORB gold standalone:      Sharpe {gold_sh:+.3f}, maxDD {gold_dd*100:.1f}%")
    print(f"  NAS100 breakout standalone: Sharpe {nas_sh:+.3f}, maxDD {nas_dd*100:.1f}%")
    print(f"  (naive average of standalone Sharpes: {0.5*(gold_sh+nas_sh):+.3f})")

    out_df = pd.DataFrame({
        "date": idx,
        "orb_gold_ret": gold.values,
        "nas100_breakout_ret": nas.values,
        "combined_fixed_ret": fixed.values,
        "combined_rp_ret": rp.values,
    })
    out = RESULTS / "orb_gold_nas100_breakout_combined_book.csv"
    out_df.to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio-construction check on two already-scored "
          "session-best configs, no parameter search). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
