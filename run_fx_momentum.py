"""
run_fx_momentum.py — Cross-sectional FX momentum (paperswithbacktest-adjacent
family, same G10 universe/pipeline as FX carry, no new data needed).

MECHANISM (stated a priori, before any result seen): Menkhoff, Sarno, Schmeling
& Schrimpf (2012, "Currency Momentum Strategies", J. Financial Economics)
document that currencies with high trailing returns continue to outperform
currencies with low trailing returns over the next month, across the same
kind of G10+ currency universe used here. Proposed mechanism: slow information
diffusion / gradual capital flows into recently-strong currencies (the same
underlying behavioral story as equity momentum, applied cross-sectionally to
FX), distinct from carry (which sorts on RATE level, not past RETURN).

UNIVERSE: same 9-currency universe as run_fx_carry.py (USD, EUR, GBP, AUD,
NZD, CAD, CHF, JPY, NOK — SEK excluded, no ask-side spot data, see
research/fx_carry_data.py docstring).

SIGNAL: rank currencies by trailing L-month return vs USD; go long the top N,
short the bottom N, equal-weighted, dollar-neutral, rebalanced monthly.

GRID (a priori, no peeking): lookback L in {1, 3, 12} months (the three
standard formation periods in the momentum literature) x leg size N in
{2, 3} (skip N=1, too concentrated/noisy for a 9-asset universe at monthly
resolution — same reasoning already applied in the FX carry N grid) = 6
configs. No other tuning.

COSTS: real Dukascopy daily bid/ask spread paid on portfolio turnover at
each monthly rebalance (reuses fx_carry_data.py's already-computed spread
series — same real cost model as FX carry, no re-verification needed).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from research.fx_carry_data import load_all_fx, currency_return_vs_usd, currency_spread_bps
from research.dsr import deflated_sharpe
from research.backtest import guard_look_ahead, LookAheadError

BARS_PER_YEAR = 12


def build_monthly_returns(daily_ret: pd.DataFrame) -> pd.DataFrame:
    m = daily_ret.copy()
    m.index = m.index.tz_localize(None) if m.index.tz is not None else m.index
    return m.resample("MS").sum()


def build_monthly_spread(daily_spread: pd.DataFrame) -> pd.DataFrame:
    m = daily_spread.copy()
    m.index = m.index.tz_localize(None) if m.index.tz is not None else m.index
    return m.resample("MS").median()


def run_one(monthly_ret: pd.DataFrame, monthly_spread: pd.DataFrame,
            lookback: int, n_leg: int) -> dict:
    idx = monthly_ret.index.intersection(monthly_spread.index).sort_values()
    rets = monthly_ret.reindex(idx)
    spreads = monthly_spread.reindex(idx)
    currencies = list(rets.columns)

    # trailing L-month cumulative log return, known at the START of month t
    # (uses months t-L .. t-1 only — .shift(1) after rolling excludes month t
    # itself, so the signal never sees the return it is about to trade).
    trailing = rets.rolling(lookback).sum().shift(1)

    weights = pd.DataFrame(0.0, index=idx, columns=currencies)
    for t in idx:
        row = trailing.loc[t].dropna()
        if len(row) < 2 * n_leg:
            continue
        ranked = row.sort_values(ascending=False)
        longs = ranked.index[:n_leg]
        shorts = ranked.index[-n_leg:]
        weights.loc[t, longs] = 1.0 / n_leg
        weights.loc[t, shorts] = -1.0 / n_leg

    for cc in currencies:
        try:
            guard_look_ahead(weights[cc], rets[cc], threshold=0.5)
        except LookAheadError as e:
            raise LookAheadError(f"{cc}: {e}")

    gross_ret = (weights.fillna(0) * rets).sum(axis=1)
    turnover = weights.diff().abs().fillna(weights.abs().iloc[0]).sum(axis=1)
    cost = (weights.diff().abs().fillna(weights.abs().iloc[0]) * spreads / 10_000).sum(axis=1)
    net_ret = gross_ret - cost

    equity = (1 + net_ret).cumprod()
    dd = (equity / equity.cummax() - 1)

    def ann_sharpe(r):
        r = r.dropna()
        return float(r.mean() / r.std() * np.sqrt(BARS_PER_YEAR)) if r.std() > 0 and len(r) >= 3 else 0.0

    valid = net_ret.dropna()
    yearly = valid.groupby(valid.index.year).apply(
        lambda r: r.mean() / r.std() * np.sqrt(12) if r.std() > 0 else 0.0
    )

    return {
        "lookback": lookback, "n_leg": n_leg, "n_months": len(valid),
        "gross_sharpe": ann_sharpe(gross_ret), "net_sharpe": ann_sharpe(net_ret),
        "max_dd": float(dd.min()),
        "cagr": float(equity.iloc[-1] ** (12 / len(valid)) - 1) if len(valid) > 0 else 0.0,
        "avg_cost_bps_per_month": float((cost * 10_000).mean()),
        "worst_month_ret": float(net_ret.min()),
        "worst_month_date": str(net_ret.idxmin().date()) if net_ret.notna().any() else None,
        "yearly_sharpe": yearly,
    }


def main():
    print("Loading FX spot (Dukascopy daily bid/ask, reused from FX carry pipeline)...")
    fx = load_all_fx()
    daily_ret = currency_return_vs_usd(fx)
    daily_spread = currency_spread_bps(fx)
    monthly_ret = build_monthly_returns(daily_ret)
    monthly_spread = build_monthly_spread(daily_spread)
    print(f"FX monthly return panel: {monthly_ret.index.min()} to {monthly_ret.index.max()}")

    results = []
    for lookback in (1, 3, 12):
        for n_leg in (2, 3):
            r = run_one(monthly_ret, monthly_spread, lookback, n_leg)
            results.append(r)
            print(f"\n--- L={lookback}mo N={n_leg} ---")
            print(f"  months={r['n_months']}  gross_SR={r['gross_sharpe']:.3f}  "
                  f"net_SR={r['net_sharpe']:.3f}  maxDD={r['max_dd']*100:.1f}%  "
                  f"CAGR={r['cagr']*100:.2f}%  worst_month={r['worst_month_ret']*100:.2f}% "
                  f"on {r['worst_month_date']}")
            pos = int((r['yearly_sharpe'] > 0).sum()); tot = len(r['yearly_sharpe'])
            print(f"  positive years: {pos}/{tot}")

    sharpes = [r["net_sharpe"] for r in results]
    print(f"\n=== Deflated Sharpe (structural pool: family=fx_momentum, this grid only, N={len(results)} trials) ===")
    for r, sr in zip(results, sharpes):
        d = deflated_sharpe(sr, sharpes, n_obs=r["n_months"], ann_factor=BARS_PER_YEAR)
        print(f"  L={r['lookback']} N={r['n_leg']}: net_SR={sr:.3f}  DSR={d['dsr']:.4f}  "
              f"E[max SR|null]={d['e_max_sr']:.3f}  pool_n={d['pool_n']}")

    Path("results").mkdir(exist_ok=True)
    out = pd.DataFrame([{k: v for k, v in r.items() if k != "yearly_sharpe"} for r in results])
    out.to_csv("results/fx_momentum.csv", index=False)
    print("\nSaved results/fx_momentum.csv")
    return results


if __name__ == "__main__":
    main()
