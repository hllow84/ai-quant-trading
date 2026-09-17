"""
out_of_regime_check_refined_candidates.py -- SS67: the out-of-regime test
that killed every prior "winner" in this project (index basket, Sneaky
Pivot, the original ORB, M1 momentum -- all looked real on 2018-2025 and
were re-run UNCHANGED on 2013-2017 data) has NEVER been run on the
Sec39-Sec66 refined candidates. Those were found AND tuned entirely on
2018-2025 data via the joint entry/exit/SL/TP grid method -- this closes
that gap before any live-money decision, per explicit user request
2026-09-17.

DATA: NAS100 and US30 have continuous (non-RTH-restricted) real-spread H1
data covering 2013-09-30 -> 2017-12-29 (data/NAS100_H1_2013_2017_cfd_
dukascopy.csv, data/US30_H1_2013_2017_cfd_dukascopy.csv) -- resampled to
H4 exactly like the 2018-2025 M1 data, just from a coarser native
resolution (same schema, same research/gold_data.py loader, no special-
casing). XAUUSD only has a 2017 stub (data/XAUUSD_M1_2017_spot_
dukascopy.csv, single year, NOT a full 2013-2017 window) -- weaker
evidence, stated explicitly, not treated as equivalent to the index
windows.

METHOD: re-run each candidate's EXACT already-tuned params (no re-
optimization -- that would defeat the purpose of an out-of-regime test)
against the out-of-regime data, same cost model/engine/resolution as the
in-regime version. Report gross PF, net PF, Sharpe, maxDD, vs the
window's own buy-and-hold, exactly as this project's own out-of-regime
convention has always been applied (Sec2, Sec9.4, Sec10).

Zero new backtest trials in the "parameter search" sense -- these are the
SAME configs re-run on different data, not a new search. Cumulative
trial count unaffected (N=1645 unchanged by this check itself, though it
may downgrade/kill candidates depending on the result).
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
from research.orb_retest_entry_stop_grid import mid_frame, build_trades as gold_build_trades
from strategies.sweep_families import ma_cross, breakout_retest, momentum, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)

NAS100_OOR = _ROOT / "data" / "NAS100_H1_2013_2017_cfd_dukascopy.csv"
US30_OOR = _ROOT / "data" / "US30_H1_2013_2017_cfd_dukascopy.csv"
GOLD_OOR = _ROOT / "data" / "XAUUSD_M1_2013_2017_spot_dukascopy.csv"


def score_h4(data_path, fn, params, label, native_freq_note):
    m1 = load_m1_mid(data_path)
    daily_index = aggregate_daily(load_m1_spot(data_path)).index
    m = resample_mid(m1, "4h")
    cands = fn(m, params, TF_DELTA["H4"])
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
    daily = aggregate_daily(load_m1_spot(data_path))
    bah_ret = np.log(daily["mid_close"] / daily["mid_close"].shift(1)).dropna()
    bah_sharpe = sharpe(bah_ret, BARS_PER_YEAR)
    yr_log = np.log1p(daily_ret).groupby(daily_ret.index.year).sum()
    n_pos = int((yr_log > 0).sum())
    n_years = len(yr_log)
    result = dict(
        label=label, native=native_freq_note, n_trades=len(trades), guard=guard,
        gross_pf=profit_factor(trades["gross_R"]) if len(trades) else float("nan"),
        net_pf=profit_factor(trades["net_R"]) if len(trades) else float("nan"),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR), max_dd=max_drawdown(equity),
        bah_sharpe=bah_sharpe, beats_bah=sharpe(daily_ret, BARS_PER_YEAR) > bah_sharpe,
        n_pos_years=n_pos, n_years=n_years,
        span=f"{m.index[0].date()} -> {m.index[-1].date()}",
    )
    print(f"--- {label} ({native_freq_note}) ---")
    print(f"  span={result['span']}  n={result['n_trades']} guard={result['guard']}")
    print(f"  grossPF={result['gross_pf']:.3f}  netPF={result['net_pf']:.3f}  "
          f"Sharpe={result['sharpe']:+.3f}  maxDD={result['max_dd']*100:.1f}%  "
          f"B&H Sharpe={result['bah_sharpe']:+.3f}  beats B&H={result['beats_bah']}  "
          f"years+={result['n_pos_years']}/{result['n_years']}\n")
    return result


def score_gold_orb(data_path, label):
    m, spot = mid_frame(data_path)
    daily_index = aggregate_daily(spot).index
    tr = gold_build_trades(m, tol_frac=0.20, stop_mode="moderate")
    if len(tr) == 0:
        print(f"--- {label} ---\n  0 trades\n")
        return dict(label=label, native="M1 (native)", n_trades=0, guard="N/A",
                     gross_pf=float("nan"), net_pf=float("nan"), sharpe=float("nan"),
                     max_dd=float("nan"), bah_sharpe=float("nan"), beats_bah=False,
                     n_pos_years=0, n_years=0, span="n/a")
    daily_ret = build_daily_returns(tr, daily_index)
    equity = equity_from_returns(daily_ret)
    daily = aggregate_daily(spot)
    bah_ret = np.log(daily["mid_close"] / daily["mid_close"].shift(1)).dropna()
    bah_sharpe = sharpe(bah_ret, BARS_PER_YEAR)
    yr_log = np.log1p(daily_ret).groupby(daily_ret.index.year).sum()
    result = dict(
        label=label, native="M1 (native)", n_trades=len(tr), guard="N/A (reused engine)",
        gross_pf=profit_factor(tr["gross_R"]), net_pf=profit_factor(tr["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR), max_dd=max_drawdown(equity),
        bah_sharpe=bah_sharpe, beats_bah=sharpe(daily_ret, BARS_PER_YEAR) > bah_sharpe,
        n_pos_years=int((yr_log > 0).sum()), n_years=len(yr_log),
        span=f"{m.index[0].date()} -> {m.index[-1].date()}",
    )
    print(f"--- {label} (M1 native, 2017 stub only -- NOT a full 2013-2017 window) ---")
    print(f"  span={result['span']}  n={result['n_trades']}")
    print(f"  grossPF={result['gross_pf']:.3f}  netPF={result['net_pf']:.3f}  "
          f"Sharpe={result['sharpe']:+.3f}  maxDD={result['max_dd']*100:.1f}%  "
          f"B&H Sharpe={result['bah_sharpe']:+.3f}  beats B&H={result['beats_bah']}  "
          f"years+={result['n_pos_years']}/{result['n_years']}\n")
    return result


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=== OUT-OF-REGIME CHECK on the Sec39-Sec66 refined candidates ===")
    print("NAS100/US30: continuous H1 2013-09-30 -> 2017-12-29 (resampled to H4, same schema as 2018-2025 M1).")
    print("XAUUSD: 2017 M1 stub only (NOT a full pre-2018 window) -- weaker evidence, stated explicitly.\n")

    rows = []
    rows.append(score_h4(NAS100_OOR, ma_cross, dict(fast=10, slow=30, ema_trend=200, k_atr=1.0, R=4.0, H=192),
                          "NAS100 H4 macross (Sec42 params)", "H1 native, resampled to H4"))
    rows.append(score_h4(US30_OOR, ma_cross, dict(fast=10, slow=30, ema_trend=100, k_atr=2.5, R=1.0, H=72),
                          "US30 H4 macross (Sec43 params)", "H1 native, resampled to H4"))
    rows.append(score_h4(US30_OOR, breakout_retest, dict(N=20, k_atr=4.0, R=0.25, H=20),
                          "US30 H4 breakout-retest (Sec45 params)", "H1 native, resampled to H4"))
    rows.append(score_h4(US30_OOR, momentum, dict(N=96, k_atr=1.25, R=5.0, H=192),
                          "US30 H4 momentum (Sec64 params)", "H1 native, resampled to H4"))
    rows.append(score_gold_orb(GOLD_OOR, "ORB gold RETEST (Sec39 params, tol_frac=0.20/moderate) -- 2013-2017 full backfill"))

    df = pd.DataFrame(rows)
    out = RESULTS / "out_of_regime_check_refined_candidates.csv"
    df.to_csv(out, index=False)

    print("=== SUMMARY ===")
    for _, r in df.iterrows():
        verdict = "SURVIVES" if (r["beats_bah"] and r["sharpe"] > 0) else "FAILS"
        print(f"  {r['label']}: Sharpe={r['sharpe']:+.3f} (B&H {r['bah_sharpe']:+.3f})  "
              f"netPF={r['net_pf']:.3f}  maxDD={r['max_dd']*100:.1f}%  n={r['n_trades']}  -> {verdict}")

    n_survive = int(((df["beats_bah"]) & (df["sharpe"] > 0)).sum())
    print(f"\n{n_survive}/{len(df)} candidates beat their OUT-OF-REGIME buy-and-hold with positive Sharpe.")
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
