#!/usr/bin/env python3
"""
run_vol_risk_premium.py — PART 2: does a strategy that harvests the
confirmed volatility risk premium (scripts/test_vol_risk_premium.py: VIX
averages +3.69 vol points above forward-realized SPY vol, 83.3% of days,
t=48.5, consistent across all 4 decades) survive real costs, real tail
risk, and the honesty gates?

A fourth distinct information category: a bet on volatility being
mispriced, not on price direction (sections 1-11/13), cross-sectional rank
(12/17), positioning (18), or cross-asset lead-lag (19).

PROXY: SVXY (ProShares Short VIX Short-Term Futures ETF), the tradeable
short-vol product the task named, available since 2011-10-04. Its REAL
historical price is used unmodified -- expense ratio, VIX-futures roll
cost/contango drag, AND its real 2018-02-05/06 near-wipeout (ProShares cut
its leverage from -1x to -0.5x VIX-futures exposure immediately after,
because the product came close to the fate its cousin XIV suffered -- XIV
was terminated) are all genuinely embedded in the price series, not
modeled around. SVXY's own backtest window (2011-2026) already spans BOTH
2018's "Volmageddon" and 2020's COVID crash -- no artificial window
construction was needed to include a major vol event; it is simply there.

SIGNAL: causal. Trailing realized SPY vol, 20 trading days, annualized
(SAME window as the base-rate check, so the strategy signal and the
confirmed base rate are measuring the same underlying quantity). Ratio =
VIX(t) / trailing_RV(t), known fully at the CLOSE of day t. Position for
day t+1 = LONG SVXY if ratio(t) > threshold, else CASH -- entered at day
t+1's close-to-close return (i.e. the position is only exposed to the
return realized AFTER the signal was known), never same-day.
Thresholds tested (task-stated): 1.2x and 1.5x.

COSTS: SVXY spread -- a stated, conservative 5bps/side (10bps round-turn)
assumption for a specialized, less-liquid-than-SPY vol ETF, charged only
when the position actually changes (SVXY<->cash), reported separately from
gross. NO separate borrow/financing cost is added on top: SVXY is a LONG
position (never a short sale requiring borrow) in a fund that itself holds
the short-VIX-futures exposure internally -- the fund's own roll cost and
expense ratio are already embedded in the real price series pulled above,
so charging a second, separate "short-vol financing cost" would double-
count a cost the data already reflects. Stated explicitly, not assumed.

TAIL RISK -- READ THIS SECTION FIRST, not the Sharpe. Worst single-day and
worst single-week (5 trading day) strategy return are computed and
reported explicitly and PROMINENTLY, ahead of any Sharpe/CAGR figure. Per
the task's explicit instruction: if the strategy shows a good average
Sharpe but has a single-day/week loss that would gut a large fraction of
account equity, THAT IS A KILL regardless of the headline number, and the
verdict below reflects that rule literally, not just descriptively.

Usage: python run_vol_risk_premium.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.dsr import deflated_sharpe, expected_max_sharpe
from research.metrics import sharpe, max_drawdown, profit_factor

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252  # US-market-hours daily strategy, standard repo convention (not crypto's 365)
RV_WINDOW = 20
THRESHOLDS = [1.2, 1.5]
SPREAD_BPS_PER_SIDE = 5.0
CATASTROPHIC_SINGLE_DAY = -0.30   # task's stated kill bar
CATASTROPHIC_SINGLE_WEEK = -0.50  # task's stated kill bar

PRIOR_TRIALS = 932  # unchanged since section 19 (0 backtested trials there)
PRIOR_CSVS = [
    "sweep_progress.csv", "htf_breakout.csv", "sweep_indices.csv",
    "basket_configs.csv", "basket_configs_scored_pre2018.csv",
    "sneaky_pivot.csv", "sneaky_pivot_pre2018.csv", "orb.csv", "orb_pre2018.csv",
    "sweep_m1_scored.csv", "sweep_m1_rth_scored.csv",
    "sweep_crypto_scored.csv", "sweep_stocks_scored.csv", "sweep_stocks_pre2018_scored.csv",
    "regime_switch.csv", "regime_switch_longlb.csv",
    "momentum_rotation_generalization.csv", "positioning_reversal_scored.csv",
]

OUT_CSV = RESULTS / "vol_risk_premium.csv"


def load_close(fname: str) -> pd.Series:
    df = pd.read_csv(DATA / fname, index_col=0, parse_dates=True)
    return df["close"].dropna()


def trailing_rv(spy_close: pd.Series, window: int) -> pd.Series:
    """Causal: RV(t) uses only log returns through day t."""
    log_ret = np.log(spy_close / spy_close.shift(1))
    return log_ret.rolling(window, min_periods=window).std() * np.sqrt(252) * 100


def build_strategy(vix: pd.Series, ratio: pd.Series, svxy_close: pd.Series,
                   threshold: float) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Returns (gross_ret, net_ret, position) all indexed on SVXY's own trading
    calendar. position(d) is decided from ratio(d-1) (previous day's close,
    fully known before d opens) -- shift(1) enforces this causally.
    """
    common_idx = svxy_close.index
    ratio_aligned = ratio.reindex(common_idx)
    signal = (ratio_aligned > threshold)
    position = signal.shift(1).fillna(False)  # decided on prior day's close, held today

    svxy_ret = svxy_close.pct_change()
    gross_ret = position.astype(float) * svxy_ret
    gross_ret = gross_ret.fillna(0.0)

    switched = position != position.shift(1).fillna(False)
    cost = switched.astype(float) * (SPREAD_BPS_PER_SIDE / 10_000.0)
    net_ret = gross_ret - cost
    return gross_ret, net_ret, position


