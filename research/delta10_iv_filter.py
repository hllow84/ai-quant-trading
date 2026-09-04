#!/usr/bin/env python3
"""
delta10_iv_filter.py -- does Ultimate Investor's live credit-spread scanner
filter (only show delta-10 short legs when IV is elevated vs its own recent
range) actually make the SHORT-OPTION outcome more consistent, or is it
theatre?

This is NOT a full profitability verdict on short options -- sec 20
(run_vol_risk_premium.py, naked SVXY VIX-premium harvest) already answered
that question and KILLED it on tail risk (worst single day -83.0%/-85.3%,
2018 Volmageddon, regardless of headline Sharpe). This script asks a
narrower, different question: given that naked short volatility carries
that tail profile, does entering ONLY when IV rank is high (the Ultimate
Investor scanner's live filter, project C:\\Claude Code\\Ultimate Investor,
backend/app/services/options_scanner.py -- TARGET_DELTA=0.10, 30-45 DTE,
DELTA_RANGE 0.05-0.25) reduce that risk or improve consistency at all,
versus selling the same delta-10 option with no IV filter whatsoever.

=====================================================================
DATA -- REUSED, NOT RE-DERIVED
=====================================================================
Same real, causal VIX + SPY series already validated in
scripts/test_vol_risk_premium.py (base rate: VIX > forward realized vol on
83.3% of days, 1990-2026, t=48.5, holds in all 4 decades) and used as the
live trading signal in run_vol_risk_premium.py (trailing-RV ratio, sec 20).
    data/SPY_daily_yfinance.csv  -- SPY daily close, 1993-01-29 -> 2026-08-28
    data/vix_daily_yfinance.csv  -- ^VIX daily close, 1990-01-02 -> 2026-08-28
Common overlap used: 1993-01-29 -> ~2026-07 (last ~40 days dropped so every
opened trade has real subsequent price/vol history to expire against --
otherwise the last cohort would be censored mid-life, biasing win rate up).

=====================================================================
OPTION PRICING -- BLACK-SCHOLES WITH REAL VIX AS IMPLIED VOL
=====================================================================
Same approach as sec 20 (VIX as the market's own IV, not a fitted or
assumed number) and sec 24/research/long_call_trend.py (BS approximation
stated plainly because no free historical SPY option-chain data exists).
HONEST LIMITATIONS, stated up front, not silently assumed:
  - VIX is a 30-day ATM-ish implied-vol INDEX, not the actual OTM-wing IV a
    delta-10 strike trades at. Real 10-delta wings carry a volatility SKEW
    premium above ATM (SPY puts especially) -- using flat VIX as the wing's
    sigma UNDERSTATES the real premium received on puts and OVERSTATES it
    for calls (skew is asymmetric). This is the same "flat vol surface"
    simplification used throughout this project's options work (sec 24)
    because no free skew data exists. Flagged, not hidden.
  - VIX is nominally a 30-day measure, applied flat here to a 37-day option
    (see DTE choice below) -- a small, stated basis, same treatment as
    sec 24's "VIX/VXN used flat for both tenors."
  - r = 4.5% constant, matching Ultimate Investor's own RISK_FREE_RATE
    constant exactly (options_scanner.py line 33), not re-fit here.
  - q = 0 (SPY dividend yield ignored) -- SPY's yield (~1.3%) is small for a
    37-day option; slightly overprices puts / underprices calls, stated.
  - This is a MARK-TO-MARKET simulation using the REAL subsequent VIX and
    SPY path every single day of each trade's life (not a static/frozen
    entry-day IV) -- this is what makes the tail-risk numbers below
    meaningful: a real vol-spike day re-prices the still-open short options
    using the REAL VIX print that day, exactly capturing what a real short
    seller would have marked-to-market on, e.g., 2018-02-05.

DTE: 37 calendar days -- the midpoint Ultimate Investor's own
_find_target_expiry() targets inside its stated 30-45 DTE window
(TARGET_DTE_MIN=30, TARGET_DTE_MAX=45, closest-to-37 tie-break). Expiry =
last trading day on/before entry_date + 37 calendar days.

STRIKE: solved analytically from the Black-Scholes delta formula for the
EXACT target |delta| = 0.10 (Ultimate Investor's TARGET_DELTA), both put and
call side, each run as its own independent book (never combined into a
strangle -- Ultimate Investor's scanner also lists Bull Put and Bear Call
as separate, independent opportunities on the same ticker/date).

=====================================================================
THE TWO GROUPS -- causal, no look-ahead
=====================================================================
IV RANK(t) = pandas rolling(252, causal).rank(pct=True) of VIX(t) inside its
own trailing 1-year window -- known fully at the close of day t, uses only
data through t (this IS "IV rank" as options desks define it: current IV's
percentile inside its own recent range).
ELIGIBLE(t) = IV_RANK(t) >= 2/3 (top tercile) for the FILTERED group ("the
Ultimate Investor filter"); ELIGIBLE(t) = True unconditionally (same-history
start date, so the two groups differ ONLY in the filter, not in available
history) for the UNFILTERED / CONTROL group.
A new position may only be OPENED on day t+1 using ELIGIBLE(t) decided at
the close of day t (one full trading day of delay between "IV rank known"
and "position opened") -- same causal-shift convention as sec 20's
ratio(t)->position(t+1). One position open at a time per book; re-check
eligibility the day after the prior position in that book expires.

=====================================================================
SIZING / COSTS -- stated, not invented to flatter either group
=====================================================================
Naked short options carry UNDEFINED risk -- there is no "max_risk" the way
Ultimate Investor's CREDIT SPREADS have (short leg + long leg = width caps
risk). To get a capital base for a return series at all, margin is
estimated with the standard broker/CBOE rule-of-thumb for a naked short
equity option:
    margin = 100 x [ premium + max(0.20 x S - OTM_amount, 0.10 x K) ]
This is a REAL, commonly quoted formula (not fitted to make either group
look better) and is held FIXED at its entry-day value for that trade's
life, so the daily return series is "return on margin capital committed at
entry," not a moving target.
COSTS: entry premium received = BS mid x (1 - half_spread - commission),
half_spread = 2% of premium (SAME assumption as sec 24's SPY leg),
commission = 0.5% (same as sec 24). No re-entry/exit cost is charged
separately at expiry -- it settles to intrinsic automatically, same
convention as sec 24.

=====================================================================
HONESTY GATES
=====================================================================
1. Look-ahead guard: assert every entry's eligibility flag was computed
   using ONLY vix/spy data at or before the PRIOR trading day.
2. Real transaction costs (above) -- both groups charged identically.
3. Deflated Sharpe: REFERENCE ONLY, not a survival gate (this is a
   diagnostic study of a filter, not a strategy pitch).
4. Per-year concentration reported for both groups.
5. Worst single-day AND worst single-month strategy-level (combined
   put+call pooled per group) loss reported EXPLICITLY and FIRST, before
   any Sharpe/win-rate table, because sec 20 already found this exact
   short-vol tail (-83% single day) and the whole point of this script is
   to check whether the IV filter blunts it.

TRIALS: 2 a priori cells (filtered vs unfiltered), each pooling its put-book
and call-book trades. Not a new strategy search -- a validation of an
existing filter used in a live sibling project.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
from scipy.stats import norm

from research.dsr import deflated_sharpe, expected_max_sharpe
from research.metrics import sharpe, max_drawdown, profit_factor

DATA = _ROOT / "data"
RESULTS = _ROOT / "results"
RESULTS.mkdir(exist_ok=True)

BARS_PER_YEAR = 252
DTE_DAYS = 37                    # calendar days -- see docstring
TARGET_DELTA = 0.10              # Ultimate Investor TARGET_DELTA
R_RATE = 0.045                   # Ultimate Investor RISK_FREE_RATE, exact match
IV_LOOKBACK = 252                # trailing 1y window for IV rank, causal
TOP_TERCILE = 2.0 / 3.0
HALF_SPREAD = 0.02               # sec 24 SPY assumption
COMMISSION_PCT = 0.005           # sec 24 assumption
MARGIN_UNDERLYING_PCT = 0.20     # CBOE/broker naked-equity-option rule of thumb
MARGIN_STRIKE_FLOOR_PCT = 0.10
CONTRACT_MULT = 100
END_BUFFER_DAYS = 50             # drop the tail so every trade can fully expire
CATASTROPHIC_SINGLE_DAY = -0.30  # same bar as sec 20/21
CATASTROPHIC_SINGLE_MONTH = -0.50

PRIOR_TRIALS = 1085
NEW_TRIALS = 2                   # filtered cell, unfiltered cell (each pools put+call)

OUT_CSV = RESULTS / "delta10_iv_filter.csv"
OUT_TRADES_CSV = RESULTS / "delta10_iv_filter_trades.csv"


# --------------------------------------------------------------------------- #
# data
# --------------------------------------------------------------------------- #
def load_data() -> pd.DataFrame:
    spy = pd.read_csv(DATA / "SPY_daily_yfinance.csv", index_col=0, parse_dates=True)["close"].dropna()
    vix = pd.read_csv(DATA / "vix_daily_yfinance.csv", index_col=0, parse_dates=True)["close"].dropna()
    df = pd.DataFrame({"spy": spy, "vix": vix}).dropna()
    df = df.iloc[:-END_BUFFER_DAYS] if len(df) > END_BUFFER_DAYS else df
    return df


# --------------------------------------------------------------------------- #
# Black-Scholes -- price + delta-targeted strike solve
# --------------------------------------------------------------------------- #
def bs_price(S: float, K: float, T: float, r: float, sigma: float, opt_type: str) -> float:
    if T <= 1e-9 or sigma <= 1e-9:
        return max(S - K, 0.0) if opt_type == "call" else max(K - S, 0.0)
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if opt_type == "call":
        return float(S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))
    return float(K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1))


def solve_delta10_strike(S: float, T: float, r: float, sigma: float, opt_type: str,
                         target_delta: float = TARGET_DELTA) -> float:
    """
    Analytic strike for an EXACT target |delta|, from inverting the BS delta
    formula. Call delta = N(d1) = target_delta  ->  d1 = N^-1(target_delta).
    Put delta = N(d1) - 1 = -target_delta       ->  d1 = N^-1(1 - target_delta).
    """
    if T <= 1e-9 or sigma <= 1e-9:
        return S
    d1 = norm.ppf(target_delta) if opt_type == "call" else norm.ppf(1.0 - target_delta)
    K = S * np.exp((r + 0.5 * sigma ** 2) * T - d1 * sigma * np.sqrt(T))
    return float(K)


def naked_margin(S: float, K: float, premium: float, opt_type: str) -> float:
    """CBOE/broker rule-of-thumb margin for one naked short equity option, x100."""
    otm_amount = max(S - K, 0.0) if opt_type == "put" else max(K - S, 0.0)
    base = max(MARGIN_UNDERLYING_PCT * S - otm_amount, MARGIN_STRIKE_FLOOR_PCT * K)
    return CONTRACT_MULT * (premium + base)


# --------------------------------------------------------------------------- #
# one book (put-only or call-only), filtered or unfiltered
# --------------------------------------------------------------------------- #
def run_book(df: pd.DataFrame, opt_type: str, eligible: pd.Series, group_label: str) -> tuple[pd.DataFrame, pd.Series, list]:
    """
    One position open at a time. eligible(t) (known at close of day t) gates
    whether a NEW position may be opened at t+1. Returns (trades_df,
    daily_return_series indexed on df.index, guard_records).
    """
    idx = df.index
    spy = df["spy"].to_numpy()
    vix = df["vix"].to_numpy() / 100.0
    n = len(df)

    daily_ret = pd.Series(0.0, index=idx)
    trades = []
    guard_records = []  # (entry_date, decision_date, eligible_flag) for the look-ahead check

    i = 1
    open_pos = None
    while i < n:
        if open_pos is None:
            decision_i = i - 1
            if bool(eligible.iloc[decision_i]) and np.isfinite(vix[i]):
                target_exp = idx[i] + pd.Timedelta(days=DTE_DAYS)
                j = idx.searchsorted(target_exp, side="right") - 1
                if j > i and j < n:
                    S0, sig0 = float(spy[i]), float(vix[i])
                    T0 = max((idx[j] - idx[i]).days, 1) / 365.0
                    K = solve_delta10_strike(S0, T0, R_RATE, sig0, opt_type)
                    prem_mid = bs_price(S0, K, T0, R_RATE, sig0, opt_type)
                    if prem_mid > 1e-6:
                        prem_recv = prem_mid * (1.0 - HALF_SPREAD - COMMISSION_PCT)
                        margin = naked_margin(S0, K, prem_recv, opt_type)
                        # day-of-entry mark: cash received minus the fair-value liability just
                        # established -- the spread/commission haircut is a real, immediate cost.
                        entry_equity = prem_recv * CONTRACT_MULT - prem_mid * CONTRACT_MULT
                        open_pos = dict(entry_i=i, exp_i=j, S0=S0, K=K, opt_type=opt_type,
                                        entry_date=idx[i], exp_date=idx[j],
                                        prem_mid=prem_mid, prem_recv=prem_recv, margin=margin,
                                        prev_equity=entry_equity)
                        guard_records.append((idx[i], idx[decision_i], group_label))
                        daily_ret.iloc[i] = entry_equity / margin
            i += 1
            continue

        # mark-to-market this open position on day i using REAL vix[i], spy[i]
        j = open_pos["exp_i"]
        S_t, sig_t = float(spy[i]), float(vix[i])
        T_rem = max((idx[j] - idx[i]).days, 0) / 365.0
        val = bs_price(S_t, open_pos["K"], T_rem, R_RATE, sig_t, open_pos["opt_type"])
        equity_t = open_pos["prem_recv"] * CONTRACT_MULT - val * CONTRACT_MULT
        daily_ret.iloc[i] = (equity_t - open_pos["prev_equity"]) / open_pos["margin"]
        open_pos["prev_equity"] = equity_t

        if i >= j:  # expired today
            payoff = max(S_t - open_pos["K"], 0.0) if opt_type == "call" else max(open_pos["K"] - S_t, 0.0)
            realized_pnl = (open_pos["prem_recv"] - payoff) * CONTRACT_MULT
            trades.append(dict(
                opt_type=opt_type, entry_date=open_pos["entry_date"], exp_date=open_pos["exp_date"],
                S0=open_pos["S0"], K=open_pos["K"], S_exit=S_t,
                prem_mid=open_pos["prem_mid"], prem_recv=open_pos["prem_recv"], margin=open_pos["margin"],
                payoff=payoff, realized_pnl=realized_pnl,
                ret_on_prem=realized_pnl / (open_pos["prem_recv"] * CONTRACT_MULT),
                ret_on_margin=realized_pnl / open_pos["margin"],
                expired_worthless=bool(payoff <= 1e-9), win=bool(realized_pnl > 0),
            ))
            open_pos = None
        i += 1

    tr = pd.DataFrame(trades)
    return tr, daily_ret, guard_records


# --------------------------------------------------------------------------- #
# tail-risk + summary metrics on a pooled (put+call) daily return series
# --------------------------------------------------------------------------- #
def worst_day_month(ret: pd.Series) -> dict:
    active = ret[ret != 0.0]
    if active.empty:
        return dict(worst_day=0.0, worst_day_date=None, worst_month=0.0, worst_month_date=None)
    worst_day = float(ret.min())
    worst_day_date = ret.idxmin()
    monthly = ret.groupby(ret.index.to_period("M")).apply(lambda x: float(np.prod(1 + x) - 1))
    worst_month = float(monthly.min()) if len(monthly) else 0.0
    worst_month_date = str(monthly.idxmin()) if len(monthly) else None
    return dict(worst_day=worst_day, worst_day_date=worst_day_date, worst_month=worst_month,
               worst_month_date=worst_month_date)


def year_stats(ret: pd.Series) -> tuple[dict, float]:
    active = ret.copy()
    yr_log = np.log1p(active).groupby(active.index.year).sum()
    total = float(yr_log.sum())
    top_share = float(yr_log.max() / total) if total > 0 else float("nan")
    return {int(y): float(v) for y, v in yr_log.items()}, top_share


def cell_metrics(pooled_ret: pd.Series, pooled_trades: pd.DataFrame, label: str) -> dict:
    eq = (1 + pooled_ret).cumprod()
    wdm = worst_day_month(pooled_ret)
    years, top_share = year_stats(pooled_ret)
    kill_tail = (wdm["worst_day"] < CATASTROPHIC_SINGLE_DAY) or (wdm["worst_month"] < CATASTROPHIC_SINGLE_MONTH)

    win_rate = float(pooled_trades["win"].mean()) if len(pooled_trades) else float("nan")
    pct_worthless = float(pooled_trades["expired_worthless"].mean()) if len(pooled_trades) else float("nan")
    ret_on_prem_std = float(pooled_trades["ret_on_prem"].std(ddof=1)) if len(pooled_trades) > 1 else float("nan")
    ret_on_prem_mean = float(pooled_trades["ret_on_prem"].mean()) if len(pooled_trades) else float("nan")
    worst_trade = float(pooled_trades["ret_on_prem"].min()) if len(pooled_trades) else float("nan")
    n_catastrophic_trades = int((pooled_trades["ret_on_prem"] < -1.0).sum()) if len(pooled_trades) else 0

    return dict(
        label=label, n_trades=len(pooled_trades), n_obs=int((pooled_ret != 0.0).sum()),
        win_rate=win_rate, pct_expired_worthless=pct_worthless,
        ret_on_prem_mean=ret_on_prem_mean, ret_on_prem_std=ret_on_prem_std, worst_trade_ret_on_prem=worst_trade,
        n_catastrophic_trades_gt1x_prem=n_catastrophic_trades,
        worst_day=wdm["worst_day"], worst_day_date=str(wdm["worst_day_date"]),
        worst_month=wdm["worst_month"], worst_month_date=wdm["worst_month_date"],
        sharpe=sharpe(pooled_ret, BARS_PER_YEAR), max_dd=max_drawdown(eq), pf=profit_factor(pooled_ret),
        total_ret=float(eq.iloc[-1] - 1), top_year_share=top_share,
        skew=float(pooled_ret[pooled_ret != 0].skew()) if (pooled_ret != 0).sum() > 3 else 0.0,
        ekurt=float(pooled_ret[pooled_ret != 0].kurtosis()) if (pooled_ret != 0).sum() > 4 else 0.0,
        kill_on_tail_risk=bool(kill_tail),
    )


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> None:
    W = 116
    print("=" * W)
    print("  DOES THE ULTIMATE INVESTOR IV-RANK FILTER MAKE DELTA-10 SHORT OPTIONS MORE CONSISTENT?")
    print("  Real causal VIX + SPY (same series as scripts/test_vol_risk_premium.py / run_vol_risk_premium.py).")
    print("  This is a FILTER-LOGIC validation, NOT a full profitability verdict (that is sec 20, already KILLED).")
    print("=" * W)

    df = load_data()
    print(f"\n  Data: {df.index.min().date()} -> {df.index.max().date()}  ({len(df):,} trading days)")

    iv_rank = df["vix"].rolling(IV_LOOKBACK, min_periods=IV_LOOKBACK).rank(pct=True)
    eligible_filtered = (iv_rank >= TOP_TERCILE).fillna(False)
    eligible_unfiltered = iv_rank.notna()  # same history-availability floor as the filtered group, no IV condition

    first_eligible = iv_rank.first_valid_index()
    print(f"  IV-rank warm-up: first eligible date for EITHER group = {first_eligible.date()} "
          f"(needs {IV_LOOKBACK} trading days of trailing VIX)")
    print(f"  Filtered (top-tercile IV rank) days: {int(eligible_filtered.sum()):,} / "
          f"{int(eligible_unfiltered.sum()):,} eligible days "
          f"({eligible_filtered.sum()/max(eligible_unfiltered.sum(),1):.1%})")

    cells = []
    all_guard_records = []
    all_trades = []
    for group_name, elig in [("FILTERED (IV rank top-tercile)", eligible_filtered),
                             ("UNFILTERED (control, no IV condition)", eligible_unfiltered)]:
        put_tr, put_ret, put_guard = run_book(df, "put", elig, group_name)
        call_tr, call_ret, call_guard = run_book(df, "call", elig, group_name)
        all_guard_records.extend(put_guard + call_guard)

        put_tr["leg"] = "put"; call_tr["leg"] = "call"
        pooled_trades = pd.concat([put_tr, call_tr], ignore_index=True) if len(put_tr) or len(call_tr) else pd.DataFrame()
        pooled_ret = put_ret.add(call_ret, fill_value=0.0)
        pooled_ret.name = group_name

        m = cell_metrics(pooled_ret, pooled_trades, group_name)
        m["put_n"] = len(put_tr); m["call_n"] = len(call_tr)
        m["put_win_rate"] = float(put_tr["win"].mean()) if len(put_tr) else float("nan")
        m["call_win_rate"] = float(call_tr["win"].mean()) if len(call_tr) else float("nan")
        m["put_worst_trade"] = float(put_tr["ret_on_prem"].min()) if len(put_tr) else float("nan")
        m["call_worst_trade"] = float(call_tr["ret_on_prem"].min()) if len(call_tr) else float("nan")
        cells.append(m)

        if len(pooled_trades):
            pooled_trades["group"] = group_name
            all_trades.append(pooled_trades)

    df_cells = pd.DataFrame(cells)
    df_cells.to_csv(OUT_CSV, index=False)
    if all_trades:
        pd.concat(all_trades, ignore_index=True).to_csv(OUT_TRADES_CSV, index=False)

    # ---- TAIL RISK FIRST, per the task's explicit instruction ----
    print("\n" + "#" * W)
    print("  *** TAIL RISK -- READ THIS FIRST *** (pooled put+call book per group, real subsequent SPY/VIX path)")
    print("#" * W)
    for _, r in df_cells.iterrows():
        print(f"\n  {r['label']}")
        print(f"    worst single day:   {r['worst_day']*100:+.1f}%  on {r['worst_day_date']}")
        print(f"    worst single month: {r['worst_month']*100:+.1f}%  on {r['worst_month_date']}")
        print(f"    worst single TRADE (return on premium collected): {r['worst_trade_ret_on_prem']*100:+.0f}%  "
              f"(put worst {r['put_worst_trade']*100:+.0f}%, call worst {r['call_worst_trade']*100:+.0f}%)")
        print(f"    trades losing >100% of premium collected: {r['n_catastrophic_trades_gt1x_prem']}/{r['n_trades']}")
        print(f"    KILL ON TAIL RISK (bar: day<{CATASTROPHIC_SINGLE_DAY:.0%} or month<{CATASTROPHIC_SINGLE_MONTH:.0%}): "
              f"{'YES' if r['kill_on_tail_risk'] else 'no'}")

    print("\n" + "#" * W)
    print("  CONSISTENCY -- win rate, variance of outcomes, standard risk metrics")
    print("#" * W)
    print(f"  {'group':<40} {'n':>5} {'win%':>6} {'wrthls%':>8} {'meanRet%':>9} {'sdRet%':>7} "
          f"{'Sharpe':>7} {'PF':>6} {'maxDD':>7} {'top%':>6}")
    for _, r in df_cells.iterrows():
        share = r["top_year_share"]
        print(f"  {r['label']:<40} {r['n_trades']:>5} {r['win_rate']*100:>5.0f}% {r['pct_expired_worthless']*100:>7.0f}% "
              f"{r['ret_on_prem_mean']*100:>+8.1f}% {r['ret_on_prem_std']*100:>6.1f}% {r['sharpe']:>+7.2f} "
              f"{r['pf']:>6.2f} {r['max_dd']*100:>6.1f}% "
              + (f"{share*100:>5.0f}%" if np.isfinite(share) else f"{'n/a':>6}"))
        print(f"    {'':<40} put: n={r['put_n']:>4} win {r['put_win_rate']*100:>3.0f}%   "
              f"call: n={r['call_n']:>4} win {r['call_win_rate']*100:>3.0f}%")

    # ---- DSR reference only ----
    srs = df_cells["sharpe"].to_numpy(dtype=float)
    e_max, Np, mu, sd = expected_max_sharpe(srs)
    print(f"\n  DSR REFERENCE ONLY (2-cell pool, not a survival gate): E[max SR] {e_max:+.3f} over N={Np}")
    for _, r in df_cells.iterrows():
        n_obs = max(int(r["n_obs"]), 5)
        d = deflated_sharpe(float(r["sharpe"]), srs, n_obs=n_obs, ann_factor=BARS_PER_YEAR,
                            skewness=float(r["skew"]), excess_kurtosis=float(r["ekurt"]))["dsr"]
        print(f"    {r['label']:<40} Sharpe {r['sharpe']:+.2f} -> DSR {d:.3f} (n_obs={n_obs})")

    print("\n" + "#" * W)
    print("  PER-YEAR CONCENTRATION")
    print("#" * W)
    # recompute per-year table directly from the pooled return series stored via cell_metrics' inputs
    for _, r in df_cells.iterrows():
        print(f"  {r['label']}: top-year share of total log-return = "
              + (f"{r['top_year_share']*100:.0f}%" if np.isfinite(r["top_year_share"]) else "n/a (total<=0)"))

    print("\n" + "#" * W)
    print("  LOOK-AHEAD GUARD")
    print("#" * W)
    # Independent re-derivation from raw VIX only (never trusts the precomputed `eligible` series):
    # every FILTERED-group entry's decision day must show IV rank >= top-tercile using ONLY vix data
    # through that (prior) trading day. Unfiltered entries carry no such condition -- they are counted
    # but not asserted on.
    checked_filtered = 0
    guard_fail = []
    for entry_date, decision_date, group_label in all_guard_records:
        if not group_label.startswith("FILTERED"):
            continue
        window = df["vix"].loc[:decision_date].tail(IV_LOOKBACK)
        if len(window) < IV_LOOKBACK:
            guard_fail.append((entry_date, "insufficient history at decision day"))
            continue
        pct = float((window.to_numpy() <= window.iloc[-1]).mean())
        checked_filtered += 1
        if pct < TOP_TERCILE:
            guard_fail.append((entry_date, f"recomputed IV rank {pct:.3f} < {TOP_TERCILE:.3f} at decision day {decision_date.date()}"))

    print(f"  FILTERED-group entries re-derived from raw VIX (never trusting the precomputed series): "
          f"{checked_filtered} checked, using only data through each entry's PRIOR trading day "
          f"(one full day of delay, same shift(1) convention as sec 20).")
    print(f"  UNFILTERED-group entries: {sum(1 for _, _, g in all_guard_records if g.startswith('UNFILTERED'))} "
          f"(no IV condition to violate by construction).")
    if guard_fail:
        print(f"  *** GUARD FAIL on {len(guard_fail)} entries -- investigate before trusting anything above: {guard_fail[:5]}")
    else:
        print("  PASS -- every FILTERED entry's eligibility independently re-verified from raw VIX using only "
              "information available strictly before that entry was opened.")

    print("\n" + "=" * W)
    print("  VERDICT")
    print("=" * W)
    f_row = df_cells[df_cells["label"].str.startswith("FILTERED")].iloc[0]
    u_row = df_cells[df_cells["label"].str.startswith("UNFILTERED")].iloc[0]

    win_improves = f_row["win_rate"] > u_row["win_rate"]
    var_improves = (f_row["ret_on_prem_std"] < u_row["ret_on_prem_std"]) if np.isfinite(f_row["ret_on_prem_std"]) and np.isfinite(u_row["ret_on_prem_std"]) else False
    tail_improves = (f_row["worst_day"] > u_row["worst_day"]) and (f_row["worst_month"] > u_row["worst_month"])
    both_killed = bool(f_row["kill_on_tail_risk"]) and bool(u_row["kill_on_tail_risk"])
    only_unfiltered_killed = bool(u_row["kill_on_tail_risk"]) and not bool(f_row["kill_on_tail_risk"])

    print(f"  win rate:      filtered {f_row['win_rate']*100:.0f}%  vs  unfiltered {u_row['win_rate']*100:.0f}%  "
          f"-> filter {'IMPROVES' if win_improves else 'does NOT improve'} win rate")
    print(f"  outcome sd:    filtered {f_row['ret_on_prem_std']*100:.1f}%  vs  unfiltered {u_row['ret_on_prem_std']*100:.1f}%  "
          f"-> filter {'REDUCES' if var_improves else 'does NOT reduce'} variance of outcomes")
    print(f"  worst day:     filtered {f_row['worst_day']*100:+.1f}%  vs  unfiltered {u_row['worst_day']*100:+.1f}%")
    print(f"  worst month:   filtered {f_row['worst_month']*100:+.1f}%  vs  unfiltered {u_row['worst_month']*100:+.1f}%  "
          f"-> filter {'REDUCES' if tail_improves else 'does NOT reduce'} tail risk on this specific metric")
    if both_killed:
        print("  BOTH groups breach the sec-20 catastrophic single-day/-month bar. The IV filter does NOT remove the")
        print("  underlying naked-short-option tail risk -- it can only change how OFTEN you are exposed to it.")
    elif only_unfiltered_killed:
        print("  Only the UNFILTERED control breaches the catastrophic bar -- the filter's reduced time-in-market")
        print("  (trading only top-tercile-IV days) means fewer separate tail events were sampled, not necessarily")
        print("  smaller ones. Read the worst-day/month numbers above, not just the YES/NO, before concluding safety.")
    else:
        print("  Neither group breaches the stated catastrophic single-day/-month bar over this window.")

    print(f"\n  PLAIN ANSWER: does the IV/VIX filter meaningfully improve consistency vs no filter? "
          f"{'YES' if (win_improves and var_improves and tail_improves) else 'NO / MIXED'}")
    print("  This is a filter-logic validation only -- it says nothing about whether either group is profitable")
    print("  enough to trade once compared to buy-and-hold (that comparison is out of scope here; see sec 20 for")
    print("  the full-strategy verdict on naked short vol, which was KILL regardless of any filter).")

    cumulative = PRIOR_TRIALS + NEW_TRIALS
    print(f"\n  NEW TRIALS: {NEW_TRIALS} (filtered cell, unfiltered cell; each pools its put-book + call-book).")
    print(f"  Cumulative project trials after this batch: {cumulative} ({PRIOR_TRIALS} prior + {NEW_TRIALS}).")
    print("  saved -> results/delta10_iv_filter.csv, results/delta10_iv_filter_trades.csv, "
          "results/delta10_iv_filter_run.log")
    print("=" * W)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
