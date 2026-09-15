"""
run_fx_carry.py — FX carry trade: "Good Carry, Bad Carry" family
(paperswithbacktest candidate #1, notes/paperswithbacktest_candidates.md).

MECHANISM (stated a priori, before any result seen):
Uncovered interest rate parity (UIP) predicts high-rate currencies should
depreciate enough to offset their rate advantage, leaving zero expected excess
return. Empirically UIP fails (the "forward premium puzzle" / Fama 1984): high
interest rate currencies do NOT depreciate enough on average, so a strategy that
goes long high-rate currencies and short low-rate currencies earns a positive
average excess return. This is one of the most replicated anomalies in
international finance (Lustig & Verdelhan 2007; the paperswithbacktest
"Good Carry, Bad Carry" replication reports Sharpe 1.74 gross over 37 years).
Crash risk (carry unwinds violently in risk-off episodes, e.g. 2008, Aug 2024
JPY unwind) is the standard proposed compensation for the premium.

UNIVERSE: USD, EUR, GBP, AUD, NZD, CAD, CHF, JPY, NOK, SEK (10 G10 currencies).
RATE: FRED IR3TIB01 (OECD 3-month interbank), monthly, 2-month publication lag.
SIGNAL: rank currencies by lagged short rate; go long the top N, short the
bottom N, equal-weighted, dollar-neutral, rebalanced monthly.
COSTS: real Dukascopy daily bid/ask spread paid on every unit of turnover at
rebalance. No leverage, no forward/swap data — carry accrual is proxied by
(foreign rate - USD rate)/12 added directly to the monthly return, which is the
standard covered-interest-parity-consistent proxy used in the academic carry
literature (Fama regression framing) given no NDF/swap points are available
here. This is stated as a methodological limitation, not hidden.

GRID (a priori, no peeking): N (long/short leg size) in {1, 2, 3} = 3 configs.
Weekly rebalance is NOT tested — rate data is monthly, so higher-frequency
rebalancing only adds turnover cost with no new information.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from research.fx_carry_data import (
    load_all_rates, rates_available_at, load_all_fx,
    currency_return_vs_usd, currency_spread_bps, PUBLICATION_LAG_MONTHS,
)
from research.dsr import deflated_sharpe, structural_pool
from research.backtest import guard_look_ahead, LookAheadError

BARS_PER_YEAR = 12  # monthly rebalance/return series


def build_monthly_returns(daily_ret: pd.DataFrame) -> pd.DataFrame:
    """Compound daily currency-vs-USD log returns to calendar-month log returns."""
    m = daily_ret.copy()
    m.index = m.index.tz_localize(None) if m.index.tz is not None else m.index
    monthly = m.resample("MS").sum()  # sum of log returns = log of compounded return
    return monthly


def build_monthly_spread(daily_spread: pd.DataFrame) -> pd.DataFrame:
    """Median daily spread within each month, in bps — the cost paid at rebalance."""
    m = daily_spread.copy()
    m.index = m.index.tz_localize(None) if m.index.tz is not None else m.index
    return m.resample("MS").median()


def run_one(rate_avail: pd.DataFrame, monthly_ret: pd.DataFrame,
            monthly_spread: pd.DataFrame, n_leg: int) -> dict:
    idx = monthly_ret.index.intersection(rate_avail.index)
    idx = idx.intersection(monthly_spread.index)
    idx = idx.sort_values()

    rates = rate_avail.reindex(idx)
    rets = monthly_ret.reindex(idx)
    spreads = monthly_spread.reindex(idx)

    currencies = list(rates.columns)
    weights = pd.DataFrame(0.0, index=idx, columns=currencies)

    for t in idx:
        row = rates.loc[t].dropna()
        if len(row) < 2 * n_leg:
            continue
        ranked = row.sort_values(ascending=False)
        longs = ranked.index[:n_leg]
        shorts = ranked.index[-n_leg:]
        weights.loc[t, longs] = 1.0 / n_leg
        weights.loc[t, shorts] = -1.0 / n_leg

    # Signal is the rank-derived weight computed from rates known at START of
    # month t (already lagged PUBLICATION_LAG_MONTHS months upstream). Apply
    # the standard 1-BAR additional lag: trade on last month's weights this
    # month, so month t's weight (formed from data known at start of t) is
    # applied to month t's return, not shifted further — the publication lag
    # already prevents look-ahead. We do NOT shift again here because
    # rates_available_at() already encodes "what was known at t".
    port_weights = weights

    # look-ahead guard: rate signal (rank position, using AVAILABLE-at-t rates)
    # must not be suspiciously correlated with the SAME/NEXT month return it's
    # trading. Use total portfolio weight-times-return relationship per currency.
    for cc in currencies:
        try:
            guard_look_ahead(port_weights[cc], rets[cc], threshold=0.5)
        except LookAheadError as e:
            raise LookAheadError(f"{cc}: {e}")

    # Carry accrual: (foreign monthly rate - USD monthly rate), using the SAME
    # lagged/available rate that generated the ranking (no extra look-ahead).
    rate_diff = rates.sub(rates["USD"], axis=0) / 100 / 12

    # No extra shift here: rates_avail already encodes "known at the START of
    # month t" (via the 2-month publication lag applied upstream), so the
    # weight decided for month t, formed from that already-lagged rate, is
    # legitimately tradeable AT the start of month t and held through it.
    gross_leg_ret = port_weights.fillna(0) * (rets + rate_diff)
    gross_ret = gross_leg_ret.sum(axis=1)

    turnover = port_weights.diff().abs().fillna(port_weights.abs().iloc[0]).sum(axis=1)
    cost_bps = (port_weights.diff().abs().fillna(port_weights.abs().iloc[0]) * spreads / 10_000).sum(axis=1)
    net_ret = gross_ret - cost_bps

    equity = (1 + net_ret).cumprod()
    running_max = equity.cummax()
    dd = (equity / running_max - 1)
    max_dd = float(dd.min())

    def ann_sharpe(r):
        r = r.dropna()
        if r.std() == 0 or len(r) < 3:
            return 0.0
        return float(r.mean() / r.std() * np.sqrt(BARS_PER_YEAR))

    gross_sharpe = ann_sharpe(gross_ret)
    net_sharpe = ann_sharpe(net_ret)

    # per-year Sharpe concentration
    yearly = net_ret.groupby(net_ret.index.year).apply(
        lambda r: r.mean() / r.std() * np.sqrt(12) if r.std() > 0 else 0.0
    )

    # worst single month (carry-style tail risk, per CLAUDE.md standing rule)
    worst_month = float(net_ret.min())
    worst_month_date = net_ret.idxmin()

    return {
        "n_leg": n_leg,
        "n_months": len(idx),
        "gross_sharpe": gross_sharpe,
        "net_sharpe": net_sharpe,
        "max_dd": max_dd,
        "cagr": float(equity.iloc[-1] ** (12 / len(idx)) - 1) if len(idx) > 0 else 0.0,
        "avg_turnover": float(turnover.mean()),
        "avg_cost_bps_per_month": float((cost_bps * 10_000).mean()),
        "worst_month_ret": worst_month,
        "worst_month_date": str(worst_month_date.date()) if pd.notna(worst_month_date) else None,
        "yearly_sharpe": yearly,
        "net_ret": net_ret,
        "equity": equity,
    }


def main():
    print("Loading rates (FRED, monthly, 2-month publication lag)...")
    rates_raw = load_all_rates()
    rates_avail = rates_available_at(rates_raw)

    print("Loading FX spot (Dukascopy daily bid/ask)...")
    fx = load_all_fx()
    daily_ret = currency_return_vs_usd(fx)
    daily_spread = currency_spread_bps(fx)

    monthly_ret = build_monthly_returns(daily_ret)
    monthly_spread = build_monthly_spread(daily_spread)

    print(f"Rate panel: {rates_avail.index.min()} to {rates_avail.index.max()}, "
          f"{rates_avail.shape[1]} currencies")
    print(f"FX monthly return panel: {monthly_ret.index.min()} to {monthly_ret.index.max()}")

    results = []
    for n_leg in (1, 2, 3):
        r = run_one(rates_avail, monthly_ret, monthly_spread, n_leg)
        results.append(r)
        print(f"\n--- N={n_leg} (long top {n_leg}, short bottom {n_leg} of 10) ---")
        print(f"  months={r['n_months']}  gross_SR={r['gross_sharpe']:.3f}  "
              f"net_SR={r['net_sharpe']:.3f}  maxDD={r['max_dd']*100:.1f}%  "
              f"CAGR={r['cagr']*100:.2f}%")
        print(f"  avg_cost={r['avg_cost_bps_per_month']:.2f} bps/mo  "
              f"worst_month={r['worst_month_ret']*100:.2f}% on {r['worst_month_date']}")
        pos_years = int((r["yearly_sharpe"] > 0).sum())
        tot_years = len(r["yearly_sharpe"])
        print(f"  positive years: {pos_years}/{tot_years}")
        print(f"  yearly Sharpe:\n{r['yearly_sharpe'].round(2).to_string()}")

    sharpes = [r["net_sharpe"] for r in results]
    print("\n=== Deflated Sharpe (structural pool: family=fx_carry, this grid only, N=3 trials) ===")
    for r, sr in zip(results, sharpes):
        d = deflated_sharpe(sr, sharpes, n_obs=r["n_months"], ann_factor=BARS_PER_YEAR)
        print(f"  N={r['n_leg']}: net_SR={sr:.3f}  DSR={d['dsr']:.4f}  "
              f"E[max SR|null]={d['e_max_sr']:.3f}  pool_n={d['pool_n']}")

    Path("results").mkdir(exist_ok=True)
    out = pd.DataFrame([{k: v for k, v in r.items() if k not in ("yearly_sharpe", "net_ret", "equity")}
                         for r in results])
    out.to_csv("results/fx_carry.csv", index=False)
    print("\nSaved results/fx_carry.csv")

    return results


if __name__ == "__main__":
    main()
