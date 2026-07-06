# Factor Report: price_momentum_daily

**Asset:** BTC/USDT  
**Generated:** 2026-07-06 17:04 UTC  
**Verdict:** **KILL**

## Alpha Story

Same mechanism as price_momentum (1h): trend continuation from slow
information diffusion and momentum-chasing behavior on BTC/USDT.

This is a diagnostic run, not a new hypothesis. The five 1h kills
(coinbase_premium_gap, perpetual_funding_rate, funding_rate_regime_cond,
futures_basis, price_momentum) could reflect either (a) the factor
mechanisms themselves lack edge, or (b) 1h resolution is the confound —
noise dominates signal at hourly granularity, and 12bp fixed costs eat any
marginal edge in a short holding window. This test isolates which.

At daily (1d) resolution the signal-to-noise ratio is higher: each bar
integrates 24h of price discovery. The holding period for a full MA-cross
cycle is 5-30 bars = 1-4 weeks. The 12bp round-trip cost is amortized over
a longer hold, reducing cost-per-day from 12bp (1h turnover) toward 0.5bp.

Counter-argument: daily crypto momentum is well-documented in academic
literature (Liu, Tsyvinski & Wu 2019; Borri 2019; Cong et al 2021). Every
institutional crypto fund runs daily trend signals. The edge at daily
resolution has had years to be arbed by participants with near-zero costs.

The diagnostic question: if daily kills, the five 1h kills generalize across
timeframe — the factor mechanisms themselves lack edge, and on-chain data is
the justified next spend. If daily shows structure, resolution was the
confound and we have free daily factors to work before spending on Glassnode.

Model: mean_drift (fast/slow MA cross). MA windows scaled to daily
equivalents: fast [5, 10, 20] days, slow [30, 60, 120] days.

## Distribution Analysis

**Classification:** `signed`

**Transform justification:**
Series is signed/bidirectional (mean near 0, ~50% negative values). Applied rolling-median centering + MAD scaling. Symmetric thresholds are valid because positive and negative values have symmetric economic meaning. Robust scaling chosen over mean/std to limit influence of outlier spikes.

**Summary statistics:**

| Stat | Value |
|------|-------|
| mean | 0.0017 |
| median | 0.0006 |
| std | 0.0323 |
| skewness | -0.5795 |
| excess_kurtosis | 13.1839 |
| pct_negative | 0.4886 |
| autocorr_lag1 | -0.0749 |
| adf_t | -50.4191 |
| adf_p | 0.0000 |

![Factor distribution](price_momentum_daily/factor_distribution.png)

## Signal Model

mean_drift(fast=10, slow=60)

## Full-sample Backtest Metrics

| Metric | Value |
|--------|-------|
| Sharpe (annualised) | 0.119 |
| Sortino | 0.166 |
| Calmar | nan |
| Max drawdown | 76.2% |
| Hit rate | 48.0% |
| Profit factor | 1.02 |
| Avg turnover / bar | 0.2287 |
| Observations | 2,191 |
| DSR probability | 0.5000 |
| E[max SR] (9 configs) | 0.119 |

## Walk-forward Validation

```
Walk-forward report
====================================================
 Fold  Train bars  Test bars    IS SR   OOS SR
----------------------------------------------------
    0         490         90    0.792   -0.721
    1         490         90    0.669    1.079
    2         490         90    0.519   -2.437
    3         490         90   -0.088    0.943
    4         490         90   -1.127   -1.398
    5         490         90   -0.600   -3.094
    6         490         90   -0.262    5.067
    7         490         90   -0.050   -2.938
    8         490         90   -0.003   -0.165
    9         490         90    0.293    4.889
   10         490         90   -0.393    0.106
   11         490         90   -0.201   -1.524
   12         490         90   -0.046    2.500
   13         490         90    0.380   -2.653
   14         490         90    0.383    1.364
   15         490         90    0.287   -0.800
   16         490         90   -0.508    1.112
   17         490         90   -0.770   -2.428
----------------------------------------------------
CV Sharpe (stitched OOS):   -0.219
Max drawdown (OOS):          66.9%
Positive folds:            8/18
IS->OOS degradation:        +0.021
Classification (fold 0):   signed
```

![Walk-forward OOS equity](price_momentum_daily/equity_curve.png)

![Per-fold Sharpe](price_momentum_daily/walkforward_folds.png)

## Optimisation

```
Optimisation report
====================================================
Grid shape:     3 x 3  (9 configs)
Threshold:      -0.047
Plateau size:   9 cells
Best params:    {'fast': 20, 'slow': 30}
Best CV Sharpe: -0.219  (raw, pre-DSR)
----------------------------------------------------
Smoothed grid (rows = param1, cols = param2):
         5:  0.017    0.011    0.062 
        10:  0.066    0.044    0.133 
        20:  0.134*   0.089    0.253 
                30      60     120
  param2 = slow
```


## Verdict: KILL

- CV Sharpe = -0.219 <= 0 (KILL)
- Positive folds = 8/18 = 44% < 50% (OVERFIT)

**Decision thresholds:**
- Keep: CV Sharpe >= 1.0, positive folds >= 60%, degradation <= 40%
- Overfit flag: IS->OOS degradation > 40%, single-cell plateau, or < 50% positive folds
- Kill: OOS Sharpe <= 0

---
*Generated by crypto-factor-lab research harness*