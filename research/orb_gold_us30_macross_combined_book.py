"""
orb_gold_us30_macross_combined_book.py — ORB gold RETEST + US30 MACROSS
combined book (§54), a seventh pairing (sixth requested this session) on
the same cross-asset-class axis as §49 but with the OTHER US30 family:
macross instead of breakout. Completes the "ORB gold x both US30
candidates" 2-pairing set (§49 did gold+breakout, this does gold+macross)
and is a genuinely new combination not yet tested.

Legs, both independently strong (both beat their own buy-and-hold):
- ORB gold RETEST (§39): XAUUSD, retest_tol_frac=0.20/stop_mode=
  'moderate'/target=1R, Sharpe +1.488 standalone.
- US30 macross (§43): fast=10/slow=30/ema_trend=100/k_atr=2.5/R=1.0/H=72,
  Sharpe +0.999 standalone.

Quality gap ~1.49x (1.488/0.999) — smaller than §49's gold+breakout gap
(1.488 vs 1.684, actually gold was the WEAKER leg there; here gold is the
STRONGER leg and macross the weaker one, a genuinely different shape) and
smaller than every quality-gap pairing tested so far except §50's ~1.8x
and this session's own §53 ~1.75x — worth checking directly rather than
assuming the outcome from gap size alone, per §53's own conclusion that
gap size is not fully predictive.

Method: identical to every prior pairing — both legs' own unchanged
engines/params (ORB gold reuses research/orb_gold_us30_breakout_combined_
book.py's run_orb_gold_leg() unchanged; US30 macross reuses strategies/
sweep_families.py's ma_cross() unchanged), daily log-returns aligned on
the union of trading days, tested at both fixed 50/50 and in-sample
risk-parity weight (§51's adopted default).

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
from strategies.sweep_families import ma_cross, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
US30_DATA = _ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv"


def run_us30_macross_leg():
    m1 = load_m1_mid(US30_DATA)
    daily_index = aggregate_daily(load_m1_spot(US30_DATA)).index
    m = resample_mid(m1, "4h")
    params = dict(fast=10, slow=30, ema_trend=100, k_atr=2.5, R=1.0, H=72)
    cands = ma_cross(m, params, TF_DELTA["H4"])
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
    print("--- US30 macross standalone (leg re-run, unchanged params) ---")
    print(f"  n={len(trades)} guard={guard} grossPF={profit_factor(trades['gross_R']):.3f} "
          f"netPF={profit_factor(trades['net_R']):.3f} Sharpe={sh:+.3f} maxDD={dd*100:.1f}%\n")
    return daily_ret, sh, dd


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    gold_ret, gold_sh, gold_dd = run_orb_gold_leg()
    us30_ret, us30_sh, us30_dd = run_us30_macross_leg()

    idx = gold_ret.index.union(us30_ret.index)
    gold = gold_ret.reindex(idx, fill_value=0.0)
    us30 = us30_ret.reindex(idx, fill_value=0.0)

    corr = float(np.corrcoef(gold.values, us30.values)[0, 1])
    print(f"Correlation of daily log-returns (aligned, {len(idx)} days): {corr:+.3f}\n")

    fixed = 0.5 * gold + 0.5 * us30
    sh_fixed, dd_fixed = sharpe(fixed, BARS_PER_YEAR), max_drawdown(equity_from_returns(fixed))

    std_gold, std_us30 = gold.std(), us30.std()
    w_gold = (1.0 / std_gold) / (1.0 / std_gold + 1.0 / std_us30)
    rp = w_gold * gold + (1.0 - w_gold) * us30
    sh_rp, dd_rp = sharpe(rp, BARS_PER_YEAR), max_drawdown(equity_from_returns(rp))

    yr_fixed = fixed.groupby(fixed.index.year).sum()
    yr_rp = rp.groupby(rp.index.year).sum()

    print("=== Combined book: ORB gold RETEST + US30 macross ===")
    print(f"  Fixed 50/50:                 Sharpe={sh_fixed:+.3f}  maxDD={dd_fixed*100:.1f}%  "
          f"years_pos={int((yr_fixed>0).sum())}/{len(yr_fixed)}")
    print(f"  Risk-parity ({w_gold:.2f}/{1-w_gold:.2f}):        Sharpe={sh_rp:+.3f}  maxDD={dd_rp*100:.1f}%  "
          f"years_pos={int((yr_rp>0).sum())}/{len(yr_rp)}")
    print()
    print("=== Comparison ===")
    print(f"  ORB gold standalone:   Sharpe {gold_sh:+.3f}, maxDD {gold_dd*100:.1f}%")
    print(f"  US30 macross standalone: Sharpe {us30_sh:+.3f}, maxDD {us30_dd*100:.1f}%")
    print(f"  (naive average of standalone Sharpes: {0.5*(gold_sh+us30_sh):+.3f})")

    out_df = pd.DataFrame({
        "date": idx,
        "orb_gold_ret": gold.values,
        "us30_macross_ret": us30.values,
        "combined_fixed_ret": fixed.values,
        "combined_rp_ret": rp.values,
    })
    out = RESULTS / "orb_gold_us30_macross_combined_book.csv"
    out_df.to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio-construction check on two already-scored "
          "session-best configs, no parameter search). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
