"""
run_fx_carry_em.py — FX carry, emerging-market extension.

WHY: §35 (run_fx_carry.py) found only a weak G10-only carry Sharpe (best 0.228,
DSR 0.559) and attributed the gap to the published 37-year Sharpe 1.74 partly to
a thin G10-only universe with compressed post-GFC ZIRP-era rate dispersion. This
script tests that stated hypothesis directly by adding currencies with genuinely
wide rate dispersion vs G10 (MXN ~11%, ZAR ~8%, ILS/CNH lower but still distinct
regimes) — same mechanism as §35 (UIP failure / forward premium puzzle), same
engine (imports run_fx_carry.run_one/build_monthly_returns/build_monthly_spread
UNCHANGED), only the currency universe changes.

EM UNIVERSE ADDED: only ZAR and CNH (see research/fx_carry_data.py docstring
for the full probe). MXN and ILS were ALSO tried — both have working FRED rate
series and working bid-side spot — but their Dukascopy ASK-side d1 history is
broken (MXN: 0 bytes every year 2010-2025; ILS: data only for 2025), so a real
spread cannot be computed for most of the window and they are dropped, same
policy as SEK in the G10 set. SGD/TRY/PLN/HUF/BRL/INR/KRW/THB/CZK/RUB were also
probed and excluded (no rate series, or discontinuous/nonexistent FX data).
**This is a narrow 2-currency EM extension, not a broad institutional-style EM
basket** — a real scope limitation of this project's free-data/single-broker
constraint, stated up front, not discovered post-hoc. CNH caveat restated:
PBOC manages the RMB via a daily fixing + trading band; offshore CNH "carry"
may partly reflect currency policy rather than a pure market risk premium, and
its bid-side coverage is sparser than its ask-side over the same span (1,723
vs 4,215 days) — fewer usable trading days than the calendar span suggests.

TWO RUNS (a priori, both genuinely informative, neither post-hoc):
  (A) EM-ONLY basket: USD + ZAR + CNH (3 currencies). Directly answers "does
      an EM-only carry basket work" — the user's literal question. Only
      N=1 is feasible (2*N<=3 caps N at 1 for a 3-asset universe).
  (B) COMBINED G10+EM broad universe: USD + 8 G10 (§35's set, minus SEK) + 2 EM
      = 11 currencies. Closer to the actual "Good Carry, Bad Carry"-style broad
      global carry replication (that literature does not segregate G10 vs EM).
      N in {1, 2, 3, 4}.

Total 5 new trials, single family "fx_carry_em", deflated together (not mixed
with §35's G10-only pool — different family per CLAUDE.md structural_pool rule).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from research.fx_carry_data import (
    load_all_rates, rates_available_at, load_all_fx,
    currency_return_vs_usd, currency_spread_bps,
    RATE_FILES, FX_PAIRS, EM_RATE_FILES, EM_FX_PAIRS,
)
from research.dsr import deflated_sharpe
from run_fx_carry import run_one, build_monthly_returns, build_monthly_spread, BARS_PER_YEAR


def load_universe(rate_files, fx_pairs):
    rates_raw = load_all_rates(rate_files)
    rates_avail = rates_available_at(rates_raw)
    fx = load_all_fx(fx_pairs)
    daily_ret = currency_return_vs_usd(fx)
    daily_spread = currency_spread_bps(fx)
    monthly_ret = build_monthly_returns(daily_ret)
    monthly_spread = build_monthly_spread(daily_spread)
    return rates_avail, monthly_ret, monthly_spread


def run_grid(label, rate_files, fx_pairs, n_grid):
    print(f"\n============ {label} ============")
    rates_avail, monthly_ret, monthly_spread = load_universe(rate_files, fx_pairs)
    print(f"Currencies ({len(rate_files)}): {sorted(rate_files)}")
    print(f"Rate panel: {rates_avail.index.min()} to {rates_avail.index.max()}")
    print(f"FX monthly return panel: {monthly_ret.index.min()} to {monthly_ret.index.max()}")

    results = []
    for n_leg in n_grid:
        r = run_one(rates_avail, monthly_ret, monthly_spread, n_leg)
        r["label"] = label
        results.append(r)
        print(f"\n--- {label} N={n_leg} ---")
        print(f"  months={r['n_months']}  gross_SR={r['gross_sharpe']:.3f}  "
              f"net_SR={r['net_sharpe']:.3f}  maxDD={r['max_dd']*100:.1f}%  "
              f"CAGR={r['cagr']*100:.2f}%")
        print(f"  avg_cost={r['avg_cost_bps_per_month']:.2f} bps/mo  "
              f"worst_month={r['worst_month_ret']*100:.2f}% on {r['worst_month_date']}")
        pos_years = int((r["yearly_sharpe"] > 0).sum())
        tot_years = len(r["yearly_sharpe"])
        print(f"  positive years: {pos_years}/{tot_years}")
        print(f"  yearly Sharpe:\n{r['yearly_sharpe'].round(2).to_string()}")
    return results


def main():
    em_only_rates = {"USD": RATE_FILES["USD"], **EM_RATE_FILES}
    em_only_fx = dict(EM_FX_PAIRS)

    combined_rates = {**RATE_FILES, **EM_RATE_FILES}
    combined_fx = {**FX_PAIRS, **EM_FX_PAIRS}

    results = []
    results += run_grid("EM-ONLY (USD+ZAR+CNH)", em_only_rates, em_only_fx, (1,))
    results += run_grid("COMBINED G10+EM (11 currencies)", combined_rates, combined_fx, (1, 2, 3, 4))

    sharpes = [r["net_sharpe"] for r in results]
    print(f"\n=== Deflated Sharpe (structural pool: family=fx_carry_em, this session's grid only, N={len(results)} trials) ===")
    for r, sr in zip(results, sharpes):
        d = deflated_sharpe(sr, sharpes, n_obs=r["n_months"], ann_factor=BARS_PER_YEAR)
        print(f"  {r['label']} N={r['n_leg']}: net_SR={sr:.3f}  DSR={d['dsr']:.4f}  "
              f"E[max SR|null]={d['e_max_sr']:.3f}  pool_n={d['pool_n']}")

    Path("results").mkdir(exist_ok=True)
    out = pd.DataFrame([{k: v for k, v in r.items() if k not in ("yearly_sharpe", "net_ret", "equity")}
                         for r in results])
    out.to_csv("results/fx_carry_em.csv", index=False)
    print("\nSaved results/fx_carry_em.csv")
    return results


if __name__ == "__main__":
    main()
