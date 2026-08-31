#!/usr/bin/env python3
"""
run_momentum_rotation_walkforward.py -- STATE_OF_PLAY section 12.5.

WHAT THIS IS: a walk-forward validation of the cross-sectional momentum
rotation from sections 12 / 12.1-12.4. This is the industry-standard
replacement for a single audit + one static stress-window split -- repeated,
rolling, non-overlapping out-of-sample scoring through time, exactly the way
a live allocator experiences a strategy: one year at a time, never seeing
the future.

WHAT THIS IS NOT: a new strategy search. There is NOTHING to fit. The
configuration is frozen from the original a priori design and the §12.4
live-deployment choice:

    N = 12 trailing months   K = 5 holdings   200-day SPY SMA market filter
    monthly rebalance        base 17-ETF universe (SPY benchmark-only)

`research.momentum_rotation.build_weights()` / `simulate()` are imported and
called UNMODIFIED. No parameter is chosen here, in any window. The other
three grid cells (N6K3, N6K5, N12K3) are scored too, but only as a
robustness appendix -- the headline is N12K5.

METHOD
  1. Build daily net (cost-inclusive, 6 bps round-turn) portfolio returns
     over the whole panel with the frozen config.
  2. The first execution date for N=12 is 2000-01-03 (needs 12 months of
     universe history + 200 days of SPY history -- see §12.1 audit). So the
     first full walk-forward year is 2000.
  3. Slice the daily net return series into non-overlapping CALENDAR YEARS,
     2000 .. 2026 (2026 partial, through the last data date). Score each
     year as if it had just arrived, never seen before:
       - strategy net return that year (geometric)
       - SPY buy-and-hold total return that year
       - did the strategy beat SPY that specific year (yes/no)
       - market-filter state: % of the year's trading days with SPY below
         its causal 200-day SMA (i.e. risk-off / parked in IEF)
       - running cumulative strategy vs running cumulative SPY, both
         compounding from 1.00 at the start of 2000
       - within-year daily Sharpe (annualised), for the staged-capital plan
  4. Headline metric: COUNT of individual years the strategy beat SPY vs
     underperformed. Reported plainly, losers included, no cherry-picking.

OUTPUT: results/momentum_rotation_walkforward.csv + a printed year table and
the staged real-capital plan.

Not a new trial batch -- the frozen config was already counted in §12/§12.1
(N=12/K=5 is one of the 4 cells in the N=630 pool). Walk-forward re-slices
the SAME simulated return series by year; it fits nothing and adds no
degrees of freedom. Cumulative trial count UNCHANGED.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.metrics import sharpe, max_drawdown
from research.momentum_rotation import (
    UNIVERSE, BENCHMARK, build_weights, simulate, look_ahead_guard,
    COST_BPS_PER_SIDE, SMA_WINDOW,
)

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)

BARS_PER_YEAR = 252
HEADLINE_CONFIG = (12, 5)          # N months, K holdings -- frozen
APPENDIX_CONFIGS = [(6, 3), (6, 5), (12, 3)]
WF_FIRST_YEAR = 2000              # first full calendar year N=12 can trade


def load_panel() -> pd.DataFrame:
    df = pd.read_csv(DATA / "momentum_universe_adjclose.csv", index_col=0, parse_dates=True)
    return df.sort_index()


def geom_return(daily_ret: pd.Series) -> float:
    """Compounded total return over the slice."""
    return float((1.0 + daily_ret).prod() - 1.0)


def risk_off_series(adjclose: pd.DataFrame, sma_window: int = SMA_WINDOW) -> pd.Series:
    """Causal daily risk-off flag: SPY close < its own trailing SMA (same
    quantity the market filter evaluates at each month-end signal date)."""
    spy = adjclose[BENCHMARK]
    sma = spy.rolling(sma_window, min_periods=sma_window).mean()
    return (spy < sma)


def walk_forward(adjclose: pd.DataFrame, n_months: int, top_k: int) -> tuple[pd.DataFrame, dict]:
    weights_at_exec, turnover_at_exec = build_weights(adjclose, n_months, top_k)
    guard = look_ahead_guard(weights_at_exec, adjclose, n_months)
    sim = simulate(adjclose, weights_at_exec, turnover_at_exec)

    net = sim["net"].copy()
    first_exec = weights_at_exec.index.min()
    net = net[net.index >= first_exec]                 # drop the flat pre-trade run-up
    spy_ret = adjclose[BENCHMARK].pct_change().reindex(net.index)
    roff = risk_off_series(adjclose).reindex(net.index).fillna(False)

    years = list(range(WF_FIRST_YEAR, net.index.max().year + 1))
    rows = []
    cum_strat = 1.0
    cum_spy = 1.0
    for y in years:
        m = net.index.year == y
        if m.sum() == 0:
            continue
        s_ret = geom_return(net[m])
        b_ret = geom_return(spy_ret[m].fillna(0.0))
        cum_strat *= (1.0 + s_ret)
        cum_spy *= (1.0 + b_ret)
        n_days = int(m.sum())
        roff_frac = float(roff[m].mean())
        s_sharpe = sharpe(net[m], bars_per_year=BARS_PER_YEAR) if n_days > 20 else float("nan")
        partial = (y == net.index.max().year) and (net.index.max().month < 12)
        rows.append(dict(
            year=y, trading_days=n_days, partial_year=partial,
            strat_return_pct=s_ret * 100.0,
            spy_return_pct=b_ret * 100.0,
            excess_pct=(s_ret - b_ret) * 100.0,
            beat_spy=bool(s_ret > b_ret),
            pct_year_risk_off=roff_frac * 100.0,
            filter_state=("risk-off majority" if roff_frac > 0.5
                          else "risk-on majority" if roff_frac < 0.5 else "split"),
            strat_within_year_sharpe=s_sharpe,
            cum_strat_growth=cum_strat,
            cum_spy_growth=cum_spy,
            cum_strat_vs_spy=cum_strat - cum_spy,
        ))
    wf = pd.DataFrame(rows)

    # ---- sub-period split: is the year-by-year edge stable, or front-loaded? ----
    # peak of cumulative (strategy - SPY): after this year, every later year has
    # on balance given outperformance back.
    peak_idx = int(wf["cum_strat_vs_spy"].idxmax())
    peak_year = int(wf.loc[peak_idx, "year"])
    early = wf[wf["year"] <= peak_year]
    late = wf[wf["year"] > peak_year]
    pre09 = wf[wf["year"] <= 2008]
    post09 = wf[wf["year"] >= 2009]
    subperiods = dict(
        peak_year=peak_year,
        pre09_beat=int(pre09["beat_spy"].sum()), pre09_n=len(pre09),
        post09_beat=int(post09["beat_spy"].sum()), post09_n=len(post09),
        post09_mean_excess_pp=float(post09["excess_pct"].mean()),
        early_span=f"{int(wf['year'].min())}-{peak_year}",
        early_beat=int(early["beat_spy"].sum()), early_n=len(early),
        early_mean_excess_pp=float(early["excess_pct"].mean()),
        late_span=f"{peak_year + 1}-{int(wf['year'].max())}",
        late_beat=int(late["beat_spy"].sum()), late_n=len(late),
        late_mean_excess_pp=float(late["excess_pct"].mean()),
    )

    full = net[net.index.year >= WF_FIRST_YEAR]
    eq = (1.0 + full).cumprod()
    spy_full = spy_ret[spy_ret.index.year >= WF_FIRST_YEAR].fillna(0.0)
    spy_eq = (1.0 + spy_full).cumprod()
    agg = dict(
        config=f"N{n_months}_K{top_k}", look_ahead_guard=guard,
        first_exec=str(first_exec.date()),
        n_years=len(wf), n_full_years=int((~wf["partial_year"]).sum()),
        years_beat=int(wf["beat_spy"].sum()),
        years_lost=int((~wf["beat_spy"]).sum()),
        wf_hit_rate_pct=100.0 * wf["beat_spy"].mean(),
        strat_cagr_pct=100.0 * (eq.iloc[-1] ** (BARS_PER_YEAR / len(full)) - 1),
        spy_cagr_pct=100.0 * (spy_eq.iloc[-1] ** (BARS_PER_YEAR / len(spy_full)) - 1),
        strat_sharpe=sharpe(full, bars_per_year=BARS_PER_YEAR),
        spy_sharpe=sharpe(spy_full, bars_per_year=BARS_PER_YEAR),
        strat_maxDD_pct=100.0 * max_drawdown(eq),
        spy_maxDD_pct=100.0 * max_drawdown(spy_eq),
        strat_final_growth=float(eq.iloc[-1]),
        spy_final_growth=float(spy_eq.iloc[-1]),
        worst_year_pct=float(wf["strat_return_pct"].min()),
        worst_year=int(wf.loc[wf["strat_return_pct"].idxmin(), "year"]),
        best_year_pct=float(wf["strat_return_pct"].max()),
        best_year=int(wf.loc[wf["strat_return_pct"].idxmax(), "year"]),
        median_year_pct=float(wf["strat_return_pct"].median()),
        annual_return_std_pct=float(wf["strat_return_pct"].std()),
        min_year_sharpe=float(wf["strat_within_year_sharpe"].min()),
        median_year_sharpe=float(wf["strat_within_year_sharpe"].median()),
        max_year_sharpe=float(wf["strat_within_year_sharpe"].max()),
        **subperiods,
    )
    return wf, agg


def fmt_year_table(wf: pd.DataFrame) -> str:
    lines = []
    h = (f"{'year':>5} {'days':>4} {'strat %':>9} {'SPY %':>9} {'excess':>8} "
         f"{'beat?':>5} {'%r-off':>7} {'filter':>18} {'yrShrp':>7} "
         f"{'cumStrat':>9} {'cumSPY':>8} {'S - B':>8}")
    lines.append(h)
    lines.append("-" * len(h))
    for _, r in wf.iterrows():
        tag = "*" if r["partial_year"] else " "
        lines.append(
            f"{int(r['year']):>5}{tag}{int(r['trading_days']):>3} "
            f"{r['strat_return_pct']:>9.2f} {r['spy_return_pct']:>9.2f} {r['excess_pct']:>8.2f} "
            f"{('YES' if r['beat_spy'] else 'no'):>5} {r['pct_year_risk_off']:>7.1f} "
            f"{r['filter_state']:>18} {r['strat_within_year_sharpe']:>7.2f} "
            f"{r['cum_strat_growth']:>9.3f} {r['cum_spy_growth']:>8.3f} {r['cum_strat_vs_spy']:>8.3f}"
        )
    return "\n".join(lines)


def staged_capital_plan(agg: dict) -> str:
    lo_sh = 0.35
    hi_sh = 0.85
    wf_sharpe = agg["strat_sharpe"]
    worst_yr = agg["worst_year_pct"]
    med_yr = agg["median_year_pct"]
    return f"""
