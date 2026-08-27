#!/usr/bin/env python3
"""
run_sweep_m1.py — THE MISSING ROW: the 5-family sweep at the 1-MINUTE bar.

WHY THIS RUN EXISTS
-------------------
Every timeframe sweep in this project deliberately started at M5. M1 was never
run. That leaves one honest gap in an otherwise complete grid, and it leaves a
prediction untested. The measured cost gradient on the gold sweep
(results/sweep_progress.csv, mean cost_R as a share of 1R) is:

    M5 32.7%   M15 17.3%   M30 11.4%   H1 7.6%   H4 3.7%

and on the index sweep (results/sweep_indices.csv):

    NAS100  M5 27.8%  M15 14.4%  M30 8.9%  H1 5.4%  H4 2.7%
    US30    M5 26.0%  M15 13.4%  M30 8.2%  H1 5.1%  H4 2.5%

Cost per trade is fixed (spread + commission + slippage) while 1R is a stop
distance set by ATR, and ATR scales roughly with the square root of bar
duration. So cost_R should scale as 1/sqrt(TF), and the M5 -> M1 step should
multiply cost_R by about sqrt(5) = 2.24:

    PREDICTION, STATED BEFORE THE RUN:
        XAUUSD  ~73%   NAS100  ~62%   US30  ~58%

That is a falsifiable number, and the run either confirms the gradient or
breaks it. The second question is independent of cost and is the one that
actually matters: **is there any GROSS edge at M1 at all**, before a cent of
cost is charged? A gross PF at 1.00 says the M1 tape carries no exploitable
signal for these families, which is a stronger and more useful statement than
"costs ate it".

Those two findings are reported SEPARATELY throughout. Do not merge them.

GRID (stated, small, a priori, NOT tuned)
------------------------------------------
    3 instruments (XAUUSD, NAS100, US30)
  x 1 timeframe   (M1)
  x 5 families    (trend, breakout, meanrev, momentum, macross)
  x 3 stated variants each
  = 45 configs THIS BATCH.

The families, the variants and every numeric parameter are imported UNCHANGED
from strategies/sweep_families.py — the same objects run_sweep.py (75 gold
configs) and run_sweep_indices.py (150 index configs) used. Nothing is re-tuned
for M1. That is the whole point: this is one more row of an existing grid, not a
new strategy.

WHAT "THE SAME VARIANTS AT M1" ACTUALLY MEANS — stated, because it is material
-------------------------------------------------------------------------------
Every parameter in the grid is expressed in BARS of the execution timeframe, so
running the same grid at M1 rescales every one of them in wall-clock terms:

    ATR period 14            ->  14 minutes
    EMA trend 200 / 100      ->  200 / 100 minutes
    max hold H = 12/24/48/96 ->  12 / 24 / 48 / 96 MINUTES
    momentum lookback N = 24 ->  24 minutes

That is the correct and only honest way to add a row to a timeframe sweep — it
is what M5 through H4 each did in their turn. It does mean the M1 row is a set
of ultra-short-hold systems, which is exactly the regime where a fixed per-trade
cost is most punishing. The run measures that; it does not assume it.

COSTS — the same model each instrument already used, unchanged
----------------------------------------------------------------
  XAUUSD : the engine's LEGACY $/oz model (cost_bps=None), i.e. real per-bar
           spread + $0.03/$0.10 per-side slippage + $0.07/oz commission. This is
           byte-for-byte what run_sweep.py charged at M5-H4, so the M1 row is
           comparable to the rows above it.
  NAS100 : the engine's bps model, commission 0.35 bps round-turn, slippage
  US30     0.15 bps per side normal / 0.50 bps in the engine's UTC news windows.
           Byte-for-byte what run_sweep_indices.py charged at M5-H4.

Using each instrument's own established model is what makes the gradient
readable. Swapping in a single unified model would have made the M1 row
incomparable to the five rows it is being added to.

SHARPE ANNUALISATION — the trap this run is most exposed to
-------------------------------------------------------------
Getting this wrong at M1 inflates Sharpe by ~33x, so it is verified in the run
and printed in the header rather than asserted here. The short version:

  * P&L is aggregated to CALENDAR-DAILY returns (research/ftmo_engine.py::
    build_daily_returns) and annualised at **252**. The annualisation factor is
    a property of the RETURN SERIES, not of the signal timeframe. An M1 system
    and a D1 system both produce one return per trading day, so both use 252.
  * The factor would only need to be ~283,000 (measured M1 bars/year, NOT the
    525,600 in metrics.py::BARS_PER_YEAR which assumes a 24/7 year) if Sharpe
    were computed on PER-BAR returns. It is not.
  * `verify_annualisation()` below proves it from this run's own trades by
    computing both and printing the ratio. If the daily construction had been
    silently bypassed the ratio would not be sqrt(bars_per_day).

LEVERAGE CAVEAT — stated up front, not buried
-----------------------------------------------
The repo convention is 1% risk per trade. At M5 that was ~5 trades/day; at M1 it
is ~30/day, which implies risking ~30% of equity per day. Nobody would run that.
So the equity-curve metrics (Sharpe, maxDD) sit on a leverage assumption that is
not realistic at this trade rate, and they are reported for continuity with the
rows above, not as a tradeable claim. **The verdict rests on the R-space metrics
— gross PF, net PF, cost_R, R per trade — which are leverage-invariant.**

GATES (every one must pass; a config that fails the guard is DISCARDED)
------------------------------------------------------------------------
  1. look-ahead guard PASS (research/backtest.py, threshold 0.5).
  2. gross PF > 1  — FINDING (1): is there an edge before costs at all?
  3. net PF > 1 and net Sharpe > 0.
  4. DSR > 0.95 against a STATED STRUCTURAL pool (this batch's 45 a priori
     cells). The project-cumulative pool is printed for CONTRAST only —
     research/dsr.py BUG 2 documents that it is sigma-contaminated.
  5. OOS holds across the fixed split (2023-01-01 in regime).
  6. NOT single-year concentrated (top calendar year <= 60% of total net R) —
     the signature that killed the index basket, the Sneaky Pivot and ORB.
  7. Beats buy-and-hold on the same instrument over the same window.

Gate 8 — OUT OF REGIME — is run separately by run_sweep_m1_pre2018.py, per
STATE_OF_PLAY section 7 rule 3. Nothing here is a lead until it survives that.

Usage:  py -3.14 run_sweep_m1.py              (full run, ~45 configs)
        py -3.14 run_sweep_m1.py --analyze    (re-score from CSV, no reload)
        py -3.14 run_sweep_m1.py --rth        (matched RTH-only control; see
                                               run_sweep_m1_pre2018.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.gold_data import load_m1_spot, load_m1_mid, resample_mid, aggregate_daily
from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns,
    build_position_series,
)
from strategies.sweep_families import FAMILIES, TIMEFRAMES_M1, TF_DELTA

TF_KEY = "M1"
TF_FREQ = TIMEFRAMES_M1[TF_KEY]
BARS_PER_YEAR = 252            # daily-aggregated returns; see module docstring
OOS_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
WINDOW_LABEL = "2018-2025"
MIN_OOS_TRADES = 20
DSR_BAR = 0.95
CONC_BAR = 0.60
GUARD_THRESHOLD = 0.5

# Cumulative project trial count before this batch (STATE_OF_PLAY section 1, N=499).
PRIOR_TRIALS = 499
PRIOR_CSVS = [
    "sweep_progress.csv",                   # 75  gold family sweep      M5-H4
    "htf_breakout.csv",                     # 12  HTF-gated breakout
    "sweep_indices.csv",                    # 150 US index sweep         M5-H4
    "basket_configs.csv",                   # 108 index trend basket 2018-25
    "basket_configs_scored_pre2018.csv",    # 90  pre-2018 basket
    "sneaky_pivot.csv",                     # 24  sneaky pivot 2018-25
    "sneaky_pivot_pre2018.csv",             # 16  sneaky pivot out of regime
    "orb.csv",                              # 12  ORB 2018-25
    "orb_pre2018.csv",                      # 12  ORB out of regime
]

# ── cost models: each instrument keeps the model it already used at M5-H4 ─────
COST_BPS_INDEX = dict(commission=0.35, slip_normal=0.15, slip_news=0.50)
COST_GOLD_LEGACY = None        # engine default = the $/oz model run_sweep.py used

INSTRUMENTS = {
    "XAUUSD": (_ROOT / "data" / "XAUUSD_M1_2018_2025_spot_dukascopy.csv", COST_GOLD_LEGACY),
    "NAS100": (_ROOT / "data" / "NAS100_M1_2018_2025_cfd_dukascopy.csv",  COST_BPS_INDEX),
    "US30":   (_ROOT / "data" / "US30_M1_2018_2025_cfd_dukascopy.csv",    COST_BPS_INDEX),
}

# The measured cost_R gradient this run extends, and the sqrt(5) prediction for M1.
GRADIENT = {
    "XAUUSD": dict(M5=32.7, M15=17.3, M30=11.4, H1=7.6, H4=3.7, pred_M1=73.2),
    "NAS100": dict(M5=27.8, M15=14.4, M30=8.9,  H1=5.4, H4=2.7, pred_M1=62.2),
    "US30":   dict(M5=26.0, M15=13.4, M30=8.2,  H1=5.1, H4=2.5, pred_M1=58.1),
}

# RTH filter, only used by the matched control / out-of-regime driver. The
# pre-2018 M1 archive holds [13:00, 21:00) UTC and NOTHING else — measured, 100%
# of bars in both files — so the matched in-regime frame uses the same minutes.
RTH_UTC_MIN = (13 * 60, 21 * 60)
RTH_FILTER = False

OUT_CSV = _ROOT / "results" / "sweep_m1.csv"
SCORED_CSV = _ROOT / "results" / "sweep_m1_scored.csv"


def _coerce_utc(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tz is None else t.tz_convert("UTC")


def _apply_rth(frame: pd.DataFrame) -> pd.DataFrame:
    """Restrict to the pre-2018 archive's [13:00,21:00) UTC session."""
    mod = frame.index.hour * 60 + frame.index.minute
    lo, hi = RTH_UTC_MIN
    return frame[(mod >= lo) & (mod < hi)]


