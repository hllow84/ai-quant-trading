# Factor Report: price_momentum

**Asset:** BTC/USDT  
**Generated:** 2026-07-06 16:23 UTC  
**Verdict:** **KILL**

## Alpha Story

Price momentum on hourly BTC: trend continuation from slow information
diffusion and momentum-chasing behavior.

Mechanism: when a genuine catalyst (macro news, ETF inflows, protocol event)
hits the market, not all participants react simultaneously. Slower participants
— retail, family offices, smaller funds — receive, process, and act on
information over hours to days rather than milliseconds. This creates a
predictable drift in the direction of the initial move. Compounding this,
trend-following systematic strategies and discretionary momentum traders
explicitly buy strength and sell weakness, creating a self-reinforcing
dynamic in the short run. Leveraged longs facing margin calls in a downtrend
also create forced selling that continues the trend past the point where
fundamentals justify it.

Who is on the other side: (1) mean-reversion market-makers who provide
liquidity and lose directionally when a trend materializes; (2) value-oriented
investors buying into weakness; (3) the general pool of liquidity providers
who take the other side of trend trades at the quoted spread.

Why it might persist: behavioral biases (anchoring, herding) are stable human
traits. Forced liquidations from over-leveraged positions amplify trends beyond
rational levels. Regulatory fragmentation slows capital allocation globally.

Honest prior: price momentum is the most crowded, most documented factor in
finance. The 12-1 month anomaly has been in academic literature since Jegadeesh
and Titman (1993). Crypto-specific momentum is covered in every factor survey
since 2018. Free OHLCV at 1h resolution is available to every participant on
Earth. Every quant trading firm has run MA-cross momentum on hourly crypto data.
The prior probability of finding a genuine, cost-inclusive edge on free 1h data
is very low — this is the closing test on the free price/derivatives surface.

Model matched to mechanism: mean_drift (fast/slow MA cross), not spike_capture.
Momentum is a drift signal — a sustained directional tendency — not a spike-and-
revert. MA cross is the canonical operator for detecting sustained drift.

## Distribution Analysis

**Classification:** `signed`

**Transform justification:**
Series is signed/bidirectional (mean near 0, ~50% negative values). Applied rolling-median centering + MAD scaling. Symmetric thresholds are valid because positive and negative values have symmetric economic meaning. Robust scaling chosen over mean/std to limit influence of outlier spikes.

**Summary statistics:**

| Stat | Value |
|------|-------|
| mean | 0.0001 |
| median | 0.0001 |
| std | 0.0067 |
| skewness | -0.4233 |
| excess_kurtosis | 48.3639 |
| pct_negative | 0.4918 |
| autocorr_lag1 | -0.0225 |
| adf_t | -234.4467 |
| adf_p | 0.0000 |

![Factor distribution](price_momentum/factor_distribution.png)

## Signal Model

mean_drift(fast=24, slow=168)

## Full-sample Backtest Metrics

| Metric | Value |
|--------|-------|
| Sharpe (annualised) | -2.528 |
| Sortino | -3.403 |
| Calmar | nan |
| Max drawdown | 100.0% |
| Hit rate | 46.4% |
| Profit factor | 0.91 |
| Avg turnover / bar | 0.1588 |
| Observations | 52,552 |
| DSR probability | 0.5000 |
| E[max SR] (9 configs) | -2.528 |

## Walk-forward Validation

```
Walk-forward report
====================================================
 Fold  Train bars  Test bars    IS SR   OOS SR
----------------------------------------------------
    0        4152       2160   -0.097   -0.938
    1        4152       2160   -1.372    0.568
    2        4152       2160    0.370   -0.151
    3        4152       2160    0.317   -1.408
    4        4152       2160   -0.741   -3.648
    5        4152       2160   -1.776   -1.484
    6        4152       2160   -2.351   -1.995
    7        4152       2160   -2.240   -2.017
    8        4152       2160   -2.163   -1.705
    9        4152       2160   -1.002   -2.733
   10        4152       2160   -1.442   -0.117
   11        4152       2160   -2.171   -3.400
   12        4152       2160   -2.052   -4.788
   13        4152       2160   -5.011   -0.755
   14        4152       2160   -3.725   -3.149
   15        4152       2160   -1.701   -2.967
   16        4152       2160   -3.776    1.026
   17        4152       2160   -1.725    0.036
   18        4152       2160    0.386   -4.385
   19        4152       2160   -2.338   -3.483
   20        4152       2160   -5.100   -5.246
   21        4152       2160   -3.979    0.869
----------------------------------------------------
CV Sharpe (stitched OOS):   -1.642
Max drawdown (OOS):          99.8%
Positive folds:            4/22
IS->OOS degradation:        -0.083
Classification (fold 0):   signed
```

![Walk-forward OOS equity](price_momentum/equity_curve.png)

![Per-fold Sharpe](price_momentum/walkforward_folds.png)

## Optimisation

```
Optimisation report
====================================================
Grid shape:     3 x 3  (9 configs)
Threshold:      -2.680
Plateau size:   2 cells
Best params:    {'fast': 48, 'slow': 336}
Best CV Sharpe: -1.642  (raw, pre-DSR)
----------------------------------------------------
Smoothed grid (rows = param1, cols = param2):
        12: -3.677   -3.635   -3.574 
        24: -3.287   -3.163   -2.930 
        48: -2.818   -2.675   -2.380*
                72     168     336
  param2 = slow
```


## Verdict: KILL

- CV Sharpe = -1.642 <= 0 (KILL)
- Positive folds = 4/22 = 18% < 50% (OVERFIT)

**Decision thresholds:**
- Keep: CV Sharpe >= 1.0, positive folds >= 60%, degradation <= 40%
- Overfit flag: IS->OOS degradation > 40%, single-cell plateau, or < 50% positive folds
- Kill: OOS Sharpe <= 0

---
*Generated by crypto-factor-lab research harness*