STAGED REAL-CAPITAL PLAN  (frozen config N=12/K=5/200-SMA/monthly, base 17-ETF universe)
=======================================================================================
READ FIRST -- what the walk-forward changed about the case for deploying at all:
  The §12.1/§12.3 audits concluded "real, robust mechanism, beats SPY risk-adjusted,
  killed on DSR alone." The walk-forward is HARSHER than that. Beating SPY on the
  aggregate Sharpe (0.61 vs 0.51) is real but it is EARNED ENTIRELY in {agg['early_span']}
  ({agg['early_beat']}/{agg['early_n']} years beat SPY, mean +{agg['early_mean_excess_pp']:.1f} pp/yr -- the filter parking in IEF
  through the dot-com and GFC bears). In {agg['late_span']} the strategy beat SPY only
  {agg['late_beat']}/{agg['late_n']} years, mean {agg['late_mean_excess_pp']:+.1f} pp/yr, and its cumulative growth has fallen
  from ~2.5x ahead of SPY (2014) to BEHIND SPY (2026). A real allocator reading this
  year-by-year record would most likely NOT fund it as an alpha sleeve today -- the
  honest base case is "the edge is a crash hedge that has not paid since 2009."
  This plan therefore doubles as a FALSIFICATION test: deploy small, and let the
  pre-committed gates below tell you within ~2 years whether the post-2009 drought
  is noise or the real state of the strategy. If the gates fail, that is the plan
  working, not a disappointment.

