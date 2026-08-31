#!/usr/bin/env python3
"""
run_sweep_stocks.py — the 5-family sweep on INDIVIDUAL US STOCKS, daily bars.

WHY THIS RUN EXISTS
--------------------
Every price-pattern kill in this project (sections 1-11) was tested on gold
and index CFDs only. This closes a real scope gap: does the same "no
price-pattern edge" conclusion extend to individual US equities, a
structurally different instrument class (idiosyncratic single-name risk,
earnings gaps, no 24h session, real corporate actions)?

GRID (stated, small, a priori, NOT tuned)
------------------------------------------
    6 stocks (AAPL, JPM, XOM, JNJ, WMT, CAT -- diverse sectors, large-cap,
              liquid; scripts/download_us_stocks.py)
  x 1 timeframe   (D1 -- yfinance daily; intraday history is too short for
                    a genuine multi-year test, see download script docstring)
  x 5 families    (trend, breakout, meanrev, momentum, macross)
  x 3 stated variants each
  = 90 configs THIS BATCH (in-regime, 2018-2025).

Families, variants, every numeric parameter imported UNCHANGED from
strategies/sweep_families.py -- the same objects every prior sweep used.
Nothing is re-tuned for daily bars or for equities. Every parameter is in
BARS, so at D1: ATR 14 = 14 trading days, EMA 200 = 200 trading days
(~10 months), max hold H = 12-96 TRADING DAYS (~2-19 weeks).

COSTS: 2bps stated round-turn spread (conservative for these 6 liquid
large-caps; download script) + a bps cost model matching the repo's index
convention (commission + per-side slippage, widened in the same
NEWS_HOURS_UTC windows as every other bps-model instrument -- a US-market
proxy for scheduled data/earnings-adjacent volatility, reused unchanged).

GATES: identical to every prior sweep -- look-ahead guard, gross PF > 1,
net PF > 1 AND net Sharpe > 0, DSR > 0.95 (structural pool = this batch's
own 90 a priori cells), OOS holds (2023-01-01 split), NOT single-year
concentrated (top year <= 60% of net R), beats buy-and-hold.

Out-of-regime (2010-2017) is run separately by run_sweep_stocks_pre2018.py,
per STATE_OF_PLAY section 7 rule 3 -- same pattern as run_sweep_m1_pre2018.py:
a rebind-only driver, no strategy/cost/scoring code of its own.

Usage:  python run_sweep_stocks.py              (full run, 90 configs)
        python run_sweep_stocks.py --analyze    (re-score from CSV)
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

TF_KEY = "D1"
BARS_PER_YEAR = 252
OOS_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
WINDOW_LABEL = "2018-2025"
WINDOW_START = pd.Timestamp("2018-01-01", tz="UTC")
WINDOW_END = None  # open-ended: whatever the file holds
MIN_OOS_TRADES = 10
DSR_BAR = 0.95
CONC_BAR = 0.60
GUARD_THRESHOLD = 0.5

# Cumulative project trial count before this batch (STATE_OF_PLAY.md, N=638;
# 638 crypto -> +90 = 728 after run_sweep_crypto.py; this stocks batch runs
# independently and states its own baseline explicitly).
PRIOR_TRIALS = 728
PRIOR_CSVS = [
    "sweep_progress.csv", "htf_breakout.csv", "sweep_indices.csv",
    "basket_configs.csv", "basket_configs_scored_pre2018.csv",
    "sneaky_pivot.csv", "sneaky_pivot_pre2018.csv", "orb.csv", "orb_pre2018.csv",
    "sweep_m1_scored.csv", "sweep_m1_rth_scored.csv",
    "sweep_crypto_scored.csv",
]

STOCK_COST_BPS = dict(commission=1.0, slip_normal=0.5, slip_news=1.5)

TICKERS = ["AAPL", "JPM", "XOM", "JNJ", "WMT", "CAT"]
INSTRUMENTS = {t: _ROOT / "data" / f"{t}_D1_2010_2025_yfinance.csv" for t in TICKERS}

OUT_CSV = _ROOT / "results" / "sweep_stocks.csv"
SCORED_CSV = _ROOT / "results" / "sweep_stocks_scored.csv"


def load_daily(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["datetime_utc"]).set_index("datetime_utc").sort_index()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    else:
        df.index = df.index.tz_convert("UTC")
    return df


def _coerce_utc(ts) -> pd.Timestamp:
    t = pd.Timestamp(ts)
    return t.tz_localize("UTC") if t.tz is None else t.tz_convert("UTC")


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
    yr = pd.to_datetime(trades["exit_time"], utc=True).dt.year
    agg = trades.groupby(yr)["net_R"].sum()
    total = float(agg.sum())
    top = float(agg.max()) if len(agg) else float("nan")
    share = (top / total) if total > 0 else float("nan")
    return ({int(y): float(v) for y, v in agg.items()}, top, share,
            int(len(agg)), int((agg > 0).sum()))


TF_DELTA_D1 = pd.Timedelta(days=1)


def score_config_real(m: pd.DataFrame, family_fn, params: dict, daily_index, cost_bps) -> tuple[dict, pd.DataFrame]:
    """One config. Identical control flow to run_sweep_m1.py::score_config."""
    empty = pd.DataFrame()
    cands = family_fn(m, params, TF_DELTA_D1)
    for tr in cands:
        tr["session_end"] = _coerce_utc(tr["session_end"])
        tr["entry_time"] = _coerce_utc(tr["entry_time"])
    if not cands:
        return dict(n_cands=0, n_trades=0, guard="N/A"), empty

    # strictly_after=True: D1 signal + D1 resolution, same execution frame ->
    # resolution must start the bar AFTER the signal bar (repo convention,
    # identical to every other row in the M5-D1 ladder).
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
        is_trades=is_n, oos_trades=oos_n,
        is_pf=is_pf, oos_pf=oos_pf, is_sharpe=is_sr, oos_sharpe=oos_sr,
        top_year_R=top_R, top_year_share=top_share,
        n_years=n_years, n_pos_years=n_pos_years,
    )
    for y, v in years.items():
        res[f"yr_{y}"] = v
    return res, trades


def buy_and_hold(daily: pd.DataFrame) -> dict:
    px = daily["mid_close"]
    ret = px.pct_change().dropna()
    entry_cost = float(daily["spread"].iloc[0] / px.iloc[0])
    eq = (1 + ret).cumprod() * (1 - entry_cost)
    return dict(sharpe=sharpe(ret, BARS_PER_YEAR), max_dd=max_drawdown(eq))


def main() -> None:
    rows, bh = [], {}
    for tick, path in INSTRUMENTS.items():
        if not path.exists():
            print(f"[{tick}] MISSING {path.name} — skipped.", flush=True)
            continue
        print(f"\n[{tick}] loading D1 ...", flush=True)
        full = load_daily(path)
        mask = full.index >= WINDOW_START
        if WINDOW_END is not None:
            mask &= full.index <= WINDOW_END
        m = full[mask].copy()
        if m.empty:
            print(f"[{tick}] no data in window — skipped.", flush=True)
            continue
        daily_index = m.index

        bh[tick] = buy_and_hold(m)
        med_sp = float(m["spread"].median())
        print(f"[{tick}] {len(m):,} daily bars {m.index[0].date()} -> {m.index[-1].date()} "
              f"| spread {1e4 * med_sp / float(m['mid_close'].median()):.2f} bps "
              f"| B&H SR {bh[tick]['sharpe']:+.2f}", flush=True)

        for fam, (fn, variants) in FAMILIES.items():
            for i, params in enumerate(variants):
                res, tr = score_config_real(m, fn, params, daily_index, STOCK_COST_BPS)
                rows.append(dict(instrument=tick, timeframe=TF_KEY, family=fam,
                                 variant=str(i), params=str(params),
                                 bh_sharpe=bh[tick]["sharpe"], bh_max_dd=bh[tick]["max_dd"], **res))
                print(f"  {tick:>5} {TF_KEY} {fam:<9} v{i} "
                      f"cands={res.get('n_cands', 0):>5,} n={res.get('n_trades', 0):>5,} "
                      f"grPF={res.get('gross_pf', float('nan')):.3f} "
                      f"netPF={res.get('net_pf', float('nan')):.3f} "
                      f"SR={res.get('sharpe', float('nan')):+.2f} "
                      f"costR={res.get('cost_R_mean', float('nan')) * 100:.1f}% "
                      f"guard={res.get('guard', '?')[:4]}", flush=True)

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
              "cost_R_mean", "gross_R_mean", "net_R_mean", "risk_med_bps",
              "top_year_share", "win_rate", "gross_win_rate", "trades_per_day",
              "n_trades", "gross_R_total", "net_R_total", "bh_sharpe", "bh_max_dd"):
        if c in traded:
            traded[c] = pd.to_numeric(traded[c], errors="coerce")

    W = 132
    print("\n" + "=" * W)
    print(f"  INDIVIDUAL US STOCKS — 5-family sweep, D1, 6 large-caps, {WINDOW_LABEL}")
    print("  Same families, same stated variants, same engine as every prior sweep. Nothing re-tuned.")
    print("  Costs: 2bps stated spread + bps commission/slippage model (repo index convention).")
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

    print("\n  CONFIG TABLE — instrument x family, all cells")
    print(f"  {'inst':>5} {'family':<9} {'v':>1} {'trades':>7} {'grPF':>6} {'netPF':>6} "
          f"{'Sharpe':>8} {'DSR':>5} {'maxDD':>6} {'costR%':>7} {'1R bps':>7} {'top%':>5} "
          f"{'OOS?':>4} {'B&H?':>5} {'guard':>5}")
    print("  " + "-" * (W - 4))
    for _, r in traded.sort_values(["instrument", "family", "variant"]).iterrows():
        share = r["top_year_share"]
        print(f"  {r['instrument']:>5} {r['family']:<9} {r['variant']:>1} "
              f"{int(r['n_trades']):>7,} {r['gross_pf']:>6.3f} {r['net_pf']:>6.3f} "
              f"{r['sharpe']:>+8.2f} {r['dsr']:>5.2f} {r['max_dd'] * 100:>5.1f}% "
              f"{r['cost_R_mean'] * 100:>6.1f}% {r['risk_med_bps']:>7.1f} "
              + (f"{share * 100:>4.0f}%" if np.isfinite(share) else f"{'n/a':>5}")
              + f" {'YES' if r['oos_holds'] else 'no':>4} "
              f"{'BEAT' if r['beats_bh'] else 'lose':>5} {r['guard'][:5]:>5}")
    print("=" * W)

    per_year(traded)
    verdict(traded, bh, n_batch, cumulative)


def per_year(traded: pd.DataFrame) -> None:
    ycols = sorted([c for c in traded.columns if c.startswith("yr_")])
    if not ycols:
        return
    print("\n  YEAR-BY-YEAR net R, ALL configs (single-year concentration = gate)")
    head = "  " + f"{'config':<22}" + "".join(f"{c[3:]:>9}" for c in ycols) + f"{'total':>10}{'top%':>7}"
    print(head)
    print("  " + "-" * (len(head) - 2))
    for _, r in traded.sort_values("sharpe", ascending=False).iterrows():
        vals = [float(r[c]) if pd.notna(r.get(c)) else 0.0 for c in ycols]
        share = r["top_year_share"]
        label = f"{r['instrument']} {r['family']} v{r['variant']}"
        print(f"  {label:<22}" + "".join(f"{v:>+9.1f}" for v in vals) + f"{sum(vals):>+10.1f}"
              + (f"{share * 100:>6.0f}%" if np.isfinite(share) else f"{'n/a':>7}"))


def verdict(traded: pd.DataFrame, bh: dict, n_batch: int, cumulative: int) -> None:
    n = len(traded)
    survivors = traded[traded["SURVIVOR"]]
    best = traded.sort_values("sharpe", ascending=False).iloc[0]

    print("\n  GATE TALLY")
    print("  " + "-" * 60)
    for label, col in (("look-ahead guard PASS", None), ("gross PF > 1", "gross_edge"),
                       ("net PF > 1", None), ("net Sharpe > 0", None), (f"DSR > {DSR_BAR}", None),
                       ("OOS holds", "oos_holds"), (f"top year <= {CONC_BAR:.0%} of net R", "not_concentrated"),
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
        print("\n  NOT A LEAD — STATE_OF_PLAY section 7 rule 3: run_sweep_stocks_pre2018.py must")
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
        print(f"    {inst:>5}: best D1 config SR {s['sharpe']:+.2f} (maxDD {s['max_dd'] * 100:.1f}%)  "
              f"vs  B&H SR {b_sr:+.2f} (maxDD {b_dd * 100:.1f}%)  -> "
              f"{'BEATS' if s['sharpe'] > b_sr else 'LOSES'}")

    print(f"\n  Cumulative project trials after this batch: {cumulative} "
          f"({PRIOR_TRIALS} prior + {n_batch} stocks cells)")
    print("  " + "=" * 90)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--analyze" in sys.argv:
        analyze_only()
    else:
        main()
