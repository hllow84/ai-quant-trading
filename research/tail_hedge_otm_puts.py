#!/usr/bin/env python3
"""
tail_hedge_otm_puts.py -- STATE_OF_PLAY section 34.2.

TAIL-RISK HEDGE: a small, constant allocation to OTM SPY puts, rolled
monthly, layered on top of a fully-invested (100%) SPY position -- the
standard institutional "tail-hedged equity" overlay framing (retain full
equity beta, pay a recurring insurance toll), not a reduction of SPY
exposure.

REUSES, UNCHANGED, the SAME Black-Scholes/real-VIX approximation already
validated in this project for the credit-spread (sec 27) and delta-10 IV
filter (sec 26) work: `bs_price()` from research/delta10_iv_filter.py,
R_RATE=4.5% (project convention, exact match to the sibling live project's
RISK_FREE_RATE), sigma = real trailing VIX/100 (flat, no smile), marked to
market DAILY using the REAL subsequent VIX+SPY path for the option's whole
life (not frozen at entry) -- same convention as sec 24/26.

STATED LIMITATIONS (repeated here, not silently dropped, per the existing
sec 26 precedent): flat VIX as the OTM put's IV ignores the real skew
premium that OTM puts trade at in practice (skew UNDERSTATES the true cost
of this hedge -- a real trader would pay MORE than this model prices, so
if this hedge already looks expensive here, it is a conservative-for-the-
hedge, i.e. flattering, assumption). VIX is nominally a 30d measure applied
here to a ~30-33 calendar-day option, a reasonable match (better than sec
24/26's 37d mismatch).

STRIKE CONVENTION (stated design decision, not asked as a question): fixed
5% OUT-OF-THE-MONEY (K = 0.95 x spot at roll date), the standard "5% OTM
protective put" convention used by e.g. Cboe's own protective-put indices
-- chosen over a delta-target (like sec 26's delta-10) because the user's
brief explicitly offered "5-10% OTM" as the natural framing for a hedge
overlay (vs a delta target, which is the framing used for the short-premium
credit-spread work); 5% (not 10%) is the more standard/cheaper "close-to-
the-money" tail-hedge convention and is used here as the primary test.

ROLL: 30 calendar days to expiry at each roll date, monthly cadence (first
trading day of each calendar month), continuous (a new position opens the
trading day after the prior one expires/settles).

ALLOCATION: `HEDGE_ALLOC_PCTS = [0.01, 0.02]` of CURRENT total portfolio
equity is spent on premium at each roll -- an ONGOING recurring cost, not a
one-time capital carve-out; the SPY sleeve stays at 100% notional exposure
throughout (this is the overlay framing, not a reduced-equity framing).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd

from research.delta10_iv_filter import bs_price, R_RATE, HALF_SPREAD, COMMISSION_PCT, load_data
from research.dsr import deflated_sharpe
from research.metrics import sharpe, max_drawdown
from research.six_strategies_engine import drawdown_with_recovery

RESULTS = _ROOT / "results"
BARS_PER_YEAR = 252
DTE_DAYS = 30
OTM_PCT = 0.05           # 5% OTM strike, primary convention (stated above)
HEDGE_ALLOC_PCTS = [0.01, 0.02]
CONTRACT_MULT = 100
CRISIS_2008 = (pd.Timestamp("2008-01-01"), pd.Timestamp("2008-12-31"))
CRISIS_2020 = (pd.Timestamp("2020-01-01"), pd.Timestamp("2020-12-31"))
CRISIS_2020_ACUTE = (pd.Timestamp("2020-02-19"), pd.Timestamp("2020-03-23"))  # the actual crash window


def month_start_dates(idx: pd.DatetimeIndex) -> list[pd.Timestamp]:
    s = pd.Series(idx, index=idx)
    return sorted(s.groupby([idx.year, idx.month]).min().tolist())


def build_hedged_series(df: pd.DataFrame, hedge_alloc: float) -> dict:
    """Returns dict with daily_ret (SPY + put-overlay), spy_daily_ret,
    guard_pass, trades (list of dicts)."""
    idx = df.index
    spy = df["spy"].to_numpy()
    vix = df["vix"].to_numpy() / 100.0
    n = len(idx)
    roll_dates = set(month_start_dates(idx))

    spy_ret = pd.Series(df["spy"]).pct_change().fillna(0.0)

    # Contract count is sized off the RUNNING equity at each roll date (hedge_alloc% of
    # current equity spent on premium each month), so equity and positions are built in
    # one single forward pass -- no look-ahead, equity_{t-1} is used at every step.
    equity = 1.0
    hedge_pnl_ret = pd.Series(0.0, index=idx)
    open_pos = None
    trades = []
    guard_records = []
    i = 1
    while i < n:
        today = idx[i]
        if open_pos is None and today in roll_dates:
            decision_i = i - 1
            S0, sig0 = float(spy[decision_i]), float(vix[decision_i])
            if np.isfinite(S0) and np.isfinite(sig0) and sig0 > 0:
                target_exp = today + pd.Timedelta(days=DTE_DAYS)
                j = idx.searchsorted(target_exp, side="right") - 1
                if j > i and j < n:
                    K = S0 * (1.0 - OTM_PCT)
                    T0 = max((idx[j] - today).days, 1) / 365.0
                    prem_mid = bs_price(S0, K, T0, R_RATE, sig0, "put")
                    if prem_mid > 1e-6:
                        prem_paid = prem_mid * (1.0 + HALF_SPREAD + COMMISSION_PCT)
                        budget = hedge_alloc * equity
                        n_units = budget / (prem_paid * CONTRACT_MULT)
                        fair_val0 = n_units * prem_mid * CONTRACT_MULT
                        # immediate cost of crossing the spread + commission, charged today
                        hedge_pnl_ret.iloc[i] += (fair_val0 - budget) / equity
                        equity *= (1.0 + hedge_pnl_ret.iloc[i] + spy_ret.iloc[i])
                        open_pos = dict(exp_i=j, entry_date=today, exp_date=idx[j], S0=S0, K=K,
                                         prem_mid=prem_mid, prem_paid=prem_paid, n_units=n_units,
                                         prev_val=fair_val0, budget=budget)
                        guard_records.append((today, idx[decision_i]))
                        i += 1
                        continue

        if open_pos is not None:
            j = open_pos["exp_i"]
            S_t, sig_t = float(spy[i]), float(vix[i])
            T_rem = max((idx[j] - today).days, 0) / 365.0
            val_t = open_pos["n_units"] * bs_price(S_t, open_pos["K"], T_rem, R_RATE, sig_t, "put") * CONTRACT_MULT
            hedge_pnl_ret.iloc[i] += (val_t - open_pos["prev_val"]) / equity
            open_pos["prev_val"] = val_t

            if i >= j:
                payoff = open_pos["n_units"] * max(open_pos["K"] - S_t, 0.0) * CONTRACT_MULT
                realized = payoff - open_pos["budget"]
                trades.append(dict(entry_date=open_pos["entry_date"], exp_date=open_pos["exp_date"],
                                    S0=open_pos["S0"], K=open_pos["K"], S_exit=S_t,
                                    prem_paid_total=open_pos["budget"], payoff=payoff,
                                    realized_pnl=realized, ret_on_prem=realized / open_pos["budget"],
                                    expired_worthless=bool(payoff <= 1e-9)))
                open_pos = None

        equity *= (1.0 + hedge_pnl_ret.iloc[i] + spy_ret.iloc[i])
        i += 1

    total_ret = spy_ret + hedge_pnl_ret
    guard_pass = all(dec_date < entry_date for entry_date, dec_date in guard_records)
    return dict(daily_ret=total_ret, spy_ret=spy_ret, hedge_pnl_ret=hedge_pnl_ret,
                guard_pass=guard_pass, trades=pd.DataFrame(trades))


def window_stats(ret: pd.Series) -> dict:
    ret = ret.dropna()
    eq = (1 + ret).cumprod()
    years = len(ret) / BARS_PER_YEAR
    total_ret = float(eq.iloc[-1] - 1)
    cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else float("nan")
    dd = drawdown_with_recovery(eq)
    rec_days = (dd["recovery_date"] - dd["trough_date"]).days if dd["recovery_date"] is not None else None
    return dict(n_obs=len(ret), years=years, sharpe=sharpe(ret, BARS_PER_YEAR), cagr_pct=cagr * 100,
                total_return_pct=total_ret * 100, maxDD_pct=max_drawdown(eq) * 100, recovery_days=rec_days)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    W = 112
    print("=" * W)
    print("  SECTION 34.2 -- TAIL-RISK HEDGE: SMALL CONSTANT ALLOCATION TO OTM SPY PUTS")
    print("=" * W)
    print(f"\nStrike: {OTM_PCT*100:.0f}% OTM (K=0.95xspot). Roll: monthly, {DTE_DAYS}d target tenor. "
          f"Sigma: flat trailing VIX (skew ignored -- understates true hedge cost, flattering the hedge). "
          f"r={R_RATE*100:.1f}%. Costs: {HALF_SPREAD*100:.0f}% half-spread + {COMMISSION_PCT*100:.1f}% "
          f"commission on entry (buyer pays the ask), same sec 24/26 assumptions.")

    df = load_data()
    print(f"\nData: SPY+VIX daily, {df.index[0].date()} .. {df.index[-1].date()}, {len(df):,} days")

    spy_only = df["spy"].pct_change().fillna(0.0)
    spy_stats_full = window_stats(spy_only)
    print(f"\nUNHEDGED SPY baseline (full period): Sharpe {spy_stats_full['sharpe']:.3f}  "
          f"CAGR {spy_stats_full['cagr_pct']:.2f}%  total_return {spy_stats_full['total_return_pct']:.1f}%  "
          f"maxDD {spy_stats_full['maxDD_pct']:.2f}%")

    all_rows = []
    calm_year_bleeds = {}
    for alloc in HEDGE_ALLOC_PCTS:
        print(f"\n{'='*W}\n  ALLOCATION {alloc*100:.0f}% of equity spent on premium per roll\n{'='*W}")
        res = build_hedged_series(df, alloc)
        ret = res["daily_ret"]
        print(f"  Look-ahead guard: {'PASS' if res['guard_pass'] else 'FAIL'} ({len(res['trades'])} rolled puts)")

        s = window_stats(ret)
        print(f"  FULL PERIOD (hedged): Sharpe {s['sharpe']:.3f}  CAGR {s['cagr_pct']:.2f}%  "
              f"total_return {s['total_return_pct']:.1f}%  maxDD {s['maxDD_pct']:.2f}%  "
              f"recovery {s['recovery_days']}d")
        print(f"    vs UNHEDGED SPY: Sharpe {spy_stats_full['sharpe']:.3f}  CAGR {spy_stats_full['cagr_pct']:.2f}%  "
              f"maxDD {spy_stats_full['maxDD_pct']:.2f}%")

        # ---- steady-state bleed: calm years = every year EXCLUDING 2008 and 2020 ----
        yearly_hedge_pnl = res["hedge_pnl_ret"].groupby(res["hedge_pnl_ret"].index.year).apply(lambda x: float(np.prod(1 + x) - 1))
        calm_years = [y for y in yearly_hedge_pnl.index if y not in (2008, 2020)]
        calm_bleed = float(yearly_hedge_pnl.loc[calm_years].mean())
        calm_year_bleeds[alloc] = calm_bleed
        pct_positive_calm = float((yearly_hedge_pnl.loc[calm_years] > 0).mean())
        print(f"  STEADY-STATE COST: mean annual hedge-overlay P&L in {len(calm_years)} calm years "
              f"(excl. 2008, 2020) = {calm_bleed*100:+.2f}%/yr ({pct_positive_calm*100:.0f}% of calm years "
              f"the hedge P&L was positive) -- this is the ongoing insurance premium bled in ordinary years.")

        # ---- 2008 and 2020 crisis payoff, quantified ----
        for label, (c0, c1) in [("2008 (full year)", CRISIS_2008), ("2020 (full year)", CRISIS_2020),
                                  ("2020 acute crash (2020-02-19..2020-03-23)", CRISIS_2020_ACUTE)]:
            m = (ret.index >= c0) & (ret.index <= c1)
            spy_seg = spy_only[m]
            hedged_seg = ret[m]
            spy_window_ret = float((1 + spy_seg).prod() - 1)
            hedged_window_ret = float((1 + hedged_seg).prod() - 1)
            offset_pp = (hedged_window_ret - spy_window_ret) * 100
            print(f"  {label}: unhedged SPY {spy_window_ret*100:+.2f}%  |  hedged (alloc {alloc*100:.0f}%) "
                  f"{hedged_window_ret*100:+.2f}%  |  hedge offset {offset_pp:+.2f}pp "
                  f"({'DOES' if offset_pp > 5 else 'does NOT' if offset_pp < 2 else 'PARTIALLY'} "
                  f"meaningfully offset the loss)")

        pool = np.array([s["sharpe"], spy_stats_full["sharpe"]])
        d = deflated_sharpe(s["sharpe"], pool, n_obs=s["n_obs"], ann_factor=BARS_PER_YEAR,
                             skewness=float(ret.dropna().skew()), excess_kurtosis=float(ret.dropna().kurtosis()))
        print(f"  DSR reference (pool=this alloc's Sharpe + unhedged SPY's Sharpe, N=2): {d['dsr']:.4f} "
              f"(E[maxSR]={d['e_max_sr']:.4f})")

        s.update(alloc=alloc, guard_pass=res["guard_pass"], calm_year_bleed_pct=calm_bleed * 100,
                 dsr=d["dsr"], n_trades=len(res["trades"]))
        all_rows.append(s)
        res["trades"].to_csv(RESULTS / f"tail_hedge_otm_puts_trades_alloc{int(alloc*100)}pct.csv", index=False)
        ret.to_csv(RESULTS / f"tail_hedge_otm_puts_daily_ret_alloc{int(alloc*100)}pct.csv")

    pd.DataFrame(all_rows).to_csv(RESULTS / "tail_hedge_otm_puts_summary.csv", index=False)
    print(f"\nSaved: results/tail_hedge_otm_puts_summary.csv, "
          f"tail_hedge_otm_puts_{{trades,daily_ret}}_alloc{{1,2}}pct.csv")


if __name__ == "__main__":
    main()