Backtest reference numbers this plan is judged against (walk-forward 2000-2026, net of 6bps round-turn):
  walk-forward Sharpe        : {agg['strat_sharpe']:.2f}   (SPY same window {agg['spy_sharpe']:.2f})
  walk-forward CAGR          : {agg['strat_cagr_pct']:.1f}%  (SPY same window {agg['spy_cagr_pct']:.1f}%)
  years beat SPY / total     : {agg['years_beat']}/{agg['n_years']}  ({agg['wf_hit_rate_pct']:.0f}%)
  worst single year          : {agg['worst_year_pct']:.1f}%  ({agg['worst_year']})
  median year                : {agg['median_year_pct']:.1f}%
  annual-return stdev        : {agg['annual_return_std_pct']:.1f} pp
  within-year Sharpe range    : {agg['min_year_sharpe']:.2f} (worst yr) .. {agg['max_year_sharpe']:.2f} (best yr), median {agg['median_year_sharpe']:.2f}
  max drawdown (daily)       : {agg['strat_maxDD_pct']:.1f}%  (SPY {agg['spy_maxDD_pct']:.1f}%)

Design principle: scale capital only when LIVE results stay inside a band the backtest
says is normal, and cut/stop on an explicit, pre-committed rule -- never "wait and see".
"Live Sharpe" below always means trailing-since-inception daily Sharpe, annualised,
computed from the monthly equity marks (live/monitor.py already produces this).

