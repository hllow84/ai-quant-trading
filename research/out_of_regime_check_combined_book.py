"""
out_of_regime_check_combined_book.py -- SS68 follow-up to Sec67: re-runs
the ORB gold + US30 breakout combined book (Sec52, the project's "honest
deployable best") on the FULL 2013-2017 out-of-regime window, now that
the XAUUSD backfill (scripts/download_xauusd_2013_2017.sh,
data/XAUUSD_M1_2013_2017_spot_dukascopy.csv, 1.63M real bid/ask M1 rows)
has replaced the thin 2017-only stub Sec67 was forced to use. Same exact
tuned params as Sec52 (no re-optimization), same cost model/engine.
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
from research.metrics import sharpe, max_drawdown
from research.orb_retest_entry_stop_grid import mid_frame, build_trades as gold_build_trades
from research.combined_book_risk_parity_rolling import rolling_weight_series
from strategies.sweep_families import breakout_retest, TF_DELTA

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
COST_BPS = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
GOLD_OOR = _ROOT / "data" / "XAUUSD_M1_2013_2017_spot_dukascopy.csv"
US30_OOR = _ROOT / "data" / "US30_H1_2013_2017_cfd_dukascopy.csv"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    m, spot = mid_frame(GOLD_OOR)
    daily_index_g = aggregate_daily(spot).index
    tr = gold_build_trades(m, tol_frac=0.20, stop_mode="moderate")
    gold_ret = build_daily_returns(tr, daily_index_g)

    m1 = load_m1_mid(US30_OOR)
    daily_index_u = aggregate_daily(load_m1_spot(US30_OOR)).index
    mh4 = resample_mid(m1, "4h")
    cands = breakout_retest(mh4, dict(N=20, k_atr=4.0, R=0.25, H=20), TF_DELTA["H4"])
    for t in cands:
        t["session_end"] = pd.Timestamp(t["session_end"]).tz_convert("UTC") if pd.Timestamp(t["session_end"]).tz else pd.Timestamp(t["session_end"]).tz_localize("UTC")
        t["entry_time"] = pd.Timestamp(t["entry_time"]).tz_convert("UTC") if pd.Timestamp(t["entry_time"]).tz else pd.Timestamp(t["entry_time"]).tz_localize("UTC")
    trades = de_overlap(simulate_trades(mh4, cands, strictly_after=True, cost_bps=COST_BPS))
    us30_ret = build_daily_returns(trades, daily_index_u)

    idx = gold_ret.index.union(us30_ret.index)
    g = gold_ret.reindex(idx, fill_value=0.0)
    u = us30_ret.reindex(idx, fill_value=0.0)

    fixed = 0.5 * g + 0.5 * u
    w = rolling_weight_series(g, u)
    rp = w * g + (1.0 - w) * u

    rows = []
    for label, s in [("ORB gold RETEST standalone", g),
                      ("US30 breakout-retest standalone", u),
                      ("Combined, fixed 50/50", fixed),
                      ("Combined, rolling risk-parity (deployable)", rp)]:
        eq = equity_from_returns(s)
        sh = sharpe(s, BARS_PER_YEAR)
        dd = max_drawdown(eq)
        tot = float(eq.iloc[-1] - 1.0)
        yr_log = np.log1p(s).groupby(s.index.year).sum()
        n_pos = int((yr_log > 0).sum())
        n_years = len(yr_log)
        rows.append(dict(label=label, sharpe=sh, max_dd=dd, total_return=tot,
                          n_pos_years=n_pos, n_years=n_years))
        print(f"{label}: Sharpe={sh:+.3f}  maxDD={dd*100:.1f}%  total_return={tot*100:+.1f}%  "
              f"years+={n_pos}/{n_years}")

    out = RESULTS / "out_of_regime_check_combined_book.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"\nSaved {out}")
    print("Trial count: 0 new (Sec52's exact tuned config re-run on the newly-backfilled "
          "2013-2017 out-of-regime window). Cumulative trials: N=1645 unchanged.")


if __name__ == "__main__":
    main()
