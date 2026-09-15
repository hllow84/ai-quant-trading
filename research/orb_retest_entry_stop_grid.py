"""
orb_retest_entry_stop_grid.py — ORB gold RETEST: joint ENTRY (retest_tol_frac)
x STOP (stop_mode) grid, on the same continuous 2017-2025 XAUUSD span as
§33/report_retest_xauusd_2017_2025_continuous.py.

WHY THIS IS GENUINELY NEW (checked against the log first, per standing rule
1): §10.7 (2026-09-02) already exhausted the TARGET/exit dimension (2R, 3R,
breakeven-stop, trailing-stop(0.5R) all tested, none beat 1R or B&H) — that
thread stays closed, not re-run. What has NEVER been swept, confirmed by
grep across every script in this repo that calls orb(...), is:
  - retest_tol_frac: fixed at 0.10 everywhere, always.
  - stop_mode: 'moderate' (fixed 25bps) exists in strategies/orb.py and was
    tested on the UNFILTERED breakout in the 2026-08-29 audit (worse there),
    but never combined with retest=True — a materially different setup,
    since RETEST already changes both entry price and trade selection.

MECHANISM for each (stated a priori, before any result seen):
  retest_tol_frac controls how close price must return to the broken OR
  level before entry triggers. A TIGHTER tolerance (0.05) demands a cleaner,
  closer retest — selecting for stronger support/resistance re-confirmation
  at the cost of fewer trades (more setups cancelled for no valid retest). A
  LOOSER tolerance (0.20) accepts a sloppier pullback — more trades, but a
  worse average entry price relative to the stop (less of the move "given
  back" before the stop is levied), which should show up as a smaller
  R-multiple per trade actually banked. This is a real entry-quality
  tradeoff, not an arbitrary knob.

  stop_mode='moderate' (fixed 25bps stop, independent of the day's OR width)
  was originally motivated by cost efficiency (§10, AUDIT 4): the OR-width
  stop was never cost-chosen, so a smaller, cost-solved fixed stop could in
  principle raise cost_R efficiency. It already failed on the unfiltered
  breakout; testing it once more, specifically WITH the retest filter (which
  already improves entry quality and could interact differently with a
  fixed-vs-adaptive stop), is a genuinely different combination, not a
  repaint.

GRID (a priori): retest_tol_frac in {0.05, 0.10, 0.20} x stop_mode in
{'or_range', 'moderate'} = 6 cells. (0.10, 'or_range') REPRODUCES the known
§33 baseline exactly — computed for the table but NOT counted as a new
trial, matching this project's existing reproduction-check convention. 5 new
trials.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.ftmo_engine import (
    simulate_trades, de_overlap, RISK_PER_TRADE,
    build_daily_returns, build_position_series,
)
from research.dsr import deflated_sharpe
from strategies.orb import orb, ET

D = _ROOT / "data"
RESULTS = _ROOT / "results"
START_CAP = 100_000.0
BARS_PER_YEAR = 252
PRIOR_TRIALS = 1379
NEW_TRIALS = 5

ET_SESSION = dict(session_tz=ET, open_min=9 * 60 + 30, close_min=16 * 60, min_sess_bars=300)

FILE_2017 = D / "XAUUSD_M1_2017_spot_dukascopy.csv"
FILE_2018_2025 = D / "XAUUSD_M1_2018_2025_spot_dukascopy.csv"

TOL_FRACS = (0.05, 0.10, 0.20)
STOP_MODES = ("or_range", "moderate")


def mid_frame(path: Path):
    spot = load_m1_spot(path)
    m = pd.DataFrame(index=spot.index)
    for c in ("open", "high", "low", "close"):
        m[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
    m["spread"] = spot["spread"]
    m["volume"] = spot["volume"]
    return m, spot


def build_trades(m: pd.DataFrame, tol_frac: float, stop_mode: str) -> pd.DataFrame:
    params = dict(or_minutes=30, target="1R", stop_mode=stop_mode)
    cands = orb(m, params, retest=True, retest_tol_frac=tol_frac, **ET_SESSION)
    tr = de_overlap(simulate_trades(m, cands, strictly_after=False, cost_bps=None, slip_bps_fn=None))
    if tr.empty:
        return tr
    tr["entry_time"] = pd.to_datetime(tr["entry_time"], utc=True)
    tr["exit_time"] = pd.to_datetime(tr["exit_time"], utc=True)
    return tr.sort_values("exit_time").reset_index(drop=True)


def compound_final(net_R: pd.Series, start_cap: float) -> tuple[float, float]:
    eq = start_cap
    path = np.empty(len(net_R))
    for i, r in enumerate(net_R.to_numpy()):
        eq *= (1.0 + RISK_PER_TRADE * r)
        path[i] = eq
    running_peak = np.maximum.accumulate(np.concatenate(([start_cap], path)))
    dd = 1.0 - np.concatenate(([start_cap], path)) / running_peak
    return (path[-1] if len(path) else start_cap), float(dd.max())


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    m17, spot17 = mid_frame(FILE_2017)
    m18, spot18 = mid_frame(FILE_2018_2025)
    m = pd.concat([m17, m18]).sort_index()
    spot = pd.concat([spot17, spot18]).sort_index()
    daily_index = aggregate_daily(spot).index
    print(f"Continuous frame: {len(m):,} bars, {m.index[0]} -> {m.index[-1]}\n")

    rows = []
    for tol in TOL_FRACS:
        for stop_mode in STOP_MODES:
            is_baseline = (tol == 0.10 and stop_mode == "or_range")
            tr = build_trades(m, tol, stop_mode)
            label = f"tol{tol:.2f}_{stop_mode}" + (" [BASELINE, repro-only]" if is_baseline else "")

            if tr.empty:
                print(f"{label}: 0 trades\n")
                continue

            pos = build_position_series(tr, m.index)
            try:
                guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=0.5)
                guard = "PASS"
            except LookAheadError as exc:
                guard = f"FAIL:{str(exc)[:60]}"

            daily_ret = build_daily_returns(tr, daily_index)
            sr = sharpe(daily_ret, BARS_PER_YEAR)
            gpf = profit_factor(tr["gross_R"])
            npf = profit_factor(tr["net_R"])
            end_bal, trade_maxdd = compound_final(tr["net_R"], START_CAP)
            avg_gross_R = float(tr["gross_R"].mean())
            avg_net_R = float(tr["net_R"].mean())
            avg_cost_R = float(tr["cost_R"].mean())

            rows.append(dict(
                label=label, tol_frac=tol, stop_mode=stop_mode, is_baseline=is_baseline,
                n_trades=len(tr), guard=guard, gross_pf=gpf, net_pf=npf, sharpe=sr,
                trade_maxdd=trade_maxdd, end_balance=end_bal,
                total_return=end_bal / START_CAP - 1.0,
                avg_gross_R=avg_gross_R, avg_net_R=avg_net_R, avg_cost_R=avg_cost_R,
            ))
            print(f"--- {label} ---")
            print(f"  n_trades={len(tr)}  guard={guard}  grossPF={gpf:.3f}  netPF={npf:.3f}  "
                  f"Sharpe={sr:+.3f}")
            print(f"  avg_gross_R={avg_gross_R:+.3f}  avg_net_R={avg_net_R:+.3f}  "
                  f"avg_cost_R={avg_cost_R:.3f}")
            print(f"  compounded $100k -> ${end_bal:,.0f} ({end_bal/START_CAP-1:+.1%}), "
                  f"trade-level maxDD={trade_maxdd*100:.1f}%\n")

    df = pd.DataFrame(rows)
    new_rows = df[~df["is_baseline"]]
    sharpes = new_rows["sharpe"].tolist()
    print(f"=== Deflated Sharpe (structural pool: family=orb_retest_entry_stop, N={len(sharpes)} new trials) ===")
    for _, r in new_rows.iterrows():
        d = deflated_sharpe(r["sharpe"], sharpes, n_obs=r["n_trades"], ann_factor=BARS_PER_YEAR)
        print(f"  {r['label']}: Sharpe={r['sharpe']:+.3f}  DSR={d['dsr']:.4f}  pool_n={d['pool_n']}")

    baseline = df[df["is_baseline"]]
    if len(baseline):
        b = baseline.iloc[0]
        print(f"\nBaseline (tol=0.10, or_range) repro: Sharpe={b['sharpe']:+.3f}  netPF={b['net_pf']:.3f}  "
              f"end_balance=${b['end_balance']:,.0f}  (§33 on-record: Sharpe +1.097, 554 trades)")

    out = RESULTS / "orb_retest_entry_stop_grid.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved {out}")
    print(f"Trial count: {NEW_TRIALS} new. Cumulative N={PRIOR_TRIALS} -> {PRIOR_TRIALS + NEW_TRIALS}")


if __name__ == "__main__":
    main()