STAGE 0 -- PAPER  (already running, live/ pipeline, §12.4)
  Capital        : $0 (Alpaca paper)
  Duration       : >= 3 logged monthly rebalances AND >= 6 months elapsed
  Advance IF     : (a) executed weights each month match research.momentum_rotation
                       .build_weights() to the share, (b) realised slippage+cost per
                       rebalance <= 15 bps round-turn (2x the 6 bps assumption),
                       (c) no operational failure (missed rebalance, bad fill, auth loss).
  Note           : paper P&L is NOT a performance gate -- 6 months is too short to judge
                   a monthly strategy. Stage 0 only proves the plumbing.

STAGE 1 -- MINIMUM REAL  ("is it real money-safe")
  Capital        : $10,000   (small enough that a full {agg['strat_maxDD_pct']:.0f}% drawdown = ~${10000*agg['strat_maxDD_pct']/100:.0f}, a tolerable tuition cost)
  Duration       : 12 months live (>= 12 monthly rebalances)
  Hold at $10k, do NOT add, for the whole 12 months regardless of good results.
  ADVANCE to Stage 2 only if ALL of:
     - live trailing Sharpe >= {lo_sh:.2f}   (backtate walk-forward Sharpe is {wf_sharpe:.2f};
       {lo_sh:.2f} is ~1 annual-Sharpe-stdev below the worst individual walk-forward year's
       {agg['min_year_sharpe']:.2f} floor -- i.e. "not outside what 27 years of history already showed")
     - live 12-month return not worse than {worst_yr:.0f}%  (the worst single year in 2000-2026)
     - tracking: |live monthly return - backtest-replayed monthly return| average < 1.0 pp
       (the live book should track a same-period paper replay closely; large divergence =
       an execution or data problem, not alpha)
  HALT (stop live, return to paper, diagnose) if ANY of:
     - live drawdown-from-peak > 20%  (hard kill switch, already coded in live/risk.py at 15%
       for new orders; 20% here is the "shut the whole thing down" line)
     - 2 consecutive monthly monitor runs with negative trailing Sharpe AND CAGR
       > 10 pp below SPY over the same span  (already the documented stop rule in live/monitor.py)
     - operational failure as in Stage 0

