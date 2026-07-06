# Factor Report: futures_basis

**Asset:** BTC/USDT  
**Generated:** 2026-07-06 15:36 UTC  
**Verdict:** **KILL**

## Alpha Story

The futures basis (perpetual close - spot close) captures real-time leveraged
demand imbalance. When perp trades above spot, longs are paying a premium to hold
leveraged exposure; when below, shorts are crowded and paying a discount.

Mechanism: an elevated positive basis (longs crowded) closes via three simultaneous
pressures. First, arbitrageurs buy spot and sell perp, purchasing against the trend.
Second, the 8h funding settlement forces longs to pay a cash carry cost proportional
to the basis itself, eroding their position economics. Third, over-leveraged longs
face liquidation cascades when the basis widens beyond their margin threshold.
All three forces apply simultaneously and self-reinforce — the wider the basis, the
stronger the reversion pressure. Mirror logic applies for negative basis.

Who is on the other side: momentum-driven leveraged traders chasing directional
moves on the perp; retail speculators who prefer the perp for instant leverage
access and accept any premium to open; and arb bots (who are self-correcting —
their activity closes the edge, but they exhaust their capital at large spikes).

Why the edge persists at extremes: arb capacity is bounded by balance-sheet
constraints, counterparty limits, and settlement latency between spot and perp.
At large basis spikes (e.g. 1%+ premium), the risk-adjusted return to the arb
deteriorates quickly: the arb requires holding two legs simultaneously with
margin on each, and any directional move that widens the basis before it closes
causes mark-to-market losses. Retail demand sustains the premium past efficient
arb levels for hours to days.

Distinction from perpetual_funding_rate: basis is priced continuously at every
1h bar — it measures current crowding pressure directly. Funding rate is sampled
at 8h settlement intervals and is the exchange mechanism to anchor perp to spot.
The basis is the raw imbalance signal; the funding rate is the lagged correction.
Both reflect the same underlying market structure but basis has 8x more observations
per trading day.

Expected decay: 12-24 months as cross-venue arb infrastructure scales. Data
quality is unimpeachable (5-year OHLCV cache, no revision risk, no look-ahead).
This is a clean re-approach to the carry mechanism visible in perpetual_funding_rate,
on data deep enough to validate properly.

## Distribution Analysis

**Classification:** `continuous_stationary`

**Transform justification:**
Series is stationary (ADF rejects unit root, p <= 0.10). Applied robust rolling z-score (median / MAD x 1.4826) with past-only window. Median/MAD chosen over mean/std to limit sensitivity to transient outlier spikes that are common in derivatives market data.

**Summary statistics:**

| Stat | Value |
|------|-------|
| mean | -5.6781 |
| median | -9.0000 |
| std | 30.8052 |
| skewness | 1.5196 |
| excess_kurtosis | 21.8633 |
| pct_negative | 0.6998 |
| autocorr_lag1 | 0.9297 |
| adf_t | -43.7389 |
| adf_p | 0.0000 |

![Factor distribution](futures_basis/factor_distribution.png)

## Signal Model

spike_capture(z_entry=2.0, z_exit=0.5, window=168)

## Full-sample Backtest Metrics

| Metric | Value |
|--------|-------|
| Sharpe (annualised) | -1.699 |
| Sortino | -1.008 |
| Calmar | nan |
| Max drawdown | 96.8% |
| Hit rate | 39.6% |
| Profit factor | 0.87 |
| Avg turnover / bar | 0.0636 |
| Observations | 52,552 |
| DSR probability | 0.5000 |
| E[max SR] (9 configs) | -1.699 |

## Walk-forward Validation

```
Walk-forward report
====================================================
 Fold  Train bars  Test bars    IS SR   OOS SR
----------------------------------------------------
    0        4152       2160    0.684    0.593
    1        4152       2160    1.867   -2.559
    2        4152       2160   -0.720   -1.459
    3        4152       2160   -1.170    2.984
    4        4152       2160    1.153    0.624
    5        4152       2160    2.564   -0.040
    6        4152       2160   -0.011   -0.450
    7        4152       2160   -0.284    5.053
    8        4152       2160    2.477   -3.320
    9        4152       2160    0.422   -2.473
   10        4152       2160   -2.534   -0.793
   11        4152       2160   -1.089   -1.963
   12        4152       2160   -1.312   -2.865
   13        4152       2160   -1.686    0.619
   14        4152       2160    0.026    0.278
   15        4152       2160    0.147    1.841
   16        4152       2160    1.349   -4.895
   17        4152       2160   -0.699    0.178
   18        4152       2160   -2.188   -0.013
   19        4152       2160    0.456   -5.659
   20        4152       2160    0.134    0.374
   21        4152       2160   -2.060   -7.194
----------------------------------------------------
CV Sharpe (stitched OOS):   -0.258
Max drawdown (OOS):          46.1%
Positive folds:            9/22
IS->OOS degradation:        +0.848
Classification (fold 0):   continuous_stationary
```

![Walk-forward OOS equity](futures_basis/equity_curve.png)

![Per-fold Sharpe](futures_basis/walkforward_folds.png)

## Optimisation

```
Optimisation report
====================================================
Grid shape:     3 x 3  (9 configs)
Threshold:      -0.846
Plateau size:   3 cells
Best params:    {'z_entry': 2.5, 'window': 336}
Best CV Sharpe: -0.258  (raw, pre-DSR)
----------------------------------------------------
Smoothed grid (rows = param1, cols = param2):
       1.5: -1.887   -1.779   -1.651 
       2.0: -1.364   -1.285   -1.175 
       2.5: -0.632   -0.614   -0.546*
                72     168     336
  param2 = window
```


## Verdict: KILL

- CV Sharpe = -0.258 <= 0 (KILL)
- IS->OOS degradation = +0.848 > 0.4 (OVERFIT)
- Positive folds = 9/22 = 41% < 50% (OVERFIT)

**Decision thresholds:**
- Keep: CV Sharpe >= 1.0, positive folds >= 60%, degradation <= 40%
- Overfit flag: IS->OOS degradation > 40%, single-cell plateau, or < 50% positive folds
- Kill: OOS Sharpe <= 0

---
*Generated by crypto-factor-lab research harness*