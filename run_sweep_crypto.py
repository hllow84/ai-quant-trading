#!/usr/bin/env python3
"""
run_sweep_crypto.py — the 5-family sweep on CRYPTO (BTC/USDT, ETH/USDT),
real Binance spot data, M15/H1/H4.

WHY THIS RUN EXISTS
--------------------
Every price-pattern kill in this project (sections 1-11) was tested on gold
and index CFDs only. This closes a real scope gap: does the same "no
price-pattern edge" conclusion extend to crypto, a structurally different
instrument class (24/7/365 trading, no session structure, fee-dominated
cost model instead of spread-dominated)?

WHY M15/H1/H4, NOT M1 — stated, as required
---------------------------------------------
M1 is deliberately excluded. STATE_OF_PLAY.md section 11 (the M1 row) found
a clean, structural, instrument-agnostic result: at the 1-minute bar, cost
per trade is fixed while 1R (an ATR-scaled stop) shrinks with the square
root of bar duration, so cost_R blows out to 27-89% of 1R and kills every
one of 45 configs regardless of instrument (gold, two different index
CFDs). That mechanism is about STOP DISTANCE vs FIXED COST, not about any
one instrument's tape — it applies with equal force to a fourth and fifth
instrument. Re-running M1 here would not test anything new; it would
re-confirm a conclusion already established structurally. H1 is the anchor
timeframe (matches the M5-H4 ladder's own mid-point); M15 and H4 bracket it,
giving the same 3-timeframe span the M1-row study itself used across
instruments.

GRID (stated, small, a priori, NOT tuned)
------------------------------------------
    2 instruments (BTCUSDT, ETHUSDT)
  x 3 timeframes  (M15, H1, H4 — scripts/download_crypto_ohlcv.py, native
                    Binance candles, NOT resampled from an M1 archive)
  x 5 families    (trend, breakout, meanrev, momentum, macross)
  x 3 stated variants each
  = 90 configs THIS BATCH.

Families, variants, every numeric parameter imported UNCHANGED from
strategies/sweep_families.py. Nothing is re-tuned for crypto.

COSTS — real, and structurally different from every prior instrument in
this project, stated plainly rather than silently reused
-------------------------------------------------------------------------
Binance spot TAKER fee (no BNB/VIP discount, the conservative default a
retail account actually pays) is 10 bps PER SIDE = 20 bps round-turn. That
dominates crypto cost by 150-15,000x over the spread (BTCUSDT top-of-book
spread measured live at ~0.0013 bps, ETHUSDT ~0.041 bps —
scripts/download_crypto_ohlcv.py). This is the OPPOSITE cost structure from
every FX/index/ETF instrument in this project, where spread dominates and
commission is near-zero. Slippage: 1bps/side normal, 2bps/side during the
repo's existing NEWS_HOURS_UTC windows (reused unchanged as a conservative,
not crypto-specific, proxy for elevated-volatility periods — crypto has no
scheduled "news" session the way FX does, so this widens cost in the same
windows out of caution, not because it is the mechanistically correct
crypto analogue).

OUT-OF-REGIME — stated honestly: crypto cannot get the SAME treatment as
FX/indices did
-----------------------------------------------------------------------------
STATE_OF_PLAY section 7 rule 3 calls for a genuine pre-sample holdout. For
FX/indices that meant a truly separate multi-year archive (2013-2017,
sections 9.3/11). Binance BTC/USDT and ETH/USDT spot markets both begin
2017-08-17 (verified) — four months before this project's standard 2018
baseline. There is no clean multi-year pre-2018 crypto window to hold out;
pulling one would mean re-running on 4 months of the exchange's earliest,
thinnest trading, which is not a meaningful regime test. So this run does
NOT claim a genuine out-of-regime test for crypto. Instead, as the task
explicitly allows ("out-of-regime split, as far back as clean data
allows"), the single 2018-2025 window is split into two REGIMES within
itself — 2018-2021 (2018-19 bear, 2020-21 mania) vs 2022-2025 (2022 bear,
2023-25 recovery) — computed by RE-SLICING THE SAME SIMULATED TRADES, not a
new simulation grid. This is therefore NOT counted as new trials (same
treatment STATE_OF_PLAY section 11 gave the RTH-matched control), and it is
explicitly weaker evidence than a true holdout: both halves come from the
same continuous data pull, sharing method, universe and exchange.

GATES: identical to every prior sweep — look-ahead guard, gross PF > 1,
net PF > 1 AND net Sharpe > 0, DSR > 0.95 (structural pool = this batch's
own 90 a priori cells), OOS holds (2023-01-01 split), NOT single-year
concentrated (top year <= 60% of net R), beats buy-and-hold BTC/ETH.

Usage:  python run_sweep_crypto.py              (full run, 90 configs)
        python run_sweep_crypto.py --analyze    (re-score from CSV)
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.backtest import guard_look_ahead, LookAheadError
from research.metrics import sharpe, max_drawdown, profit_factor
from research.dsr import deflated_sharpe, expected_max_sharpe
from research.ftmo_engine import (
    simulate_trades, de_overlap, build_daily_returns, equity_from_returns,
    build_position_series,
)
from strategies.sweep_families import FAMILIES, TF_DELTA

TIMEFRAMES = ["M15", "H1", "H4"]
BARS_PER_YEAR = 252  # calendar-daily aggregated returns; same reasoning as sec 11
OOS_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
REGIME_SPLIT = pd.Timestamp("2022-01-01", tz="UTC")
WINDOW_LABEL = "2018-2025"
MIN_OOS_TRADES = 15
DSR_BAR = 0.95
CONC_BAR = 0.60
GUARD_THRESHOLD = 0.5

PRIOR_TRIALS = 638  # STATE_OF_PLAY.md current cumulative, stated by the task
PRIOR_CSVS = [
    "sweep_progress.csv", "htf_breakout.csv", "sweep_indices.csv",
    "basket_configs.csv", "basket_configs_scored_pre2018.csv",
    "sneaky_pivot.csv", "sneaky_pivot_pre2018.csv", "orb.csv", "orb_pre2018.csv",
    "sweep_m1_scored.csv", "sweep_m1_rth_scored.csv",
]

CRYPTO_COST_BPS = dict(commission=20.0, slip_normal=1.0, slip_news=2.0)

INSTRUMENTS = {
    "BTCUSDT": {tf: _ROOT / "data" / f"BTCUSDT_{tf}_2018_2025_binance.csv" for tf in TIMEFRAMES},
    "ETHUSDT": {tf: _ROOT / "data" / f"ETHUSDT_{tf}_2018_2025_binance.csv" for tf in TIMEFRAMES},
}

OUT_CSV = _ROOT / "results" / "sweep_crypto.csv"
SCORED_CSV = _ROOT / "results" / "sweep_crypto_scored.csv"


def load_bars(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime_utc"]).set_index("datetime_utc").sort_index()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    return df


def _coerce_utc(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tz is None else t.tz_convert("UTC")


def _split_stats(trades: pd.DataFrame, split: pd.Timestamp) -> tuple:
    exit_t = pd.to_datetime(trades["exit_time"], utc=True)
    is_m, oos_m = exit_t < split, exit_t >= split

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
    yr = pd.to_datetime(trades["exit_time"], utc=True).dt.year
    agg = trades.groupby(yr)["net_R"].sum()
    total = float(agg.sum())
    top = float(agg.max()) if len(agg) else float("nan")
    share = (top / total) if total > 0 else float("nan")
    return ({int(y): float(v) for y, v in agg.items()}, top, share,
            int(len(agg)), int((agg > 0).sum()))


def score_config(m: pd.DataFrame, family_fn, params: dict, daily_index, tf_key: str) -> tuple[dict, pd.DataFrame]:
    """One config. Identical control flow to run_sweep_m1.py::score_config."""
    empty = pd.DataFrame()
    cands = family_fn(m, params, TF_DELTA[tf_key])
    for tr in cands:
        tr["session_end"] = _coerce_utc(tr["session_end"])
        tr["entry_time"] = _coerce_utc(tr["entry_time"])
    if not cands:
        return dict(n_cands=0, n_trades=0, guard="N/A"), empty

    trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=CRYPTO_COST_BPS))
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
    is_n, oos_n, is_pf, oos_pf, is_sr, oos_sr = _split_stats(trades, OOS_SPLIT)
    r18_n, r22_n, r18_pf, r22_pf, r18_sr, r22_sr = _split_stats(trades, REGIME_SPLIT)
    years, top_R, top_share, n_years, n_pos_years = _year_stats(trades)

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
        n_ruin_days=int((daily_ret <= -1.0).sum()),
        equity_final=float(equity.iloc[-1]) if len(equity) else float("nan"),
        trades_per_day=float(len(trades) / max(len(daily_ret), 1)),
        is_trades=is_n, oos_trades=oos_n, is_pf=is_pf, oos_pf=oos_pf, is_sharpe=is_sr, oos_sharpe=oos_sr,
        regimeA_trades=r18_n, regimeB_trades=r22_n, regimeA_pf=r18_pf, regimeB_pf=r22_pf,
        regimeA_sharpe=r18_sr, regimeB_sharpe=r22_sr,
        top_year_R=top_R, top_year_share=top_share, n_years=n_years, n_pos_years=n_pos_years,
    )
    for y, v in years.items():
        res[f"yr_{y}"] = v
    return res, trades


def buy_and_hold(m: pd.DataFrame, daily_index) -> dict:
    """Daily buy-and-hold from the loaded bars, closing-price-crossed spread once."""
    daily_close = m["mid_close"].resample("1D").last().reindex(daily_index).ffill()
    ret = daily_close.pct_change().dropna()
    entry_cost = float(m["spread"].iloc[0] / m["mid_close"].iloc[0])
    eq = (1 + ret).cumprod() * (1 - entry_cost)
    return dict(sharpe=sharpe(ret, BARS_PER_YEAR), max_dd=max_drawdown(eq))


def main() -> None:
    rows, bh = [], {}
    for inst, tf_paths in INSTRUMENTS.items():
        for tf_key, path in tf_paths.items():
            if not path.exists():
                print(f"[{inst} {tf_key}] MISSING {path.name} — skipped.", flush=True)
                continue
            print(f"\n[{inst} {tf_key}] loading ...", flush=True)
            m = load_bars(path)
            daily_index = pd.date_range(m.index[0].normalize(), m.index[-1].normalize(), freq="D", tz="UTC")

            bh_key = f"{inst}"
            if bh_key not in bh:
                bh[bh_key] = buy_and_hold(m, daily_index)

            med_sp, med_px = float(m["spread"].median()), float(m["mid_close"].median())
            print(f"[{inst} {tf_key}] {len(m):,} bars {m.index[0].date()} -> {m.index[-1].date()} "
                  f"| spread {1e4 * med_sp / med_px:.4f} bps | B&H SR {bh[bh_key]['sharpe']:+.2f}", flush=True)

            for fam, (fn, variants) in FAMILIES.items():
                for i, params in enumerate(variants):
                    res, tr = score_config(m, fn, params, daily_index, tf_key)
                    rows.append(dict(instrument=inst, timeframe=tf_key, family=fam, variant=str(i),
                                     params=str(params), bh_sharpe=bh[bh_key]["sharpe"],
                                     bh_max_dd=bh[bh_key]["max_dd"], **res))
                    print(f"  {inst:>7} {tf_key:<3} {fam:<9} v{i} "
                          f"cands={res.get('n_cands', 0):>6,} n={res.get('n_trades', 0):>5,} "
                          f"grPF={res.get('gross_pf', float('nan')):.3f} "
                          f"netPF={res.get('net_pf', float('nan')):.3f} "
                          f"SR={res.get('sharpe', float('nan')):+.2f} "
                          f"costR={res.get('cost_R_mean', float('nan')) * 100:.1f}% "
                          f"guard={res.get('guard', '?')[:4]}", flush=True)
            del m

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    analyze(df, bh)


def analyze_only() -> None:
    if not OUT_CSV.exists():
        print(f"No {OUT_CSV.name} — run the grid first.")
        return
    analyze(pd.read_csv(OUT_CSV), {})


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


def analyze(df: pd.DataFrame, bh: dict) -> None:
    n_batch = len(df)
    cumulative = PRIOR_TRIALS + n_batch
    traded = df[pd.to_numeric(df.get("n_trades", pd.Series(dtype=float)), errors="coerce").fillna(0) > 0].copy()
    for c in ("sharpe", "gross_pf", "net_pf", "max_dd", "skew", "ekurt", "n_obs",
              "is_pf", "oos_pf", "is_sharpe", "oos_sharpe", "oos_trades",
              "regimeA_pf", "regimeB_pf", "regimeA_sharpe", "regimeB_sharpe",
              "cost_R_mean", "gross_R_mean", "net_R_mean", "risk_med_bps",
              "top_year_share", "win_rate", "gross_win_rate", "trades_per_day",
              "n_trades", "gross_R_total", "net_R_total", "bh_sharpe", "bh_max_dd"):
        if c in traded:
            traded[c] = pd.to_numeric(traded[c], errors="coerce")

    W = 138
    print("\n" + "=" * W)
    print(f"  CRYPTO — 5-family sweep, BTCUSDT/ETHUSDT, M15/H1/H4, real Binance spot, {WINDOW_LABEL}")
    print("  Same families, same stated variants, same engine as every prior sweep. Nothing re-tuned.")
    print("  Costs: 20bps taker-fee round-turn (real Binance default) + real live-measured spread "
          "(~0.001-0.04bps, negligible) + 1-2bps slippage.")
    print(f"  Configs THIS BATCH: {n_batch}  |  CUMULATIVE PROJECT TRIALS: "
          f"{PRIOR_TRIALS} prior + {n_batch} = {cumulative}")
    print("=" * W)

    if traded.empty:
        print("\n  NO config produced a trade. Investigate the setup filter before reading anything in.")
        return

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
    print(f"  DSR pool (CONTRAST) = project-cumulative {len(pool_project)} [{prior_note}]")
    print(f"                        -> E[max SR] {e_cumul[0]:+.3f} (mu {e_cumul[2]:+.3f}, "
          f"sd {e_cumul[3]:.3f}). NOT a gate — sigma-contaminated (research/dsr.py BUG 2).")

    traded["oos_holds"] = ((traded["is_pf"] > 1.0) & (traded["oos_pf"] > 1.0)
                           & (traded["oos_trades"] >= MIN_OOS_TRADES) & (traded["oos_sharpe"] > 0))
    traded["gross_edge"] = traded["gross_pf"] > 1.0
    traded["not_concentrated"] = (traded["top_year_share"].notna() & (traded["top_year_share"] <= CONC_BAR))
    traded["regime_holds"] = ((traded["regimeA_pf"] > 1.0) & (traded["regimeB_pf"] > 1.0)
                              & (traded["regimeA_sharpe"] > 0) & (traded["regimeB_sharpe"] > 0))

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

    print("\n  CONFIG TABLE — instrument x TF x family, all 90 cells")
    print(f"  {'inst':>7} {'TF':>3} {'family':<9} {'v':>1} {'trades':>7} {'grPF':>6} {'netPF':>6} "
          f"{'Sharpe':>8} {'DSR':>5} {'maxDD':>6} {'costR%':>7} {'1R bps':>7} {'top%':>5} "
          f"{'OOS?':>4} {'regime?':>7} {'B&H?':>5} {'guard':>5}")
    print("  " + "-" * (W - 4))
    for _, r in traded.sort_values(["instrument", "timeframe", "family", "variant"]).iterrows():
        share = r["top_year_share"]
        print(f"  {r['instrument']:>7} {r['timeframe']:>3} {r['family']:<9} {r['variant']:>1} "
              f"{int(r['n_trades']):>7,} {r['gross_pf']:>6.3f} {r['net_pf']:>6.3f} "
              f"{r['sharpe']:>+8.2f} {r['dsr']:>5.2f} {r['max_dd'] * 100:>5.1f}% "
              f"{r['cost_R_mean'] * 100:>6.1f}% {r['risk_med_bps']:>7.1f} "
              + (f"{share * 100:>4.0f}%" if np.isfinite(share) else f"{'n/a':>5}")
              + f" {'YES' if r['oos_holds'] else 'no':>4} "
              f"{'YES' if r['regime_holds'] else 'no':>7} "
              f"{'BEAT' if r['beats_bh'] else 'lose':>5} {r['guard'][:5]:>5}")
    print("=" * W)

    per_year(traded)
    verdict(traded, bh, n_batch, cumulative)


def per_year(traded: pd.DataFrame) -> None:
    ycols = sorted([c for c in traded.columns if c.startswith("yr_")])
    if not ycols:
        return
    print("\n  YEAR-BY-YEAR net R, ALL configs (single-year concentration = gate)")
    head = "  " + f"{'config':<26}" + "".join(f"{c[3:]:>9}" for c in ycols) + f"{'total':>10}{'top%':>7}"
    print(head)
    print("  " + "-" * (len(head) - 2))
    for _, r in traded.sort_values("sharpe", ascending=False).iterrows():
        vals = [float(r[c]) if pd.notna(r.get(c)) else 0.0 for c in ycols]
        share = r["top_year_share"]
        label = f"{r['instrument']} {r['timeframe']} {r['family']} v{r['variant']}"
        print(f"  {label:<26}" + "".join(f"{v:>+9.1f}" for v in vals) + f"{sum(vals):>+10.1f}"
              + (f"{share * 100:>6.0f}%" if np.isfinite(share) else f"{'n/a':>7}"))


def verdict(traded: pd.DataFrame, bh: dict, n_batch: int, cumulative: int) -> None:
    n = len(traded)
    survivors = traded[traded["SURVIVOR"]]
    best = traded.sort_values("sharpe", ascending=False).iloc[0]

    print("\n  GATE TALLY")
    print("  " + "-" * 60)
    for label, col in (("look-ahead guard PASS", None), ("gross PF > 1", "gross_edge"),
                       ("net PF > 1", None), ("net Sharpe > 0", None), (f"DSR > {DSR_BAR}", None),
                       ("OOS holds (2023-01-01 split)", "oos_holds"),
                       ("regime split holds (2018-21 vs 22-25, re-scoring not new trials)", "regime_holds"),
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
        print(f"  {label:<58} {k:>3}/{n}")
    print(f"  {'SURVIVORS (all gates, oos_holds required, regime_holds informational)':<58} {len(survivors):>3}/{n}")

    print("\n  VERDICT")
    print("  " + "-" * 90)
    if len(survivors):
        print(f"  {len(survivors)} config(s) cleared every in-regime gate:")
        for _, r in survivors.iterrows():
            print(f"    {r['instrument']} {r['timeframe']} {r['family']} v{r['variant']}: "
                  f"SR {r['sharpe']:+.2f}, DSR {r['dsr']:.3f}, grossPF {r['gross_pf']:.3f}, "
                  f"netPF {r['net_pf']:.3f}, regime split holds: {'YES' if r['regime_holds'] else 'no'}")
        print("\n  NOT YET A LEAD without a genuine held-out window — this run's own docstring states")
        print("  why a true pre-2018 crypto holdout does not exist. Treat the regime-split column as")
        print("  the closest available check, weaker than a true holdout, not equivalent to it.")
    else:
        print(f"  NO config cleared all gates. {n} cells, 0 survivors.")
        print(f"  Best raw net Sharpe: {best['instrument']} {best['timeframe']} {best['family']} "
              f"v{best['variant']} -> SR {best['sharpe']:+.2f}")
        print(f"    - gross PF {best['gross_pf']:.4f} -> "
              f"{'edge exists before costs' if best['gross_pf'] > 1 else 'NO edge even before costs'}")
        print(f"    - net PF   {best['net_pf']:.4f}  (cost {best['cost_R_mean'] * 100:.1f}% of 1R)")
        print(f"    - DSR {best['dsr']:.3f} (need > {DSR_BAR})")
        print(f"    - OOS holds: {'YES' if best['oos_holds'] else 'NO'}")

    print("\n  vs BUY-AND-HOLD (same instrument, same window):")
    for inst in traded["instrument"].unique():
        sub = traded[traded["instrument"] == inst]
        s = sub.sort_values("sharpe", ascending=False).iloc[0]
        b_sr = float(s.get("bh_sharpe", np.nan))
        b_dd = float(s.get("bh_max_dd", np.nan))
        print(f"    {inst:>7}: best config SR {s['sharpe']:+.2f} (maxDD {s['max_dd'] * 100:.1f}%)  "
              f"vs  B&H SR {b_sr:+.2f} (maxDD {b_dd * 100:.1f}%)  -> "
              f"{'BEATS' if s['sharpe'] > b_sr else 'LOSES'}")

    print(f"\n  Cumulative project trials after this batch: {cumulative} "
          f"({PRIOR_TRIALS} prior + {n_batch} crypto cells; the regime-split columns above are a "
          f"re-scoring of these SAME {n_batch} trades, not additional trials)")
    print("  " + "=" * 90)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--analyze" in sys.argv:
        analyze_only()
    else:
        main()