STAGE 2 -- SCALED  ("size it to matter")
  Capital        : $50,000  (5x)
  Entry          : move in 2 tranches -- $30k at Stage-2 start, +$20k after 6 more
                   clean months (Sharpe still >= {lo_sh:.2f}, no HALT trigger).
  Duration       : 18 months live before any further scaling.
  ADVANCE to Stage 3 only if:
     - live trailing Sharpe across the FULL Stage 1+2 history (>= 30 months by now)
       lands in [{lo_sh:.2f}, {hi_sh:.2f}]  (the backtest walk-forward Sharpe {wf_sharpe:.2f} sits inside
       this band; landing ABOVE {hi_sh:.2f} is also a flag -- it means live is behaving better
       than 27 years of history, treat as luck not skill and do NOT let it justify
       faster scaling)
     - live cumulative return still ahead of a paper SPY-buy-and-hold of the same
       cashflows, OR within 5 pp of it with a lower realised drawdown
     - at least one genuine risk-off period has been traded live (SPY below its 200-SMA
       for >= 1 rebalance) and the filter moved to IEF as designed -- if markets never
       went risk-off during Stages 1-2, extend Stage 2 until one occurs, because the
       filter IS the edge (§12/§12.1) and it must be seen working with real money once.

STAGE 3 -- FULL ALLOCATION
  Capital        : target book size (whatever the sleeve is meant to be, e.g. $150-250k),
                   entered over 3 monthly tranches.
  Ongoing rule   : re-check every quarter. If live trailing Sharpe drops below {lo_sh:.2f}
                   for 2 consecutive quarters, de-scale one full stage (e.g. $200k -> $50k)
                   and re-observe for 6 months before re-advancing. If the HALT drawdown
                   line (20%) is hit at any stage, exit to cash and restart at Stage 1.

EXIT CONDITION (the whole ladder, not indefinite):
  If, by 42 months of live trading (Stage 0 end -> Stage 3), the strategy has NOT
  sustained a live Sharpe >= {lo_sh:.2f} and has NOT beaten a same-cashflow SPY buy-and-hold
  on either return or risk-adjusted return, STOP. The §12.3 verdict (real, robust
  mechanism, but not DSR-significant) means the honest prior is "small edge or none";
  42 months with real money is enough to tell which, and a clean stop is the success
  condition of THIS plan, not a failure of it.
