# Factor Report: funding_rate_regime_cond

**Asset:** BTC/USDT  
**Generated:** 2026-07-06 14:51 UTC  
**Verdict:** **OVERFIT (flagged)**

## Alpha Story

Same base mechanism as perpetual_funding_rate: extreme perpetual funding
spikes signal overcrowded positions that mean-revert as carry costs force
de-levering. Hypothesis extension: the edge is conditional on a high realized-
volatility regime. When volatility is elevated — realized vol in the top 50%
of its rolling 336-bar history — crowded longs face larger mark-to-market
losses and are forced to de-lever faster. The reversion is stronger and faster.
In low-volatility regimes the carry cost is tolerable relative to the trend;
longs are not forced out; the mean-reversion signal dissolves.
Observable regime trigger: rolling 336-bar realized volatility of BTC/USDT
1-hour returns, ranked against its own 336-bar rolling percentile history.
Gate opens when that rank >= 0.50 (current vol above the median of recent history).
All regime inputs are past-only and lagged >=1 bar. No calendar date or fold
index is used anywhere in the regime construction.
The real test: if the regime gate correlates strongly with which calendar
periods fall inside the walk-forward folds, it is a calendar proxy, not a
genuine conditional strategy, and must be killed regardless of Sharpe.

## Distribution Analysis

**Classification:** `skewed`

**Transform justification:**
Series is skewed but contains negative values (log1p not applicable). Applied rolling percentile rank rescaled to [-1, +1]. This is distribution-free, robust to any outlier magnitude, and produces a stationary bounded output regardless of the underlying distribution.

**Summary statistics:**

| Stat | Value |
|------|-------|
| mean | 0.0001 |
| median | 0.0001 |
| std | 0.0002 |
| skewness | 3.3424 |
| excess_kurtosis | 37.0357 |
| pct_negative | 0.1227 |
| autocorr_lag1 | 0.9833 |
| adf_t | -21.0538 |
| adf_p | 0.0000 |

![Factor distribution](funding_rate_regime_cond/factor_distribution.png)

## Signal Model

regime_conditional(base=spike_capture(z_entry=1.5, z_exit=0.5, window=336), gate=rv336>=p50%)

## Full-sample Backtest Metrics

| Metric | Value |
|--------|-------|
| Sharpe (annualised) | -0.409 |
| Sortino | -0.239 |
| Calmar | nan |
| Max drawdown | 78.6% |
| Hit rate | 48.4% |
| Profit factor | 0.97 |
| Avg turnover / bar | 0.0091 |
| Observations | 52,552 |
| DSR probability | 0.5000 |
| E[max SR] (9 configs) | -0.409 |

## Walk-forward Validation

```
Walk-forward report
====================================================
 Fold  Train bars  Test bars    IS SR   OOS SR
----------------------------------------------------
    0        4152       2160    0.240   -0.106
    1        4152       2160   -0.875   -0.436
    2        4152       2160    0.233    1.016
    3        4152       2160   -0.603   -0.611
    4        4152       2160   -0.186   -0.660
    5        4152       2160   -0.489   -0.954
    6        4152       2160   -0.875    4.218
    7        4152       2160    1.716    1.732
    8        4152       2160    3.956    0.948
    9        4152       2160    1.118    1.488
   10        4152       2160    0.763    2.107
   11        4152       2160    1.898   -2.388
   12        4152       2160    0.744   -2.510
   13        4152       2160   -1.813   -1.402
   14        4152       2160   -0.686   -1.867
   15        4152       2160   -1.780   -1.116
   16        4152       2160   -1.329   -1.444
   17        4152       2160   -0.238   -1.444
   18        4152       2160   -1.587    1.777
   19        4152       2160    0.000    0.147
   20        4152       2160    0.953   -0.921
   21        4152       2160   -0.331   -1.138
----------------------------------------------------
CV Sharpe (stitched OOS):    0.045
Max drawdown (OOS):          57.8%
Positive folds:            8/22
IS->OOS degradation:        +0.200
Classification (fold 0):   continuous_stationary
```

![Walk-forward OOS equity](funding_rate_regime_cond/equity_curve.png)

![Per-fold Sharpe](funding_rate_regime_cond/walkforward_folds.png)

## Regime Analysis — The Real Test

```
  OOS bars : 47,520 total  |  22,432 in-regime (47.2%)  |  25,088 out-of-regime (52.8%)

  Signal                            In-regime SR  Out-regime SR
  --------------------------------  ------------  -------------
  Ungated spike_capture                   +0.255         +1.008
  Regime-gated (active bars only)         +0.147       (gate=0)

  Regime-coverage / fold-SR corr : -0.176  [OK |r|<=0.5]

  Per-fold breakdown:
   Fold  %In-regime  Ungated OOS SR  Gated OOS SR
  -----  ----------  --------------  ------------
      0       32.5%          +1.045        -0.106
      1       72.7%          -0.980        -0.436
      2       38.1%          +1.511        +1.016
      3       49.6%          +0.186        -0.611
      4       44.0%          +0.574        -0.660
      5       42.6%          +1.385        -0.954
      6       42.9%          +2.727        +4.218
      7       57.7%          +1.983        +1.732
      8       42.7%          +2.548        +0.948
      9       38.9%          +3.135        +1.488
     10       49.5%          +3.115        +2.107
     11       42.1%          -0.768        -2.388
     12       31.0%          -4.429        -2.510
     13       51.6%          -0.503        -1.402
     14       58.2%          -0.687        -1.867
     15       37.1%          +1.314        -1.116
     16       58.6%          -0.367        -1.444
     17       47.2%          -0.701        -1.444
     18       49.1%          +0.104        +1.777
     19       39.7%          +0.873        +0.147
     20       52.1%          -2.975        -0.921
     21       60.6%          -1.079        -1.138

  Interpretation:
  NO GENUINE CONDITIONAL EDGE: regime does not meaningfully discriminate.
  In-regime and out-regime ungated SRs are similar or both non-positive.
  The regime gate does not add value.
```

## Optimisation

```
Optimisation report
====================================================
Grid shape:     3 x 3  (9 configs)
Threshold:      -0.316
Plateau size:   6 cells
Best params:    {'z_entry': 1.5, 'window': 336}
Best CV Sharpe: 0.045  (raw, pre-DSR)
----------------------------------------------------
Smoothed grid (rows = param1, cols = param2):
       1.5: -0.448   -0.248   -0.025*
       2.0: -0.506   -0.283   -0.045 
       2.5: -0.536   -0.283   -0.016 
                72     168     336
  param2 = window
```


## Verdict: OVERFIT (flagged)

- Positive folds = 8/22 = 36% < 50% (OVERFIT)

**Decision thresholds:**
- Keep: CV Sharpe >= 1.0, positive folds >= 60%, degradation <= 40%
- Overfit flag: IS->OOS degradation > 40%, single-cell plateau, or < 50% positive folds
- Kill: OOS Sharpe <= 0

---
*Generated by crypto-factor-lab research harness*