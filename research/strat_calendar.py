#!/usr/bin/env python3
"""
STRATEGY 4 -- CALENDAR/SEASONALITY ON RAW PRICE. Three named, documented
effects, tested on SPX500 (the canonical domain for all three -- equity
index seasonality) and BTCUSDT (a genuinely different asset class, no
prior reason to expect the SAME calendar effects, run as a second check).

EFFECTS, stated before any test:
  1. SANTA CLAUS RALLY: long-only, last 5 trading days of December +
     first 2 trading days of January (the standard Yale Hirsch definition).
  2. SELL IN MAY: long Nov 1 -> Apr 30, flat May 1 -> Oct 31 (the standard
     "Halloween indicator" definition).
  3. TURN-OF-MONTH: long the LAST trading day of each month + the first 3
     trading days of the next month (the standard documented window).

DISCIPLINE, stated up front per the task's explicit instruction (same
standard as the on-chain / cross-asset lead-lag sections of this project):
a SIGNIFICANCE TEST runs BEFORE any tradeable rule is built. For each
effect, the mean daily return on effect-days is compared against the mean
daily return on ALL OTHER days using a two-sample t-test (Welch's,
unequal variance) AND against 10,000 bootstrap resamples of random days of
the same COUNT (not just the same total average) as the actual effect-day
count in that year, to see whether the effect's real calendar structure
does anything a same-sized random-day sample doesn't already do. An
effect only proceeds to a compounded backtest if it is significant at
p<0.05 on the SAME instrument/window under BOTH tests. If not, this is
stated as a clean non-finding and NO tradeable rule is forced onto it,
per the task's explicit instruction.

DATA: SPX500 (2017-2025 daily, from the project's own Dukascopy M1) and
BTCUSDT (2018-2026 daily, from Binance H1). Both real spread-inclusive.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
from scipy import stats

from research.six_strategies_engine import (
    load_daily, drawdown_with_recovery, year_table, top_year_concentration,
    START_CAP, BARS_PER_YEAR,
)
from research.metrics import sharpe, max_drawdown, profit_factor

RNG = np.random.default_rng(20260907)
N_BOOTSTRAP = 10_000


def santa_claus_days(idx: pd.DatetimeIndex) -> pd.Series:
    flag = pd.Series(False, index=idx)
    for yr in sorted(set(idx.year)):
        dec = idx[(idx.year == yr) & (idx.month == 12)]
        jan = idx[(idx.year == yr + 1) & (idx.month == 1)]
        if len(dec) >= 5:
            flag.loc[dec[-5:]] = True
        if len(jan) >= 2:
            flag.loc[jan[:2]] = True
    return flag


def sell_in_may_days(idx: pd.DatetimeIndex) -> pd.Series:
    return pd.Series(idx.month.isin([11, 12, 1, 2, 3, 4]), index=idx)


def turn_of_month_days(idx: pd.DatetimeIndex) -> pd.Series:
    flag = pd.Series(False, index=idx)
    months = sorted(set(zip(idx.year, idx.month)))
    for (yr, mo) in months:
        this_m = idx[(idx.year == yr) & (idx.month == mo)]
        if len(this_m):
            flag.loc[this_m[-1]] = True   # last day of this month
            flag.loc[this_m[:3]] = True   # first 3 days of this month (as "next month" for the PRIOR month's last day)
    return flag


def significance_test(ret: pd.Series, effect_days: pd.Series, label: str) -> dict:
    on = ret[effect_days.reindex(ret.index, fill_value=False)]
    off = ret[~effect_days.reindex(ret.index, fill_value=False)]
    if len(on) < 20:
        return dict(label=label, n_on=len(on), significant=False, reason="too few effect-days")

    t_stat, t_p = stats.ttest_ind(on, off, equal_var=False)

    n_on = len(on)
    all_vals = ret.to_numpy()
    boot_means = np.empty(N_BOOTSTRAP)
    for b in range(N_BOOTSTRAP):
        sample = RNG.choice(all_vals, size=n_on, replace=False)
        boot_means[b] = sample.mean()
    actual_mean = on.mean()
    boot_p = float((np.abs(boot_means - all_vals.mean()) >= np.abs(actual_mean - all_vals.mean())).mean())

    significant = bool(t_p < 0.05 and boot_p < 0.05)
    return dict(label=label, n_on=n_on, mean_on=float(actual_mean), mean_off=float(off.mean()),
                t_stat=float(t_stat), t_p=float(t_p), boot_p=boot_p, significant=significant)


def compound_effect(daily: pd.DataFrame, effect_days: pd.Series) -> dict:
    close = daily["close"]
    ret = close.pct_change().fillna(0.0)
    pos = effect_days.reindex(daily.index, fill_value=False).astype(int)
    pos_prev = pos.shift(1).fillna(0)
    changed = pos != pos_prev
    cost = (daily["spread_bps"].reindex(daily.index).fillna(daily["spread_bps"].median()) / 1e4) * changed.astype(float)
    strat_ret = pos_prev * ret - cost
    equity = START_CAP * (1.0 + strat_ret).cumprod()
    return dict(daily_ret=strat_ret, equity=equity)


def report_compounded(label: str, daily: pd.DataFrame, effect_days: pd.Series) -> None:
    out = compound_effect(daily, effect_days)
    daily_ret, equity = out["daily_ret"], out["equity"]
    dd = drawdown_with_recovery(equity)
    yt = year_table(daily_ret, equity)
    conc = top_year_concentration(yt)
    end_bal = float(equity.iloc[-1])
    bh_ret = daily["close"].pct_change().dropna()
    bh_eq = (1 + bh_ret).cumprod() * START_CAP

    W = 112
    print("=" * W)
    print(f"  {label} -- COMPOUNDED BACKTEST (significance confirmed, see above)")
    print("=" * W)
    for _, row in yt.iterrows():
        print(f"  {int(row['year']):<6} {row['start_equity']:>14,.0f} {row['end_equity']:>14,.0f} "
              f"{row['year_return_pct']:>+13.1f}%")
    print(f"\n  FULL-PERIOD: ${START_CAP:,.0f} -> ${end_bal:,.0f} ({(end_bal/START_CAP-1)*100:+.1f}%)   "
          f"Sharpe {sharpe(daily_ret, BARS_PER_YEAR):+.2f}   net PF {profit_factor(daily_ret):.3f}")
    print(f"  MAX DRAWDOWN: {dd['max_dd']*100:.1f}%  (peak {dd['peak_date'].date()}, trough {dd['trough_date'].date()}"
          + (f", recovered {dd['recovery_date'].date()})" if dd["recovery_date"] is not None else ", NOT recovered)"))
    conc_str = f"{conc*100:.0f}%" if np.isfinite(conc) else "n/a (total<=0)"
    print(f"  TOP-YEAR CONCENTRATION: {conc_str}")
    print(f"  BUY-AND-HOLD over same span: ${float(bh_eq.iloc[-1]):,.0f} ({(float(bh_eq.iloc[-1])/START_CAP-1)*100:+.1f}%)")
    print()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("STRATEGY 4 -- CALENDAR/SEASONALITY, significance test BEFORE any backtest\n")

    for inst in ["SPX500", "BTCUSDT"]:
        daily = load_daily(inst)
        ret = daily["close"].pct_change().dropna()
        idx = ret.index
        print(f"\n{'#'*112}\n  {inst}  ({idx.min().date()} -> {idx.max().date()}, {len(ret)} trading days)\n{'#'*112}")

        effects = {
            "Santa Claus rally": santa_claus_days(idx),
            "Sell in May (long Nov-Apr)": sell_in_may_days(idx),
            "Turn-of-month": turn_of_month_days(idx),
        }
        any_significant = False
        for name, days in effects.items():
            res = significance_test(ret, days, name)
            print(f"\n  [{name}] n_on={res.get('n_on')}", end="")
            if "reason" in res:
                print(f"  -- {res['reason']}, SKIPPED")
                continue
            print(f"  mean_on={res['mean_on']*100:+.4f}%/day  mean_off={res['mean_off']*100:+.4f}%/day")
            print(f"    Welch t-test: t={res['t_stat']:+.2f}, p={res['t_p']:.4f}")
            print(f"    Bootstrap ({N_BOOTSTRAP} resamples of same-size random-day baskets): p={res['boot_p']:.4f}")
            if res["significant"]:
                print(f"    -> SIGNIFICANT at p<0.05 on BOTH tests. Proceeding to compounded backtest.")
                any_significant = True
                report_compounded(f"{inst} -- {name}", daily, days)
            else:
                print(f"    -> NOT significant on both tests. NO tradeable rule built -- clean non-finding, stated plainly.")
        if not any_significant:
            print(f"\n  {inst}: NONE of the three named effects passed both significance tests. "
                  f"No backtest was forced on a non-finding for this instrument.")


if __name__ == "__main__":
    main()
