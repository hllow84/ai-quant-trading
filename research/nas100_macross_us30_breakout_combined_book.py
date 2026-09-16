"""
nas100_macross_us30_breakout_combined_book.py — NAS100 MACROSS + US30
BREAKOUT combined book (§53), a new pairing on a combined axis not yet
tested directly: CROSS-instrument AND CROSS-family simultaneously (every
prior pairing varied only one of the two: §44/§47/§49/§50 varied
instrument or asset class while holding family fixed on at least one leg,
§48 varied family while holding instrument fixed). Both legs are
independently strong (both beat their own buy-and-hold):

- NAS100 macross (§42): fast=10/slow=30/ema_trend=200/k_atr=1.0/R=4.0/
  H=192, Sharpe +0.963 standalone, beats NAS100 B&H (+0.842).
- US30 breakout (§45): N=20/k_atr=4.0/R=0.25/H=20, Sharpe +1.684
  standalone, beats US30 B&H (+0.547).

Mechanism (a priori): combines two decorrelating forces at once (different
instrument, different signal family) so a priori correlation should be at
least as low as any single-axis pairing tested so far, and per the §50/
§51 revised rule ("diversification helps unless the quality gap is too
large relative to the correlation benefit"), a small quality gap (0.963
vs 1.684, ratio ~1.75x, similar to §50's ~1.8x which worked) combined with
likely very low correlation should favor a real improvement.

Method: identical to every prior pairing in this project — both legs run
with their own unchanged session-best params/functions/data, same cost
model/H4 resample/strictly_after=True, daily log-returns aligned on the
union of trading days, combined at fixed 50/50 weight AND at in-sample
risk-parity weight (per §51's now-adopted default), for direct comparison
against every other pairing tested.

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
    "NAS100_macross": dict(
        data=_ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv",
        fn=ma_cross,
        params=dict(fast=10, slow=30, ema_trend=200, k_atr=1.0, R=4.0, H=192),
    ),
    "US30_breakout": dict(
        data=_ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",
        fn=breakout_retest,
        params=dict(N=20, k_atr=4.0, R=0.25, H=20),
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

    idx = daily_rets["NAS100_macross"].index.union(daily_rets["US30_breakout"].index)
    nas = daily_rets["NAS100_macross"].reindex(idx, fill_value=0.0)
    us30 = daily_rets["US30_breakout"].reindex(idx, fill_value=0.0)

    corr = float(np.corrcoef(nas.values, us30.values)[0, 1])
    print(f"Correlation of daily log-returns (aligned, {len(idx)} days): {corr:+.3f}\n")

    fixed = 0.5 * nas + 0.5 * us30
    sh_fixed, dd_fixed = sharpe(fixed, BARS_PER_YEAR), max_drawdown(equity_from_returns(fixed))

    std_nas, std_us30 = nas.std(), us30.std()
    w_nas = (1.0 / std_nas) / (1.0 / std_nas + 1.0 / std_us30)
    rp = w_nas * nas + (1.0 - w_nas) * us30
    sh_rp, dd_rp = sharpe(rp, BARS_PER_YEAR), max_drawdown(equity_from_returns(rp))

    yr_log_fixed = fixed.groupby(fixed.index.year).sum()
    yr_log_rp = rp.groupby(rp.index.year).sum()

    print("=== Combined book: NAS100 macross + US30 breakout ===")
    print(f"  Fixed 50/50:        Sharpe={sh_fixed:+.3f}  maxDD={dd_fixed*100:.1f}%  "
          f"years_pos={int((yr_log_fixed>0).sum())}/{len(yr_log_fixed)}")
    print(f"  Risk-parity ({w_nas:.2f}/{1-w_nas:.2f}): Sharpe={sh_rp:+.3f}  maxDD={dd_rp*100:.1f}%  "
          f"years_pos={int((yr_log_rp>0).sum())}/{len(yr_log_rp)}")
    print()
    print("=== Comparison ===")
    print(f"  NAS100 macross standalone: Sharpe {standalone['NAS100_macross']['sharpe']:+.3f}, maxDD {standalone['NAS100_macross']['max_dd']*100:.1f}%")
    print(f"  US30 breakout standalone:  Sharpe {standalone['US30_breakout']['sharpe']:+.3f}, maxDD {standalone['US30_breakout']['max_dd']*100:.1f}%")
    naive_avg_sharpe = 0.5 * (standalone["NAS100_macross"]["sharpe"] + standalone["US30_breakout"]["sharpe"])
    print(f"  (naive average of standalone Sharpes: {naive_avg_sharpe:+.3f})")

    out_df = pd.DataFrame({
        "date": idx,
        "nas100_macross_ret": nas.values,
        "us30_breakout_ret": us30.values,
        "combined_fixed_ret": fixed.values,
        "combined_rp_ret": rp.values,
    })
    out = RESULTS / "nas100_macross_us30_breakout_combined_book.csv"
    out_df.to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (portfolio-construction check on two already-scored "
          "session-best configs, no parameter search). Cumulative trials: N=1570 unchanged.")


if __name__ == "__main__":
    main()