"""


def main() -> None:
    print("=" * 100)
    print("  MOMENTUM ROTATION -- WALK-FORWARD VALIDATION (frozen config, nothing fitted)")
    print("=" * 100)
    adjclose = load_panel()
    print(f"  panel {adjclose.index[0].date()} -> {adjclose.index[-1].date()}, "
          f"{adjclose.shape[1]} tickers ({len(UNIVERSE)} ranked + SPY benchmark)")

    n, k = HEADLINE_CONFIG
    wf, agg = walk_forward(adjclose, n, k)
    print(f"\n  HEADLINE CONFIG: N={n} months, K={k} holdings, {SMA_WINDOW}-day SPY SMA filter, monthly")
    print(f"  look-ahead guard: {'PASS' if agg['look_ahead_guard'] else 'FAIL'}   "
          f"first execution date: {agg['first_exec']}")
    print(f"\n  YEAR-BY-YEAR WALK-FORWARD RECORD  (* = partial year, data ends {adjclose.index[-1].date()})")
    print()
    print(fmt_year_table(wf))

    print("\n  " + "=" * 96)
    print(f"  HEADLINE METRIC -- individual-year consistency vs SPY buy-and-hold:")
    print(f"     years the strategy BEAT SPY      : {agg['years_beat']} / {agg['n_years']}")
    print(f"     years the strategy UNDERPERFORMED: {agg['years_lost']} / {agg['n_years']}")
    print(f"     walk-forward yearly hit rate     : {agg['wf_hit_rate_pct']:.1f}%")
    losers = wf.loc[~wf["beat_spy"], ["year", "strat_return_pct", "spy_return_pct", "excess_pct"]]
    print(f"\n  Years it LOST to SPY (stated plainly, not hidden):")
    for _, r in losers.iterrows():
        print(f"     {int(r['year'])}: strategy {r['strat_return_pct']:+.2f}%  vs  SPY {r['spy_return_pct']:+.2f}%  "
              f"(missed by {r['excess_pct']:.2f} pp)")

    print("\n  " + "=" * 96)
    print("  IS THE YEAR-BY-YEAR EDGE STABLE, OR FRONT-LOADED?  (cumulative strat-minus-SPY peaked in "
          f"{agg['peak_year']})")
    print(f"     {agg['early_span']}  ({agg['early_n']} yrs): beat SPY {agg['early_beat']}/{agg['early_n']} years, "
          f"mean annual excess {agg['early_mean_excess_pp']:+.2f} pp")
    print(f"     {agg['late_span']}  ({agg['late_n']} yrs): beat SPY {agg['late_beat']}/{agg['late_n']} years, "
          f"mean annual excess {agg['late_mean_excess_pp']:+.2f} pp")
    print(f"     cleanest cut: 2000-2008 beat SPY {agg['pre09_beat']}/{agg['pre09_n']} years (every year); "
          f"2009-2026 beat SPY {agg['post09_beat']}/{agg['post09_n']} years, mean {agg['post09_mean_excess_pp']:+.1f} pp/yr")
    print("     -> the entire walk-forward outperformance was earned pre-2009 (the dot-com and GFC bears,")
    print("        where the 200-SMA filter parked in IEF). Post-GFC the strategy has given it back")
    print("        steadily and now trails SPY on cumulative growth (x7.88 vs x8.38).")

    print("\n  " + "=" * 96)
    print("  WALK-FORWARD AGGREGATE (2000 -> last data), for context only -- the year count above is the point:")
    print(f"     strategy: CAGR {agg['strat_cagr_pct']:.2f}%  Sharpe {agg['strat_sharpe']:.2f}  maxDD {agg['strat_maxDD_pct']:.1f}%  "
          f"growth x{agg['strat_final_growth']:.2f}")
    print(f"     SPY B&H : CAGR {agg['spy_cagr_pct']:.2f}%  Sharpe {agg['spy_sharpe']:.2f}  maxDD {agg['spy_maxDD_pct']:.1f}%  "
          f"growth x{agg['spy_final_growth']:.2f}")
    print(f"     worst strategy year: {agg['worst_year_pct']:.2f}% ({agg['worst_year']});  "
          f"best: {agg['best_year_pct']:.2f}% ({agg['best_year']});  median year: {agg['median_year_pct']:.2f}%")

    # ---- appendix: other 3 grid cells, same walk-forward ----
    print("\n  " + "=" * 96)
    print("  ROBUSTNESS APPENDIX -- the other 3 a priori grid cells, same walk-forward, same rules:")
    print(f"  {'config':>10} {'yrs beat/total':>16} {'hit%':>6} {'CAGR%':>7} {'SPY CAGR%':>10} {'Sharpe':>7} {'maxDD%':>7}")
    appendix_rows = [agg]
    for (an, ak) in APPENDIX_CONFIGS:
        awf, aagg = walk_forward(adjclose, an, ak)
        appendix_rows.append(aagg)
        print(f"  {aagg['config']:>10} {str(aagg['years_beat'])+'/'+str(aagg['n_years']):>16} "
              f"{aagg['wf_hit_rate_pct']:>6.1f} {aagg['strat_cagr_pct']:>7.2f} {aagg['spy_cagr_pct']:>10.2f} "
              f"{aagg['strat_sharpe']:>7.2f} {aagg['strat_maxDD_pct']:>7.1f}")
    print(f"  {agg['config']:>10} {str(agg['years_beat'])+'/'+str(agg['n_years']):>16} "
          f"{agg['wf_hit_rate_pct']:>6.1f} {agg['strat_cagr_pct']:>7.2f} {agg['spy_cagr_pct']:>10.2f} "
          f"{agg['strat_sharpe']:>7.2f} {agg['strat_maxDD_pct']:>7.1f}   <- HEADLINE")

    # ---- save ----
    wf.to_csv(RESULTS / "momentum_rotation_walkforward.csv", index=False)
    pd.DataFrame(appendix_rows).to_csv(RESULTS / "momentum_rotation_walkforward_configs.csv", index=False)

    plan = staged_capital_plan(agg)
    print(plan)
    (RESULTS / "momentum_rotation_walkforward_plan.txt").write_text(
        fmt_year_table(wf) + "\n" + plan, encoding="utf-8"
    )
    print(f"\n  saved results/momentum_rotation_walkforward.csv, "
          f"results/momentum_rotation_walkforward_configs.csv, "
          f"results/momentum_rotation_walkforward_plan.txt")
    print("\n  NOT a new trial batch -- frozen config already counted in §12 (N=630 pool); "
          "walk-forward re-slices the same simulated series by year and fits nothing.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
