"""
nas100_breakout_us30_macross_combined_book.py — NAS100 BREAKOUT + US30
MACROSS combined book (§56), the ninth pairing, one of the two remaining
untested combinations from this project's 5-leg candidate pool (NAS100
macross, NAS100 breakout, US30 macross, US30 breakout, ORB gold — 10
possible pairs, 8 already tested in §44/§47/§48/§49/§50/§53/§54/§55).

Legs:
- NAS100 breakout (§46): N=70/k_atr=1.0/R=1.75/H=90, Sharpe +0.526
  standalone — does NOT beat NAS100 buy-and-hold (+0.842), the weakest
  candidate in the project.
- US30 macross (§43): fast=10/slow=30/ema_trend=100/k_atr=2.5/R=1.0/H=72,
  Sharpe +0.999 standalone — beats US30 buy-and-hold (+0.547).

Quality gap ~1.9x (0.999/0.526), the LARGEST gap tested since §47's 3.2x
(which failed under fixed 50/50, needing risk-parity to partially
rescue it) — a real test of whether a large-but-not-extreme gap (1.9x,
between §50's 1.8x-that-worked and §47's 3.2x-that-failed) behaves like
either precedent or its own thing, per §53/§55's repeated finding that
outcome is not fully predictable from gap size alone.

Method: identical to every prior pairing — both legs' own unchanged
engines/params, daily log-returns aligned on the union of trading days,
tested at both fixed 50/50 and in-sample risk-parity weight.

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
from research.ftmo_engine import simulate_trades, de_overlap, build_daily_returns, equity_from_returns, build_position_series
from strategies.sweep_families import ma_cross, breakout_retest, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)

LEGS = {
    "NAS100_breakout": dict(
        data=_ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv",
        fn=breakout_retest,
        params=dict(N=70, k_atr=1.0, R=1.75, H=90),
    ),
    "US30_macross": dict(
        data=_ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",
        fn=ma_cross,
        params=dict(fast=10, slow=30, ema_trend=100, k_atr=2.5, R=1.0, H=72),
    ),
}


def run_leg(name, cfg):
    m1 = load_m1_mid(cfg["data"])
    daily_index = aggregate_daily(load_m1_spot(cfg["data"])).index
    m = resample_mid(m1, "4h")
    cands = cfg["fn"](m, cfg["params"], TF_DELTA["H4"])
    for tr in cands:
        tr["session_end"] = pd.Timestamp(tr["session_end"]).tz_convert("UTC") if pd.Timestamp(tr["session_end"]).tz else pd.Timestamp(tr["session_end"]).tz_localize("UTC")
        tr["entry_time"] = pd.Timestamp(tr["entry_time"]).tz_convert("UTC") if pd.Timestamp(tr["entry_time"]).tz else pd.Timestamp(tr["entry_time"]).tz_localize("UTC")
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
    print(f"--- {name} standalone (leg re-run, unchanged params) ---")
    print(f"  n={len(trades)} guard={guard} grossPF={profit_factor(trades['gross_R']):.3f} "
          f"netPF={profit_factor(trades['net_R']):.3f} Sharpe={sh:+.3f} maxDD={dd*100:.1f}%\n")
    return daily_ret, sh, dd


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    daily_rets, standalone = {}, {}
    for name, cfg in LEGS.items():
        dr, sh, dd = run_leg(name, cfg)
        daily_rets[name] = dr
        standalone[name] = dict(sharpe=sh, max_dd=dd)

    idx = daily_rets["NAS100_breakout"].index.union(daily_rets["US30_macross"].index)
    nas = daily_rets["NAS100_breakout"].reindex(idx, fill_value=0.0)
    us30 = daily_rets["US30_macross"].reindex(idx, fill_value=0.0)

    corr = float(np.corrcoef(nas.values, us30.values)[0, 1])
    print(f"Correlation of daily log-returns (aligned, {len(idx)} days): {corr:+.3f}\n")

    fixed = 0.5 * nas + 0.5 * us30
    sh_fixed, dd_fixed = sharpe(fixed, BARS_PER_YEAR), max_drawdown(equity_from_returns(fixed))

    std_nas, std_us30 = nas.std(), us30.std()
    w_nas = (1.0 / std_nas) / (1.0 / std_nas + 1.0 / std_us30)
    rp = w_nas * nas + (1.0 - w_nas) * us30
    sh_rp, dd_rp = sharpe(rp, BARS_PER_YEAR), max_drawdown(equity_from_returns(rp))

    yr_fixed = fixed.groupby(fixed.index.year).sum()
    yr_rp = rp.groupby(rp.index.year).sum()

    print("=== Combined book: NAS100 breakout + US30 macross ===")
    print(f"  Fixed 50/50:              Sharpe={sh_fixed:+.3f}  maxDD={dd_fixed*100:.1f}%  "
          f"years_pos={int((yr_fixed>0).sum())}/{len(yr_fixed)}")
    print(f"  Risk-parity ({w_nas:.2f}/{1-w_nas:.2f}):        Sharpe={sh_rp:+.3f}  maxDD={dd_rp*100:.1f}%  "
          f"years_pos={int((yr_rp>0).sum())}/{len(yr_rp)}")
    print()
    print("=== Comparison ===")
    print(f"  NAS100 breakout standalone: Sharpe {standalone['NAS100_breakout']['sharpe']:+.3f}, maxDD {standalone['NAS100_breakout']['max_dd']*100:.1f}%")
    print(f"  US30 macross standalone:    Sharpe {standalone['US30_macross']['sharpe']:+.3f}, maxDD {standalone['US30_macross']['max_dd']*100:.1f}%")
    print(f"  (naive average of standalone Sharpes: {0.5*(standalone['NAS100_breakout']['sharpe']+standalone['US30_macross']['sharpe']):+.3f})")

    out_df = pd.DataFrame({
        "date": idx,
        "nas100_breakout_ret": nas.values,
        "us30_macross_ret": us30.values,
        "combined_fixed_ret": fixed.values,
        "combined_rp_ret": rp.values,
    })
    out = RESULTS / "nas100_breakout_us30_macross_combined_book.csv"
    out_df.to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio-construction check on two already-scored "
          "session-best configs, no parameter search). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