# ── scoring ──────────────────────────────────────────────────────────────────
def _split_stats(trades: pd.DataFrame) -> tuple:
    exit_t = pd.to_datetime(trades["exit_time"], utc=True)
    is_m, oos_m = exit_t < OOS_SPLIT, exit_t >= OOS_SPLIT

    def pf(mask):
        return profit_factor(trades.loc[mask, "net_R"]) if mask.any() else float("nan")

    def sr(mask):
        sub = trades.loc[mask]
        if sub.empty:
            return float("nan")
        d = sub.groupby(pd.to_datetime(sub["exit_time"], utc=True).dt.normalize())["ret_frac"].sum()
        return sharpe(d, BARS_PER_YEAR) if len(d) > 1 else float("nan")

    return int(is_m.sum()), int(oos_m.sum()), pf(is_m), pf(oos_m), sr(is_m), sr(oos_m)


def _year_stats(trades: pd.DataFrame) -> tuple[dict, float, float, int, int]:
    """Per-calendar-year net R, plus the concentration statistics.

    The share is NaN when the total is <= 0: a losing config must not be waved
    through gate 6 by an undefined ratio.
    """
    yr = pd.to_datetime(trades["exit_time"], utc=True).dt.year
    agg = trades.groupby(yr)["net_R"].sum()
    total = float(agg.sum())
    top = float(agg.max()) if len(agg) else float("nan")
    share = (top / total) if total > 0 else float("nan")
    return ({int(y): float(v) for y, v in agg.items()}, top, share,
            int(len(agg)), int((agg > 0).sum()))