def worst_day_week(ret: pd.Series) -> tuple[float, pd.Timestamp, float, pd.Timestamp]:
    worst_day = ret.min()
    worst_day_date = ret.idxmin()
    week_ret = (1 + ret).rolling(5).apply(lambda x: np.prod(x) - 1, raw=True)
    worst_week = week_ret.min()
    worst_week_date = week_ret.idxmin()
    return float(worst_day), worst_day_date, float(worst_week), worst_week_date


def year_stats(ret: pd.Series) -> tuple[dict, float, float]:
    yr_log = np.log1p(ret).groupby(ret.index.year).sum()
    total = float(yr_log.sum())
    top = float(yr_log.max()) if len(yr_log) else float("nan")
    share = (top / total) if total > 0 else float("nan")
    return {int(y): float(v) for y, v in yr_log.items()}, top, share


def buy_and_hold(close: pd.Series) -> dict:
    ret = close.pct_change().dropna()
    eq = (1 + ret).cumprod()
    wd, wdd, ww, wwd = worst_day_week(ret)
    return dict(sharpe=sharpe(ret, BARS_PER_YEAR), max_dd=max_drawdown(eq),
               worst_day=wd, worst_day_date=wdd, worst_week=ww, worst_week_date=wwd)


def event_window(ret: pd.Series, start: str, end: str) -> dict:
    sl = ret[start:end]
    if sl.empty:
        return dict(n=0, total_ret=float("nan"), worst_day=float("nan"))
    total = float((1 + sl).prod() - 1)
    return dict(n=len(sl), total_ret=total, worst_day=float(sl.min()), worst_day_date=sl.idxmin())


