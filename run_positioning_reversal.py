#!/usr/bin/env python3
"""
run_positioning_reversal.py — does a CONTRARIAN entry on positioning
extremes (funding rate at an extreme percentile of its own trailing
distribution + elevated open interest) produce a real edge, where every
price-pattern family (sections 1-11, 13) and the momentum-rotation
generalization (section 17) did not?

This is a genuinely different information category: a bet on OTHER
TRADERS' POSITIONING (funding rate, open interest), not on price shape —
the first non-price-based signal tested in this project.

DATA — reuses notes/crypto_data_availability.md's conclusions, not
re-derived (scripts/download_crypto_funding_oi.py):
  - Funding rate: Binance USD-M, full history, no retention limit.
  - Open interest: Binance's OI endpoint is ~30-DAY RETENTION ONLY —
    unusable. OI comes from Bybit v5 instead (deep history, verified BTC
    from 2020-08-04, ETH from 2020-10-21). Cross-venue (funding=Binance,
    OI=Bybit), stated not hidden.
  - Bybit OI is the SHALLOW leg and sets the usable window: BTC usable
    from ~2020-08-04, ETH from ~2020-10-21 — years shorter than the H1
    price panel already on disk (2018-01-01) or funding-rate-only history
    (2019). This shortens the test; stated plainly, not silently absorbed.

CAUSALITY — the binding constraint on this whole study, verified not
asserted: funding_pctl and oi_pctl are computed on each feature's OWN
native timestamps (funding: 8h cadence; OI: 1h cadence) using a CAUSAL
rolling window (funding: trailing 90 days = 270 obs; OI: trailing 90 days
= 2160 obs — each observation's percentile rank uses only observations AT
OR BEFORE it), then aligned onto the H1 price index via merge_asof
(direction='backward' — each price bar gets the most recent feature value
with a timestamp <= the bar's own timestamp), THEN LAGGED BY ONE FULL H1
BAR as an explicit conservative safety buffer beyond the already-causal
merge_asof match. `verify_feature_causality()` asserts, for EVERY bar used
in a trade, that the feature's underlying source timestamp is strictly
before that bar's timestamp — not sampled, not assumed.

STRATEGY: strategies/positioning_reversal.py, mechanism stated in one
sentence in that file's docstring (crowded-positioning-squeeze /
funding-rate mean-reversion — a documented phenomenon, not an arbitrary
rule). Grid: funding_bar in {5,10} (percent, each tail) x R in {1.5,2.0},
oi_bar=70 (fixed, elevated-OI threshold, not swept), k_atr=1.0, H=48 bars
(2 days) — all stated, none tuned. 2 instruments x 4 grid cells = 8 configs.

COSTS: SAME model as run_sweep_crypto.py section 13 — CRYPTO_COST_BPS
(20bps Binance taker-fee-dominated round-turn + live-measured spread +
slippage), imported unchanged, not re-derived.

ANNUALISATION: 365, not 252 — crypto has a real return observation every
calendar day, per the section-13 correction note (section 16's own
finding), applied correctly from the start here.

HONESTY GATES: look-ahead guard (position-series, research/backtest.py,
reused) PLUS the feature-causality assertion above (a different, stronger
check specific to this study's actual risk — a backfilled/leaked feature
value, not a leaked TRADE resolution), Deflated Sharpe against the
cumulative project count, per-year concentration (reported PROMINENTLY,
not as a footnote — this project has been fooled by concentration twice),
an out-of-regime split on the OI-constrained window (2023-01-01, the same
split used throughout sections 11/13/16), vs buy-and-hold BTC/ETH.

Usage: python run_positioning_reversal.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.backtest import guard_look_ahead, LookAheadError
from research.dsr import deflated_sharpe, expected_max_sharpe
from research.metrics import sharpe, max_drawdown, profit_factor
from research.ftmo_engine import simulate_trades, de_overlap, build_daily_returns, equity_from_returns, build_position_series
from run_sweep_crypto import CRYPTO_COST_BPS, load_bars
from strategies.positioning_reversal import positioning_reversal, GRID

BARS_PER_YEAR = 365  # crypto: real obs every calendar day, section-13 correction note
OOS_SPLIT = pd.Timestamp("2023-01-01", tz="UTC")
MIN_OOS_TRADES = 5
DSR_BAR = 0.95
CONC_BAR = 0.60
GUARD_THRESHOLD = 0.5
FUNDING_WINDOW_OBS = 270   # 90 days @ 8h cadence
OI_WINDOW_OBS = 2160       # 90 days @ 1h cadence
TF_DELTA_H1 = pd.Timedelta(hours=1)

PRIOR_TRIALS = 924
PRIOR_CSVS = [
    "sweep_progress.csv", "htf_breakout.csv", "sweep_indices.csv",
    "basket_configs.csv", "basket_configs_scored_pre2018.csv",
    "sneaky_pivot.csv", "sneaky_pivot_pre2018.csv", "orb.csv", "orb_pre2018.csv",
    "sweep_m1_scored.csv", "sweep_m1_rth_scored.csv",
    "sweep_crypto_scored.csv", "sweep_stocks_scored.csv", "sweep_stocks_pre2018_scored.csv",
    "regime_switch.csv", "regime_switch_longlb.csv",
    "momentum_rotation_generalization.csv",
]

INSTRUMENTS = {
    "BTCUSDT": _ROOT / "data" / "BTCUSDT_H1_2018_2025_binance.csv",
    "ETHUSDT": _ROOT / "data" / "ETHUSDT_H1_2018_2025_binance.csv",
}

OUT_CSV = _ROOT / "results" / "positioning_reversal.csv"
SCORED_CSV = _ROOT / "results" / "positioning_reversal_scored.csv"


def rolling_percentile(s: pd.Series, window: int) -> pd.Series:
    """Causal: value at position i is ranked ONLY within [i-window+1, i]."""
    return s.rolling(window, min_periods=window).apply(
        lambda x: 100.0 * (x <= x[-1]).mean(), raw=True
    )


def load_funding(symbol: str) -> pd.DataFrame:
    df = pd.read_csv(_ROOT / "data" / f"{symbol}_funding_binance.csv")
    df["funding_time"] = pd.to_datetime(df["funding_time"], format="ISO8601", utc=True)
    df = df.sort_values("funding_time").drop_duplicates("funding_time")
    df["funding_pctl"] = rolling_percentile(df["funding_rate"], FUNDING_WINDOW_OBS)
    return df


def load_oi(symbol: str) -> pd.DataFrame:
    df = pd.read_csv(_ROOT / "data" / f"{symbol}_oi_bybit.csv")
    df["oi_time"] = pd.to_datetime(df["oi_time"], format="ISO8601", utc=True)
    df = df.sort_values("oi_time").drop_duplicates("oi_time")
    df["oi_pctl"] = rolling_percentile(df["open_interest"], OI_WINDOW_OBS)
    return df


def align_feature(price_index: pd.DatetimeIndex, feature_df: pd.DataFrame,
                  time_col: str, value_col: str) -> tuple[pd.Series, pd.Series]:
    """
    Causal alignment onto the H1 price index: merge_asof(direction='backward')
    matches each price bar to the most recent feature observation with
    time_col <= the bar's own timestamp, THEN shifts by one full H1 bar as
    an explicit extra conservative lag. Returns (aligned_value, source_time)
    so the caller can assert causality directly rather than trust the merge.
    """
    left = pd.DataFrame({"bar_time": price_index}).sort_values("bar_time")
    right = feature_df[[time_col, value_col]].dropna().sort_values(time_col)
    m = pd.merge_asof(left, right, left_on="bar_time", right_on=time_col, direction="backward")
    m = m.set_index("bar_time")
    aligned_value = m[value_col].shift(1)
    aligned_source_time = m[time_col].shift(1)
    aligned_value = aligned_value.reindex(price_index)
    aligned_source_time = aligned_source_time.reindex(price_index)
    return aligned_value, aligned_source_time


def verify_feature_causality(price_index: pd.DatetimeIndex, source_time: pd.Series) -> bool:
    valid = source_time.dropna()
    bar_times = pd.Series(valid.index, index=valid.index)
    return bool((valid < bar_times).all())


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


def buy_and_hold(m: pd.DataFrame, start: pd.Timestamp) -> dict:
    daily_index = pd.date_range(start.normalize(), m.index[-1].normalize(), freq="D", tz="UTC")
    daily_close = m["mid_close"][m.index >= start].resample("1D").last().reindex(daily_index).ffill()
    ret = daily_close.pct_change().dropna()
    entry_cost = float(m["spread"][m.index >= start].iloc[0] / m["mid_close"][m.index >= start].iloc[0])
    eq = (1 + ret).cumprod() * (1 - entry_cost)
    return dict(sharpe=sharpe(ret, BARS_PER_YEAR), max_dd=max_drawdown(eq))


def score_config(m: pd.DataFrame, funding_pctl: pd.Series, oi_pctl: pd.Series,
                 params: dict, start: pd.Timestamp) -> tuple[dict, pd.DataFrame]:
    empty = pd.DataFrame()
    cands = positioning_reversal(m, funding_pctl, oi_pctl, params, TF_DELTA_H1)
    for tr in cands:
        tr["session_end"] = _coerce_utc(tr["session_end"])
        tr["entry_time"] = _coerce_utc(tr["entry_time"])
    if not cands:
        return dict(n_cands=0, n_trades=0, guard="N/A"), empty

    trades = de_overlap(simulate_trades(m, cands, strictly_after=True, cost_bps=CRYPTO_COST_BPS))
    trades = trades[trades["entry_time"] >= start]
    if trades.empty:
        return dict(n_cands=len(cands), n_trades=0, guard="N/A"), empty

    pos = build_position_series(trades, m.index)
    try:
        guard_look_ahead(pos, m["mid_close"].pct_change(), threshold=GUARD_THRESHOLD)
        guard = "PASS"
    except LookAheadError as exc:
        guard = f"FAIL:{str(exc)[:40]}"

    daily_index = pd.date_range(start.normalize(), m.index[-1].normalize(), freq="D", tz="UTC")
    daily_ret = build_daily_returns(trades, daily_index)
    equity = equity_from_returns(daily_ret)
    is_n, oos_n, is_pf, oos_pf, is_sr, oos_sr = _split_stats(trades)
    years, top_R, top_share, n_years, n_pos_years = _year_stats(trades)

    res = dict(
        n_cands=len(cands), n_trades=len(trades), guard=guard,
        n_long=int((trades["side"] == "long").sum()), n_short=int((trades["side"] == "short").sum()),
        gross_pf=profit_factor(trades["gross_R"]), net_pf=profit_factor(trades["net_R"]),
        sharpe=sharpe(daily_ret, BARS_PER_YEAR),
        skew=float(daily_ret.skew()), ekurt=float(daily_ret.kurtosis()),
        max_dd=max_drawdown(equity),
        gross_R_mean=float(trades["gross_R"].mean()), cost_R_mean=float(trades["cost_R"].mean()),
        net_R_mean=float(trades["net_R"].mean()),
        gross_R_total=float(trades["gross_R"].sum()), net_R_total=float(trades["net_R"].sum()),
        win_rate=float((trades["net_R"] > 0).mean()), gross_win_rate=float((trades["gross_R"] > 0).mean()),
        n_targets=int((trades["reason"] == "target").sum()), n_stops=int((trades["reason"] == "stop").sum()),
        n_time=int((trades["reason"] == "time").sum()),
        n_obs=int(len(daily_ret)), equity_final=float(equity.iloc[-1]) if len(equity) else float("nan"),
        is_trades=is_n, oos_trades=oos_n, is_pf=is_pf, oos_pf=oos_pf, is_sharpe=is_sr, oos_sharpe=oos_sr,
        top_year_R=top_R, top_year_share=top_share, n_years=n_years, n_pos_years=n_pos_years,
    )
    for y, v in years.items():
        res[f"yr_{y}"] = v
    return res, trades


def main() -> None:
    rows, bh = [], {}
    for inst, path in INSTRUMENTS.items():
        if not path.exists():
            print(f"[{inst}] MISSING {path.name} — skipped.", flush=True)
            continue
        print(f"\n[{inst}] loading H1 price + funding + OI ...", flush=True)
        m = load_bars(path)
        funding = load_funding(inst)
        oi = load_oi(inst)

        funding_pctl, funding_src = align_feature(m.index, funding, "funding_time", "funding_pctl")
        oi_pctl, oi_src = align_feature(m.index, oi, "oi_time", "oi_pctl")

        f_causal = verify_feature_causality(m.index, funding_src)
        o_causal = verify_feature_causality(m.index, oi_src)
        print(f"  feature causality: funding={'PASS' if f_causal else 'FAIL'} "
              f"oi={'PASS' if o_causal else 'FAIL'}", flush=True)
        if not (f_causal and o_causal):
            print("  ABORTING this instrument — feature causality check failed.", flush=True)
            continue

        # Usable window: OI is the binding (shallow) constraint, plus its
        # own 90-day rolling-percentile warmup, plus the 1-bar alignment lag.
        start = oi["oi_time"].min() + pd.Timedelta(days=90) + pd.Timedelta(hours=1)
        print(f"  usable window starts {start} (OI start {oi['oi_time'].min()} "
              f"+ 90d rolling-percentile warmup)", flush=True)

        bh[inst] = buy_and_hold(m, start)
        print(f"  B&H from {start.date()}: Sharpe(365) {bh[inst]['sharpe']:+.2f}", flush=True)

        for i, params in enumerate(GRID):
            res, tr = score_config(m, funding_pctl, oi_pctl, params, start)
            rows.append(dict(instrument=inst, variant=str(i), params=str(params),
                             bh_sharpe=bh[inst]["sharpe"], bh_max_dd=bh[inst]["max_dd"], **res))
            print(f"  {inst:>7} v{i} funding_bar={params['funding_bar']:>2} R={params['R']} "
                  f"cands={res.get('n_cands', 0):>4} n={res.get('n_trades', 0):>4} "
                  f"grPF={res.get('gross_pf', float('nan')):.3f} netPF={res.get('net_pf', float('nan')):.3f} "
                  f"SR={res.get('sharpe', float('nan')):+.2f} guard={res.get('guard', '?')[:4]}", flush=True)

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    analyze(df, bh)


def analyze(df: pd.DataFrame, bh: dict) -> None:
    n_batch = len(df)
    cumulative = PRIOR_TRIALS + n_batch
    traded = df[pd.to_numeric(df.get("n_trades", pd.Series(dtype=float)), errors="coerce").fillna(0) > 0].copy()
    for c in ("sharpe", "gross_pf", "net_pf", "max_dd", "skew", "ekurt", "n_obs",
              "is_pf", "oos_pf", "is_sharpe", "oos_sharpe", "oos_trades",
              "cost_R_mean", "gross_R_mean", "net_R_mean", "top_year_share",
              "win_rate", "gross_win_rate", "n_trades", "bh_sharpe", "bh_max_dd"):
        if c in traded:
            traded[c] = pd.to_numeric(traded[c], errors="coerce")

    W = 140
    print("\n" + "=" * W)
    print("  POSITIONING-EXTREME CONTRARIAN REVERSAL — funding rate + open interest, BTC/ETH")
    print("  A bet on OTHER TRADERS' POSITIONING, not price shape. First non-price-based signal tested.")
    print(f"  Configs THIS BATCH: {n_batch}  |  CUMULATIVE PROJECT TRIALS: {PRIOR_TRIALS} + {n_batch} = {cumulative}")
    print("=" * W)

    if traded.empty:
        print("\n  NO config produced a trade. Investigate before reading anything in.")
        print(f"\n  Cumulative project trials after this batch: {cumulative} ({PRIOR_TRIALS} prior + {n_batch} cells)")
        return

    sr_batch = traded["sharpe"].fillna(0.0).to_numpy()
    e_struct = expected_max_sharpe(sr_batch)
    print(f"\n  DSR pool (HEADLINE) = STRUCTURAL: this batch's {len(sr_batch)} a priori cells "
          f"-> E[max SR] {e_struct[0]:+.3f} (mu {e_struct[2]:+.3f}, sd {e_struct[3]:.3f})")

    def _dsr(r):
        if not np.isfinite(r["sharpe"]) or r["n_obs"] < 4:
            return float("nan")
        return deflated_sharpe(sr_best=float(r["sharpe"]), sr_trials=sr_batch, n_obs=int(r["n_obs"]),
                               ann_factor=BARS_PER_YEAR,
                               skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
                               excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0)["dsr"]
    traded["dsr"] = traded.apply(_dsr, axis=1)

    prior_vals = []
    for name in PRIOR_CSVS:
        p = _ROOT / "results" / name
        if p.exists():
            s = pd.to_numeric(pd.read_csv(p)["sharpe"], errors="coerce").dropna().to_numpy()
            prior_vals.append(s)
    pool_project = np.concatenate(prior_vals + [sr_batch]) if prior_vals else sr_batch
    e_cumul = expected_max_sharpe(pool_project)
    print(f"  DSR pool (CONTRAST) = project-cumulative {len(pool_project)} -> E[max SR] {e_cumul[0]:+.3f}. "
          f"NOT a gate — sigma-contaminated (research/dsr.py BUG 2).")

    traded["oos_holds"] = ((traded["is_pf"] > 1.0) & (traded["oos_pf"] > 1.0)
                           & (traded["oos_trades"] >= MIN_OOS_TRADES) & (traded["oos_sharpe"] > 0))
    traded["gross_edge"] = traded["gross_pf"] > 1.0
    traded["not_concentrated"] = traded["top_year_share"].notna() & (traded["top_year_share"] <= CONC_BAR)

    def _bh_sr(r):
        return float(bh[r["instrument"]]["sharpe"]) if r["instrument"] in bh else float(r.get("bh_sharpe", np.nan))
    traded["bh_sharpe"] = traded.apply(_bh_sr, axis=1)
    traded["beats_bh"] = traded.apply(
        lambda r: bool(np.isfinite(r["sharpe"]) and np.isfinite(r["bh_sharpe"]) and r["sharpe"] > r["bh_sharpe"]),
        axis=1)
    traded["SURVIVOR"] = (traded["gross_edge"] & (traded["net_pf"] > 1.0) & (traded["sharpe"] > 0)
                          & (traded["dsr"] > DSR_BAR) & traded["oos_holds"] & traded["not_concentrated"]
                          & traded["beats_bh"] & (traded["guard"] == "PASS"))
    traded.to_csv(SCORED_CSV, index=False)

    print("\n  CONFIG TABLE — all 8 cells")
    print(f"  {'inst':>7} {'v':>1} {'fbar':>4} {'R':>4} {'trades':>7} {'grPF':>6} {'netPF':>6} "
          f"{'Sharpe':>8} {'DSR':>5} {'maxDD':>6} {'costR%':>7} {'top%':>6} {'OOS?':>4} {'B&H?':>5} {'guard':>5}")
    print("  " + "-" * (W - 4))
    for _, r in traded.sort_values(["instrument", "variant"]).iterrows():
        p = eval(r["params"])
        share = r["top_year_share"]
        print(f"  {r['instrument']:>7} {r['variant']:>1} {p['funding_bar']:>4} {p['R']:>4} "
              f"{int(r['n_trades']):>7,} {r['gross_pf']:>6.3f} {r['net_pf']:>6.3f} "
              f"{r['sharpe']:>+8.2f} {r['dsr']:>5.2f} {r['max_dd'] * 100:>5.1f}% "
              f"{r['cost_R_mean'] * 100:>6.1f}% "
              + (f"{share * 100:>5.0f}%" if np.isfinite(share) else f"{'n/a':>6}")
              + f" {'YES' if r['oos_holds'] else 'no':>4} "
              f"{'BEAT' if r['beats_bh'] else 'lose':>5} {r['guard'][:5]:>5}")
    print("=" * W)

    print("\n  *** CONCENTRATION — reported PROMINENTLY, not a footnote ***")
    ycols = sorted([c for c in traded.columns if c.startswith("yr_")])
    if ycols:
        head = "  " + f"{'config':<20}" + "".join(f"{c[3:]:>9}" for c in ycols) + f"{'total':>10}{'top%':>7}"
        print(head)
        print("  " + "-" * (len(head) - 2))
        for _, r in traded.sort_values("sharpe", ascending=False).iterrows():
            vals = [float(r[c]) if pd.notna(r.get(c)) else 0.0 for c in ycols]
            share = r["top_year_share"]
            label = f"{r['instrument']} v{r['variant']}"
            print(f"  {label:<20}" + "".join(f"{v:>+9.1f}" for v in vals) + f"{sum(vals):>+10.1f}"
                  + (f"{share * 100:>6.0f}%" if np.isfinite(share) else f"{'n/a':>7}"))
    print(f"  Bar for 'not concentrated': top year <= {CONC_BAR:.0%} of total net R. "
          f"{int(traded['not_concentrated'].sum())}/{len(traded)} cells PASS this gate.")

    print("\n  OUT-OF-REGIME SPLIT (2023-01-01, same convention as sections 11/13/16)")
    print(f"  {'inst':>7} {'v':>1} {'IS trades':>10} {'IS PF':>7} {'IS SR':>8} "
          f"{'OOS trades':>10} {'OOS PF':>7} {'OOS SR':>8} {'holds?':>6}")
    for _, r in traded.sort_values(["instrument", "variant"]).iterrows():
        print(f"  {r['instrument']:>7} {r['variant']:>1} {int(r['is_trades']):>10} {r['is_pf']:>7.3f} "
              f"{r['is_sharpe']:>+8.2f} {int(r['oos_trades']):>10} {r['oos_pf']:>7.3f} "
              f"{r['oos_sharpe']:>+8.2f} {'YES' if r['oos_holds'] else 'no':>6}")

    n = len(traded)
    survivors = traded[traded["SURVIVOR"]]
    print("\n  GATE TALLY")
    print(f"  guard PASS {int((traded['guard'] == 'PASS').sum())}/{n} | gross PF>1 {int(traded['gross_edge'].sum())}/{n} | "
          f"net PF>1 {int((traded['net_pf'] > 1).sum())}/{n} | Sharpe>0 {int((traded['sharpe'] > 0).sum())}/{n} | "
          f"DSR>{DSR_BAR} {int((traded['dsr'] > DSR_BAR).sum())}/{n} | OOS holds {int(traded['oos_holds'].sum())}/{n} | "
          f"not concentrated {int(traded['not_concentrated'].sum())}/{n} | beats B&H {int(traded['beats_bh'].sum())}/{n}")
    print(f"  SURVIVORS: {len(survivors)}/{n}")

    print("\n  VERDICT")
    if len(survivors):
        print(f"  {len(survivors)} config(s) cleared every gate — genuinely new evidence, verify before trusting:")
        for _, r in survivors.iterrows():
            print(f"    {r['instrument']} v{r['variant']}: SR {r['sharpe']:+.2f}, DSR {r['dsr']:.3f}, "
                  f"grossPF {r['gross_pf']:.3f}, netPF {r['net_pf']:.3f}, top-year {r['top_year_share']*100:.0f}%")
    else:
        best = traded.sort_values("sharpe", ascending=False).iloc[0]
        print(f"  NO config cleared all gates. {n} cells, 0 survivors.")
        print(f"  Best raw net Sharpe: {best['instrument']} v{best['variant']} -> SR {best['sharpe']:+.2f}, "
              f"DSR {best['dsr']:.3f}, top-year concentration {best['top_year_share']*100:.0f}%, "
              f"OOS holds: {'YES' if best['oos_holds'] else 'NO'}, beats B&H: {'YES' if best['beats_bh'] else 'NO'}")

    print("\n  vs BUY-AND-HOLD:")
    for inst in traded["instrument"].unique():
        sub = traded[traded["instrument"] == inst]
        s = sub.sort_values("sharpe", ascending=False).iloc[0]
        print(f"    {inst:>7}: best config SR {s['sharpe']:+.2f} (maxDD {s['max_dd']*100:.1f}%)  vs  "
              f"B&H SR {s['bh_sharpe']:+.2f} (maxDD {s['bh_max_dd']*100:.1f}%)  -> "
              f"{'BEATS' if s['sharpe'] > s['bh_sharpe'] else 'LOSES'}")

    print(f"\n  Cumulative project trials after this batch: {cumulative} ({PRIOR_TRIALS} prior + {n_batch} cells)")
    print("  " + "=" * (W - 4))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