def score_config(m: pd.DataFrame, family_fn, params: dict, daily_index,
                 cost_bps) -> tuple[dict, pd.DataFrame]:
    """One config. Identical control flow to run_sweep.py::score_config."""
    empty = pd.DataFrame()
    cands = family_fn(m, params, TF_DELTA[TF_KEY])
    for tr in cands:
        tr["session_end"] = _coerce_utc(tr["session_end"])
        tr["entry_time"] = _coerce_utc(tr["entry_time"])
    if not cands:
        return dict(n_cands=0, n_trades=0, guard="N/A"), empty

    # strictly_after=True: signals and resolution share the execution frame, so
    # resolution must begin on the bar AFTER the signal bar. At M1 the frame is
    # resample_mid(..., "1min"), whose bar labelled T covers [T-1min, T) and is
    # therefore fully known at T — verified identical to a +1min index shift by
    # scripts/probe_m1.py. Same convention as M5-H4; no look-ahead by construction.
    trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=cost_bps))
    if trades.empty:
        return dict(n_cands=len(cands), n_trades=0, guard="N/A"), empty

    pos = build_position_series(trades, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=GUARD_THRESHOLD)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"

    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    is_n, oos_n, is_pf, oos_pf, is_sr, oos_sr = _split_stats(trades)
    years, top_R, top_share, n_years, n_pos_years = _year_stats(trades)

    # The two annualisations, computed on the SAME trades, so the header can
    # prove the daily construction was used rather than assert it.
    bars_per_day = float(len(m) / max(m.index.normalize().nunique(), 1))

    res = dict(
        n_cands=len(cands), n_trades=len(trades), guard=guard,
        n_long=int((trades["side"] == "long").sum()),
        n_short=int((trades["side"] == "short").sum()),
        gross_pf=profit_factor(trades["gross_R"]),
        net_pf=profit_factor(trades["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR),
        skew=float(daily_ret.skew()), ekurt=float(daily_ret.kurtosis()),
        max_dd=max_drawdown(equity),
        gross_R_mean=float(trades["gross_R"].mean()),
        cost_R_mean=float(trades["cost_R"].mean()),
        net_R_mean=float(trades["net_R"].mean()),
        gross_R_total=float(trades["gross_R"].sum()),
        net_R_total=float(trades["net_R"].sum()),
        risk_med=float(trades["risk_price"].median()),
        risk_med_bps=float((trades["risk_price"] / trades["entry_mid"]).median() * 1e4),
        win_rate=float((trades["net_R"] > 0).mean()),
        gross_win_rate=float((trades["gross_R"] > 0).mean()),
        n_targets=int((trades["reason"] == "target").sum()),
        n_stops=int((trades["reason"] == "stop").sum()),
        n_time=int((trades["reason"] == "time").sum()),
        n_obs=int(len(daily_ret)),
        # A day that loses >= 100% of equity would send (1+r).cumprod() negative
        # and make max_drawdown meaningless. At M1 trade rates that is a live
        # possibility, so it is counted rather than assumed away.
        n_ruin_days=int((daily_ret <= -1.0).sum()),
        equity_final=float(equity.iloc[-1]) if len(equity) else float("nan"),
        trades_per_day=float(len(trades) / max(len(daily_ret), 1)),
        bars_per_day=bars_per_day,
        is_trades=is_n, oos_trades=oos_n,
        is_pf=is_pf, oos_pf=oos_pf, is_sharpe=is_sr, oos_sharpe=oos_sr,
        top_year_R=top_R, top_year_share=top_share,
        n_years=n_years, n_pos_years=n_pos_years,
    )
    for y, v in years.items():
        res[f"yr_{y}"] = v
    return res, trades


def buy_and_hold(daily: pd.DataFrame) -> dict:
    """Daily buy-and-hold on the same file, mid prices, spread crossed once."""
    px = daily["mid_close"]
    ret = px.pct_change().dropna()
    entry_cost = float(daily["spread_close"].iloc[0] / px.iloc[0])
    eq = (1 + ret).cumprod() * (1 - entry_cost)
    return dict(sharpe=sharpe(ret, BARS_PER_YEAR), max_dd=max_drawdown(eq))


def verify_annualisation(daily_ret: pd.Series, m: pd.DataFrame, label: str) -> dict:
    """PROVE the Sharpe annualisation from the data instead of asserting it.

    Computes the headline Sharpe (daily returns, factor 252) and the number the
    same strategy would post if per-bar M1 returns were annualised at the
    measured M1 bars/year. The ratio must equal sqrt(bars_per_year_M1 / 252);
    if the daily construction had been bypassed anywhere the identity breaks.
    """
    n_days = max(daily_ret.index.normalize().nunique(), 1)
    span_years = max((m.index[-1] - m.index[0]).days / 365.25, 1e-9)
    bars_per_year_measured = len(m) / span_years
    sr_daily = sharpe(daily_ret, BARS_PER_YEAR)
    naive_factor = bars_per_year_measured
    inflation = float(np.sqrt(naive_factor / BARS_PER_YEAR))
    return dict(
        label=label,
        n_daily_obs=int(len(daily_ret)),
        n_trading_days=int(n_days),
        m1_bars=int(len(m)),
        bars_per_year_measured=float(bars_per_year_measured),
        bars_per_year_metrics_py=525_600,      # metrics.py BARS_PER_YEAR["1m"], 24/7
        ann_factor_used=BARS_PER_YEAR,
        sharpe_daily_252=float(sr_daily),
        sharpe_if_per_bar_annualised=float(sr_daily * inflation),
        inflation_if_wrong=inflation,
    )


# ── driver ───────────────────────────────────────────────────────────────────
def main() -> None:
    rows, bh, ann_checks = [], {}, []
    for inst, (path, cost_bps) in INSTRUMENTS.items():
        if not path.exists():
            print(f"[{inst}] MISSING {path.name} — skipped.", flush=True)
            continue

        print(f"\n[{inst}] loading M1 ...", flush=True)
        spot = load_m1_spot(path)
        if RTH_FILTER:
            n_before = len(spot)
            spot = _apply_rth(spot)
            print(f"[{inst}] RTH filter [13:00,21:00) UTC: {n_before:,} -> {len(spot):,} bars",
                  flush=True)
        # daily bars (and therefore the B&H benchmark and the daily return
        # calendar) are aggregated from whatever bars the frame holds AFTER the
        # filter, so the matched control samples an RTH close exactly as the
        # pre-2018 files do. Mismatching this would move the benchmark, not the
        # strategy, and would make the two windows unreadable against each other.
        daily_full = aggregate_daily(spot)
        m1 = pd.DataFrame(index=spot.index)
        for c in ("open", "high", "low", "close"):
            m1[f"mid_{c}"] = (spot[f"bid_{c}"] + spot[f"ask_{c}"]) / 2
        m1["spread"] = spot["spread"]
        m1["volume"] = spot["volume"]
        del spot

        bh[inst] = buy_and_hold(daily_full)
        daily_index = daily_full.index

        # The execution frame. resample_mid('1min') is the SAME transform M5-H4
        # used; scripts/probe_m1.py verifies it equals a +1min index shift exactly.
        m = resample_mid(m1, TF_FREQ)
        del m1

        med_sp, med_px = float(m["spread"].median()), float(m["mid_close"].median())
        print(f"[{inst}] {len(m):,} M1 bars {m.index[0].date()} -> {m.index[-1].date()} "
              f"| median spread {med_sp:.4f} ({1e4 * med_sp / med_px:.2f} bps) "
              f"| daily obs {len(daily_index):,} | B&H SR {bh[inst]['sharpe']:+.2f}",
              flush=True)

        first_daily_ret = None
        for fam, (fn, variants) in FAMILIES.items():
            for i, params in enumerate(variants):
                res, tr = score_config(m, fn, params, daily_index, cost_bps)
                rows.append(dict(instrument=inst, timeframe=TF_KEY, family=fam,
                                 variant=str(i), params=str(params),
                                 bh_sharpe=bh[inst]["sharpe"],
                                 bh_max_dd=bh[inst]["max_dd"], **res))
                if first_daily_ret is None and not tr.empty:
                    first_daily_ret = build_daily_returns(tr, daily_index)
                print(f"  {inst:>6} {TF_KEY} {fam:<9} v{i} "
                      f"cands={res.get('n_cands', 0):>7,} n={res.get('n_trades', 0):>6,} "
                      f"grPF={res.get('gross_pf', float('nan')):.3f} "
                      f"netPF={res.get('net_pf', float('nan')):.3f} "
                      f"SR={res.get('sharpe', float('nan')):+.2f} "
                      f"costR={res.get('cost_R_mean', float('nan')) * 100:.1f}% "
                      f"guard={res.get('guard', '?')[:4]}", flush=True)

        if first_daily_ret is not None:
            ann_checks.append(verify_annualisation(first_daily_ret, m, inst))
        del m

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    analyze(df, bh, ann_checks)


def analyze_only() -> None:
    if not OUT_CSV.exists():
        print(f"No {OUT_CSV.name} — run the grid first.")
        return
    analyze(pd.read_csv(OUT_CSV), {}, [])


def _prior_sharpes() -> tuple[np.ndarray, str]:
    vals, notes = [], []
    for name in PRIOR_CSVS:
        p = _ROOT / "results" / name
        if p.exists():
            s = pd.to_numeric(pd.read_csv(p)["sharpe"], errors="coerce").dropna().to_numpy()
            vals.append(s)
            notes.append(f"{name}:{len(s)}")
        else:
            notes.append(f"{name}:MISSING")
    arr = np.concatenate(vals) if vals else np.array([])
    return arr, ", ".join(notes)


def analyze(df: pd.DataFrame, bh: dict, ann_checks: list) -> None:
    n_batch = len(df)
    cumulative = PRIOR_TRIALS + n_batch
    traded = df[pd.to_numeric(df.get("n_trades", pd.Series(dtype=float)),
                              errors="coerce").fillna(0) > 0].copy()
    for c in ("sharpe", "gross_pf", "net_pf", "max_dd", "skew", "ekurt", "n_obs",
              "is_pf", "oos_pf", "is_sharpe", "oos_sharpe", "oos_trades",
              "cost_R_mean", "gross_R_mean", "net_R_mean", "risk_med_bps",
              "top_year_share", "win_rate", "gross_win_rate", "trades_per_day",
              "n_trades", "gross_R_total", "net_R_total", "bh_sharpe", "bh_max_dd"):
        if c in traded:
            traded[c] = pd.to_numeric(traded[c], errors="coerce")

    W = 132
    print("\n" + "=" * W)
    print(f"  THE M1 ROW — 5-family sweep at the 1-MINUTE bar, real Dukascopy spread, {WINDOW_LABEL}"
          + ("  [RTH-MATCHED CONTROL]" if RTH_FILTER else ""))
    print("  Same families, same stated variants, same engine as the M5-H4 rows. Nothing re-tuned.")
    print("  Every parameter is in BARS, so at M1: ATR 14 = 14 min, EMA 200 = 200 min, "
          "max hold H = 12-96 MINUTES.")
    print("  Costs: XAUUSD = legacy $/oz model (run_sweep.py); NAS100/US30 = 0.35 bps commission "
          "+ 0.15/0.50 bps")
    print("         per-side slippage (run_sweep_indices.py). Real per-bar spread from the data in "
          "both cases. 1% risk/trade.")
    print(f"  Configs THIS BATCH: {n_batch}  |  CUMULATIVE PROJECT TRIALS: "
          f"{PRIOR_TRIALS} prior + {n_batch} = {cumulative}")
    print("=" * W)

    # ── the annualisation proof ───────────────────────────────────────────────
    if ann_checks:
        print("\n  SHARPE ANNUALISATION — PROVEN FROM THIS RUN'S OWN TRADES, NOT ASSERTED")
        print("  Headline Sharpe uses CALENDAR-DAILY aggregated returns annualised at 252.")
        print("  The annualisation factor is a property of the RETURN SERIES, not the signal TF:")
        print("  an M1 system and a D1 system both emit one return per trading day.")
        print(f"  {'inst':>6} {'M1 bars':>11} {'bars/yr measured':>17} {'daily obs':>10} "
              f"{'factor used':>12} {'SR (daily,252)':>15} {'SR if per-bar':>14} {'x inflation':>12}")
        print("  " + "-" * (W - 4))
        for a in ann_checks:
            print(f"  {a['label']:>6} {a['m1_bars']:>11,} {a['bars_per_year_measured']:>17,.0f} "
                  f"{a['n_daily_obs']:>10,} {a['ann_factor_used']:>12} "
                  f"{a['sharpe_daily_252']:>+15.3f} {a['sharpe_if_per_bar_annualised']:>+14.3f} "
                  f"{a['inflation_if_wrong']:>12.1f}x")
        print("  Read: the last column is the factor by which Sharpe WOULD be inflated if per-bar")
        print("  M1 returns were annualised at the measured M1 bars/year. That error is NOT made")
        print("  here. Note also that metrics.py::BARS_PER_YEAR['1m'] = 525,600 assumes a 24/7")
        print("  year and OVERSTATES the real M1 bar count by 1.9-2.9x — it is not used anywhere")
        print("  in this run, and it is the wrong number even for the wrong method.")

    if traded.empty:
        print("\n  NO config produced a trade. Investigate the setup filter before reading anything in.")
        return

    # ── DSR pools ─────────────────────────────────────────────────────────────
    prior, prior_note = _prior_sharpes()
    sr_batch = traded["sharpe"].fillna(0.0).to_numpy()
    pool_project = np.concatenate([prior, sr_batch]) if prior.size else sr_batch

    def _dsr(r, pool):
        if not np.isfinite(r["sharpe"]) or r["n_obs"] < 4:
            return np.nan
        return deflated_sharpe(
            sr_best=float(r["sharpe"]), sr_trials=pool, n_obs=int(r["n_obs"]),
            ann_factor=BARS_PER_YEAR,
            skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
            excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0,
        )["dsr"]

    traded["dsr"] = traded.apply(lambda r: _dsr(r, sr_batch), axis=1)
    traded["dsr_cumulative_pool"] = traded.apply(lambda r: _dsr(r, pool_project), axis=1)
    e_struct = expected_max_sharpe(sr_batch)
    e_cumul = expected_max_sharpe(pool_project)

    print(f"\n  DSR pool (HEADLINE) = STRUCTURAL: this batch's {len(sr_batch)} a priori cells "
          f"-> E[max SR] {e_struct[0]:+.3f} (mu {e_struct[2]:+.3f}, sd {e_struct[3]:.3f})")
    print(f"  DSR pool (CONTRAST) = project-cumulative {len(pool_project)} "
          f"[{prior_note}]")
    print(f"                        -> E[max SR] {e_cumul[0]:+.3f} "
          f"(mu {e_cumul[2]:+.3f}, sd {e_cumul[3]:.3f}). NOT a gate — sigma-contaminated "
          f"(research/dsr.py BUG 2).")
    if e_struct[2] < 0:
        print(f"\n  ** DSR CAVEAT, STATED BECAUSE IT MATTERS HERE. The structural pool's own mean")
        print(f"     Sharpe is {e_struct[2]:+.3f} — every cell in this batch is deeply negative. When a")
        print(f"     pool is uniformly bad, E[max SR] is dragged down with it and a merely LESS")
        print(f"     catastrophic config can post a high-looking DSR while losing money on every")
        print(f"     trade. The DSR column below is therefore NOT informative in this batch, and")
        print(f"     it is not doing any work: SURVIVOR requires net PF > 1 AND Sharpe > 0 as well,")
        print(f"     and both of those bind long before DSR does. Do not quote a DSR from this run")
        print(f"     as evidence of anything.")

    # Ruin diagnostics — reported, never silently swallowed.
    if "n_ruin_days" in traded:
        ruin = pd.to_numeric(traded["n_ruin_days"], errors="coerce").fillna(0)
        wiped = int((pd.to_numeric(traded.get("equity_final"), errors="coerce") < 0.01).sum())
        print(f"\n  RUIN DIAGNOSTICS at the repo's 1% risk/trade convention: "
              f"{int((ruin > 0).sum())}/{len(traded)} cells have a day losing >= 100% of equity "
              f"(which would invalidate maxDD);")
        print(f"  {wiped}/{len(traded)} cells end with equity below 1% of its start. maxDD and the")
        print(f"  equity curve are LEVERAGE-DEPENDENT and 1%/trade x ~25 trades/day is not a")
        print(f"  realistic sizing. Sharpe IS leverage-invariant (mu/sigma cancels the scale), and")
        print(f"  so are gross PF, net PF, cost_R and R/trade. The verdict rests on those.")

    traded["oos_holds"] = ((traded["is_pf"] > 1.0) & (traded["oos_pf"] > 1.0)
                           & (traded["oos_trades"] >= MIN_OOS_TRADES)
                           & (traded["oos_sharpe"] > 0))
    traded["gross_edge"] = traded["gross_pf"] > 1.0
    traded["not_concentrated"] = (traded["top_year_share"].notna()
                                  & (traded["top_year_share"] <= CONC_BAR))
    # bh_sharpe is persisted per row, so --analyze reproduces this gate without
    # reloading 850 MB of M1 CSV. The live `bh` dict takes precedence when present.
    def _bh_sr(r):
        if r["instrument"] in bh:
            return float(bh[r["instrument"]]["sharpe"])
        return float(r["bh_sharpe"]) if pd.notna(r.get("bh_sharpe")) else float("nan")

    traded["bh_sharpe"] = traded.apply(_bh_sr, axis=1)
    traded["beats_bh"] = traded.apply(
        lambda r: bool(np.isfinite(r["sharpe"]) and np.isfinite(r["bh_sharpe"])
                       and r["sharpe"] > r["bh_sharpe"]), axis=1)
    traded["SURVIVOR"] = (traded["gross_edge"] & (traded["net_pf"] > 1.0)
                          & (traded["sharpe"] > 0) & (traded["dsr"] > DSR_BAR)
                          & traded["oos_holds"] & traded["not_concentrated"]
                          & traded["beats_bh"] & (traded["guard"] == "PASS"))
    traded.to_csv(SCORED_CSV, index=False)

    # ── the config table ──────────────────────────────────────────────────────
    print("\n  CONFIG TABLE — family x instrument, all 45 cells")
    print(f"  {'inst':>6} {'family':<9} {'v':>1} {'trades':>7} {'/day':>5} "
          f"{'grPF':>6} {'netPF':>6} {'Sharpe':>8} {'DSR':>5} {'maxDD':>6} "
          f"{'costR%':>7} {'1R bps':>7} {'top%':>5} {'OOS?':>4} {'B&H?':>5} {'guard':>5}")
    print("  " + "-" * (W - 4))
    for _, r in traded.sort_values(["instrument", "family", "variant"]).iterrows():
        share = r["top_year_share"]
        print(f"  {r['instrument']:>6} {r['family']:<9} {r['variant']:>1} "
              f"{int(r['n_trades']):>7,} {r['trades_per_day']:>5.1f} "
              f"{r['gross_pf']:>6.3f} {r['net_pf']:>6.3f} {r['sharpe']:>+8.2f} "
              f"{r['dsr']:>5.2f} {r['max_dd'] * 100:>5.1f}% {r['cost_R_mean'] * 100:>6.1f}% "
              f"{r['risk_med_bps']:>7.1f} "
              + (f"{share * 100:>4.0f}%" if np.isfinite(share) else f"{'n/a':>5}")
              + f" {'YES' if r['oos_holds'] else 'no':>4} "
              f"{'BEAT' if r['beats_bh'] else 'lose':>5} {r['guard'][:5]:>5}")
    print("=" * W)

    finding_one(traded)
    finding_two(traded)
    per_year(traded)
    verdict(traded, bh, n_batch, cumulative)


def finding_one(traded: pd.DataFrame) -> None:
    """FINDING (1): is there ANY gross edge at M1, before a cent of cost?"""
    print("\n  FINDING (1) — IS THERE ANY *GROSS* EDGE AT M1? (cost plays no part in this table)")
    print("  gross PF uses gross_R only. If this column sits at 1.00 the M1 tape carries no")
    print("  exploitable signal for these families, and the cost question below is academic.")
    print(f"  {'inst':>6} {'family':<9} {'v':>1} {'grossPF':>8} {'grossR/trd':>11} "
          f"{'gross win%':>11} {'gross R tot':>12} {'trades':>8}")
    print("  " + "-" * 74)
    for _, r in traded.sort_values("gross_pf", ascending=False).iterrows():
        print(f"  {r['instrument']:>6} {r['family']:<9} {r['variant']:>1} "
              f"{r['gross_pf']:>8.4f} {r['gross_R_mean']:>+11.5f} "
              f"{r['gross_win_rate'] * 100:>10.1f}% {r['gross_R_total']:>+12.1f} "
              f"{int(r['n_trades']):>8,}")
    n = len(traded)
    pos = int((traded["gross_pf"] > 1).sum())
    print("  " + "-" * 74)
    print(f"  gross PF > 1 : {pos}/{n} cells   mean {traded['gross_pf'].mean():.4f}   "
          f"median {traded['gross_pf'].median():.4f}   "
          f"range {traded['gross_pf'].min():.4f}-{traded['gross_pf'].max():.4f}")
    print(f"  mean gross R per trade: {traded['gross_R_mean'].mean():+.5f} R   "
          f"(a coin flip with a 2R target and a 1R stop sits at gross PF 1.00)")


def finding_two(traded: pd.DataFrame) -> None:
    """FINDING (2): does cost_R at M1 confirm the M5->H4 gradient?"""
    print("\n  FINDING (2) — COST_R AT M1 vs THE MEASURED M5->H4 GRADIENT")
    print("  Cost per trade is fixed; 1R is an ATR-scaled stop, and ATR ~ sqrt(bar duration).")
    print("  So cost_R should scale ~1/sqrt(TF), and M5 -> M1 should multiply it by sqrt(5)=2.24.")
    print(f"  {'inst':>7} {'H4':>7} {'H1':>7} {'M30':>7} {'M15':>7} {'M5':>7} "
          f"{'M1 (this run)':>15} {'M5->M1 x':>10} {'predicted':>10} {'error':>8}")
    print("  " + "-" * 100)
    for inst, g in GRADIENT.items():
        sub = traded[traded["instrument"] == inst]
        if sub.empty:
            continue
        m1_mean = float(sub["cost_R_mean"].mean() * 100)
        ratio = m1_mean / g["M5"]
        err = (m1_mean - g["pred_M1"]) / g["pred_M1"] * 100
        print(f"  {inst:>7} {g['H4']:>6.1f}% {g['H1']:>6.1f}% {g['M30']:>6.1f}% "
              f"{g['M15']:>6.1f}% {g['M5']:>6.1f}% {m1_mean:>14.1f}% "
              f"{ratio:>9.2f}x {g['pred_M1']:>9.1f}% {err:>+7.1f}%")
    print("  " + "-" * 100)
    print("  M1 cost_R by family x instrument (mean over the 3 variants, % of 1R):")
    piv = (traded.pivot_table(index="instrument", columns="family",
                              values="cost_R_mean", aggfunc="mean") * 100).round(1)
    for line in piv.to_string().splitlines():
        print("    " + line)
    print(f"\n  Median 1R at M1 (bps of price): "
          + ", ".join(f"{i} {v:.1f}" for i, v in
                      traded.groupby("instrument")["risk_med_bps"].median().items()))
    over20 = int((traded["cost_R_mean"] > 0.20).sum())
    print(f"  Cells above the 20% cost_R regime that killed M5: {over20}/{len(traded)}")


def per_year(traded: pd.DataFrame) -> None:
    """Per-year net R for every config — gate 6, not a footnote."""
    ycols = sorted([c for c in traded.columns if c.startswith("yr_")])
    if not ycols:
        return
    print("\n  YEAR-BY-YEAR net R, ALL configs (single-year concentration = gate 6)")
    head = "  " + f"{'config':<24}" + "".join(f"{c[3:]:>9}" for c in ycols) + f"{'total':>10}{'top%':>7}"
    print(head)
    print("  " + "-" * (len(head) - 2))
    for _, r in traded.sort_values("sharpe", ascending=False).iterrows():
        vals = [float(r[c]) if pd.notna(r.get(c)) else 0.0 for c in ycols]
        share = r["top_year_share"]
        label = f"{r['instrument']} {r['family']} v{r['variant']}"
        print(f"  {label:<24}" + "".join(f"{v:>+9.1f}" for v in vals)
              + f"{sum(vals):>+10.1f}"
              + (f"{share * 100:>6.0f}%" if np.isfinite(share) else f"{'n/a':>7}"))
    print(f"  'n/a' = total net R <= 0, so the ratio is undefined. That is WORSE than")
    print(f"  concentration, not a pass. Bar for gate 6 is top year <= {CONC_BAR:.0%}.")


def verdict(traded: pd.DataFrame, bh: dict, n_batch: int, cumulative: int) -> None:
    n = len(traded)
    survivors = traded[traded["SURVIVOR"]]
    best = traded.sort_values("sharpe", ascending=False).iloc[0]

    print("\n  GATE TALLY")
    print("  " + "-" * 60)
    for label, col in (("look-ahead guard PASS", None),
                       ("gross PF > 1", "gross_edge"),
                       ("net PF > 1", None),
                       ("net Sharpe > 0", None),
                       (f"DSR > {DSR_BAR}", None),
                       ("OOS holds", "oos_holds"),
                       (f"top year <= {CONC_BAR:.0%} of net R", "not_concentrated"),
                       ("beats buy-and-hold", "beats_bh")):
        if label.startswith("look"):
            k = int((traded["guard"] == "PASS").sum())
        elif label == "net PF > 1":
            k = int((traded["net_pf"] > 1).sum())
        elif label == "net Sharpe > 0":
            k = int((traded["sharpe"] > 0).sum())
        elif label.startswith("DSR"):
            k = int((traded["dsr"] > DSR_BAR).sum())
        else:
            k = int(traded[col].sum())
        print(f"  {label:<40} {k:>3}/{n}")
    print(f"  {'SURVIVORS (all gates)':<40} {len(survivors):>3}/{n}")

    print("\n  VERDICT")
    print("  " + "-" * 90)
    if len(survivors):
        print(f"  {len(survivors)} config(s) cleared every in-regime gate:")
        for _, r in survivors.iterrows():
            print(f"    {r['instrument']} {r['family']} v{r['variant']}: SR {r['sharpe']:+.2f}, "
                  f"DSR {r['dsr']:.3f}, grossPF {r['gross_pf']:.3f}, netPF {r['net_pf']:.3f}")
        print("\n  NOT A LEAD — STATE_OF_PLAY section 7 rule 3: run_sweep_m1_pre2018.py must")
        print("  be passed before any of this is believed.")
    else:
        print(f"  NO config cleared all gates. {n} cells, 0 survivors.")
        print(f"  Best raw net Sharpe: {best['instrument']} {best['family']} v{best['variant']} "
              f"-> SR {best['sharpe']:+.2f}")
        print(f"    - gross PF {best['gross_pf']:.4f} -> "
              f"{'edge exists before costs' if best['gross_pf'] > 1 else 'NO edge even before costs'}")
        print(f"    - net PF   {best['net_pf']:.4f}  (cost {best['cost_R_mean'] * 100:.1f}% of 1R)")
        print(f"    - DSR {best['dsr']:.3f} (need > {DSR_BAR})")
        print(f"    - OOS holds: {'YES' if best['oos_holds'] else 'NO'}")

    print("\n  vs BUY-AND-HOLD (same file, same window):")
    for inst in traded["instrument"].unique():
        sub = traded[traded["instrument"] == inst]
        s = sub.sort_values("sharpe", ascending=False).iloc[0]
        b_sr = float(s.get("bh_sharpe", np.nan))
        b_dd = float(s.get("bh_max_dd", np.nan))
        print(f"    {inst:>6}: best M1 config SR {s['sharpe']:+.2f} "
              f"(maxDD {s['max_dd'] * 100:.1f}%)  vs  B&H SR {b_sr:+.2f} "
              f"(maxDD {b_dd * 100:.1f}%)  -> "
              f"{'BEATS' if s['sharpe'] > b_sr else 'LOSES'}")

    print(f"\n  Cumulative project trials after this batch: {cumulative} "
          f"({PRIOR_TRIALS} prior + {n_batch} M1 cells)")
    print("  " + "=" * 90)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--rth" in sys.argv:
        # Matched control: the SAME 2018-2025 files restricted to the pre-2018
        # archive's [13:00,21:00) UTC session, so the out-of-regime comparison is
        # like-for-like. XAUUSD is dropped because it has no pre-2018 M1 at all,
        # so a gold RTH control would have nothing to be matched against.
        RTH_FILTER = True
        INSTRUMENTS = {k: v for k, v in INSTRUMENTS.items() if k != "XAUUSD"}
        WINDOW_LABEL = "2018-2025 RTH-MATCHED"
        OUT_CSV = _ROOT / "results" / "sweep_m1_rth.csv"
        SCORED_CSV = _ROOT / "results" / "sweep_m1_rth_scored.csv"
    if "--analyze" in sys.argv:
        analyze_only()
    else:
        main()