def main() -> None:
    spy = load_close("SPY_daily_yfinance.csv")
    vix = load_close("vix_daily_yfinance.csv")
    svxy = load_close("svxy_daily_yfinance.csv")

    rv = trailing_rv(spy, RV_WINDOW)
    ratio = (vix / rv).dropna()

    print("=" * 100)
    print("  VOLATILITY RISK PREMIUM HARVEST — SVXY, VIX/trailing-RV signal")
    print(f"  Backtest window: SVXY availability, {svxy.index.min().date()} -> {svxy.index.max().date()}")
    print("  This window ALREADY spans 2018 Volmageddon and 2020 COVID crash -- no construction needed.")
    print("=" * 100)

    bh_spy = buy_and_hold(spy[spy.index >= svxy.index.min()])
    bh_svxy = buy_and_hold(svxy)
    print(f"\n  B&H SPY  over this window: Sharpe {bh_spy['sharpe']:+.2f}, maxDD {bh_spy['max_dd']*100:.1f}%, "
          f"worst day {bh_spy['worst_day']*100:+.1f}% ({bh_spy['worst_day_date'].date()}), "
          f"worst week {bh_spy['worst_week']*100:+.1f}%")
    print(f"  B&H SVXY over this window: Sharpe {bh_svxy['sharpe']:+.2f}, maxDD {bh_svxy['max_dd']*100:.1f}%, "
          f"worst day {bh_svxy['worst_day']*100:+.1f}% ({bh_svxy['worst_day_date'].date()}), "
          f"worst week {bh_svxy['worst_week']*100:+.1f}%")

    rows = []
    all_causal = True
    for thr in THRESHOLDS:
        gross, net, position = build_strategy(vix, ratio, svxy, thr)
        # explicit causality re-derivation: position(d) must equal (ratio(d-1) > thr)
        ratio_shift = ratio.reindex(position.index).shift(1)
        expected_signal = (ratio_shift > thr).fillna(False)
        causal_ok = bool((position == expected_signal).all())
        all_causal &= causal_ok

        eq_gross = (1 + gross).cumprod()
        eq_net = (1 + net).cumprod()
        wd, wdd, ww, wwd = worst_day_week(net)
        years, top_yr, top_share = year_stats(net)

        v2018 = event_window(net, "2018-02-01", "2018-02-28")
        v2020 = event_window(net, "2020-02-15", "2020-04-15")

        pct_in_position = float(position.mean())
        n_switches = int((position != position.shift(1).fillna(False)).sum())

        kill_tail = (wd < CATASTROPHIC_SINGLE_DAY) or (ww < CATASTROPHIC_SINGLE_WEEK)

        row = dict(
            threshold=thr, n_obs=len(net), pct_in_position=pct_in_position, n_switches=n_switches,
            sharpe_gross=sharpe(gross, BARS_PER_YEAR), sharpe_net=sharpe(net, BARS_PER_YEAR),
            pf_gross=profit_factor(gross), pf_net=profit_factor(net),
            max_dd=max_drawdown(eq_net), total_ret_net=float(eq_net.iloc[-1] - 1),
            worst_day=wd, worst_day_date=str(wdd.date()), worst_week=ww, worst_week_date=str(wwd.date()),
            top_year_log=top_yr, top_year_share=top_share,
            volmageddon_feb2018_ret=v2018["total_ret"], volmageddon_worst_day=v2018["worst_day"],
            covid_2020_ret=v2020["total_ret"], covid_worst_day=v2020["worst_day"],
            causal_ok=causal_ok, kill_on_tail_risk=kill_tail,
            skew=float(net.skew()), ekurt=float(net.kurtosis()),
        )
        for y, v in years.items():
            row[f"yr_{y}"] = v
        rows.append(row)

        print(f"\n  --- threshold {thr}x ---  causal={'PASS' if causal_ok else 'FAIL'}")
        print(f"  in-position {pct_in_position:.1%} of days, {n_switches} position switches")
        print(f"  *** TAIL RISK (read this first) ***")
        print(f"    worst single day:  {wd*100:+.1f}%  on {wdd.date()}")
        print(f"    worst single week: {ww*100:+.1f}%  on {wwd.date()}")
        print(f"    2018 Volmageddon window (Feb 2018): strategy total return {v2018['total_ret']*100:+.1f}%, "
              f"worst day in window {v2018['worst_day']*100:+.1f}%")
        print(f"    2020 COVID crash window (Feb15-Apr15 2020): strategy total return {v2020['total_ret']*100:+.1f}%, "
              f"worst day in window {v2020['worst_day']*100:+.1f}%")
        print(f"  net Sharpe {sharpe(net, BARS_PER_YEAR):+.2f}  gross Sharpe {sharpe(gross, BARS_PER_YEAR):+.2f}  "
              f"net PF {profit_factor(net):.3f}  maxDD {max_drawdown(eq_net)*100:.1f}%  "
              f"total net return {float(eq_net.iloc[-1]-1)*100:+.1f}%")
        print(f"  top-year concentration: "
              + (f"{top_share*100:.0f}% of total log-return" if np.isfinite(top_share) else "n/a (total <= 0)"))

    df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    analyze(df, bh_spy, all_causal)


def analyze(df: pd.DataFrame, bh_spy: dict, all_causal: bool) -> None:
    n_batch = len(df)
    cumulative = PRIOR_TRIALS + n_batch

    sr_batch = df["sharpe_net"].fillna(0.0).to_numpy()
    e_struct = expected_max_sharpe(sr_batch)

    def _dsr(r):
        if not np.isfinite(r["sharpe_net"]) or r["n_obs"] < 4:
            return float("nan")
        return deflated_sharpe(sr_best=float(r["sharpe_net"]), sr_trials=sr_batch, n_obs=int(r["n_obs"]),
                               ann_factor=BARS_PER_YEAR,
                               skewness=float(r["skew"]) if np.isfinite(r["skew"]) else 0.0,
                               excess_kurtosis=float(r["ekurt"]) if np.isfinite(r["ekurt"]) else 0.0)["dsr"]
    df["dsr"] = df.apply(_dsr, axis=1)

    W = 110
    print("\n" + "=" * W)
    print("  SUMMARY TABLE — TAIL RISK COLUMNS FIRST, PER THE TASK'S EXPLICIT INSTRUCTION")
    print("=" * W)
    print(f"  {'thr':>4} {'worst day':>10} {'worst week':>11} {'kill(tail)':>10} {'net SR':>8} {'DSR':>5} "
          f"{'netPF':>6} {'maxDD':>7} {'top%':>6}")
    print("  " + "-" * (W - 4))
    for _, r in df.iterrows():
        share = r["top_year_share"]
        print(f"  {r['threshold']:>4} {r['worst_day']*100:>9.1f}% {r['worst_week']*100:>10.1f}% "
              f"{'YES' if r['kill_on_tail_risk'] else 'no':>10} {r['sharpe_net']:>+8.2f} {r['dsr']:>5.2f} "
              f"{r['pf_net']:>6.3f} {r['max_dd']*100:>6.1f}% "
              + (f"{share*100:>5.0f}%" if np.isfinite(share) else f"{'n/a':>6}"))
    print("=" * W)

    print(f"\n  Causality (structural, re-derived per config): {'ALL PASS' if all_causal else 'FAIL -- investigate'}")
    print(f"  DSR structural pool = this batch's own {n_batch} a priori cells, E[max SR] {e_struct[0]:+.3f}")

    print("\n  vs BUY-AND-HOLD SPY (same window):")
    print(f"    B&H SPY: Sharpe {bh_spy['sharpe']:+.2f}, maxDD {bh_spy['max_dd']*100:.1f}%, "
          f"worst day {bh_spy['worst_day']*100:+.1f}%, worst week {bh_spy['worst_week']*100:+.1f}%")
    for _, r in df.iterrows():
        beats = r["sharpe_net"] > bh_spy["sharpe"]
        print(f"    threshold {r['threshold']}x: net Sharpe {r['sharpe_net']:+.2f} -> "
              f"{'BEATS' if beats else 'LOSES TO'} SPY on Sharpe alone")

    print("\n  VERDICT")
    print("  " + "-" * (W - 4))
    any_tail_kill = bool(df["kill_on_tail_risk"].any())
    if any_tail_kill:
        print("  *** KILL ON TAIL-RISK GROUNDS, REGARDLESS OF ANY HEADLINE SHARPE ABOVE ***")
        for _, r in df[df["kill_on_tail_risk"]].iterrows():
            print(f"    threshold {r['threshold']}x: worst single day {r['worst_day']*100:+.1f}% "
                  f"({r['worst_day_date']}), worst single week {r['worst_week']*100:+.1f}% ({r['worst_week_date']})")
            print(f"      This single event alone would have destroyed "
                  f"{abs(min(r['worst_day'], 0)) * 100:.0f}%+ of the capital allocated to this position on "
                  f"that day — an attractive average Sharpe elsewhere in the series does not offset this.")
    else:
        print("  No config breaches the stated single-day/-week catastrophic-loss bar.")

    n_dsr = int((df["dsr"] > 0.95).sum())
    print(f"\n  DSR > 0.95: {n_dsr}/{n_batch}")
    survivors = df[(df["dsr"] > 0.95) & (df["sharpe_net"] > 0) & (~df["kill_on_tail_risk"])
                  & (df["sharpe_net"] > bh_spy["sharpe"])]
    print(f"  SURVIVORS (DSR>0.95 AND net Sharpe>0 AND beats SPY AND NOT tail-risk-killed): {len(survivors)}/{n_batch}")

    print(f"\n  Cumulative project trials after this batch: {cumulative} ({PRIOR_TRIALS} prior + {n_batch} cells)")
    print("  " + "=" * (W - 4))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
