"""
preprocess.py — Distribution-aware factor preprocessing (spec §5).

Classifies a raw factor series into one of four types and applies the
corresponding normalisation transform. All rolling operations are past-only
(no center=True, explicit min_periods, no look-ahead by construction).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from scipy import stats as _scipy_stats
    _SCIPY = True
except ImportError:
    _SCIPY = False


# ── ADF helper ────────────────────────────────────────────────────────────────

def _adf_stat(series: pd.Series) -> tuple[float, float]:
    """
    Simplified OLS-based ADF test (constant, no trend, zero augmentation lags).
    Returns (t_statistic, p_value).  p < 0.05 ≈ stationary.

    This is a research-grade heuristic.  For production use statsmodels adfuller.
    H0: γ = 0 (unit root).  Reject H0 (small p) → stationary.
    """
    s = series.dropna().values.astype(float)
    n = len(s)
    if n < 10:
        return 0.0, 1.0

    dy    = np.diff(s)
    y_lag = s[:-1]
    X     = np.column_stack([np.ones(len(y_lag)), y_lag])

    try:
        coef, _, _, _ = np.linalg.lstsq(X, dy, rcond=None)
    except np.linalg.LinAlgError:
        return 0.0, 1.0

    gamma = coef[1]
    res   = dy - X @ coef
    df    = len(dy) - 2
    if df < 1:
        return 0.0, 1.0

    s2 = float((res @ res) / df)
    try:
        XtX_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError:
        return 0.0, 1.0

    se = float(np.sqrt(max(s2 * XtX_inv[1, 1], 1e-12)))
    t  = float(gamma / se)

    if _SCIPY:
        p = float(_scipy_stats.t.cdf(t, df=df))
    else:
        # Sigmoid fallback when scipy absent (one-tailed, rough approximation)
        p = float(1.0 / (1.0 + np.exp(0.8 * t))) if t < 0 else 0.5
    return t, p


# ── Rolling helpers ───────────────────────────────────────────────────────────

def _rolling_mad(s: pd.Series, window: int, min_periods: int) -> pd.Series:
    """
    Rolling Median Absolute Deviation (past-only).
    Second rolling uses min_periods=1 so MAD warmup equals the first roll's warmup,
    not 2× it.
    """
    roll_med = s.rolling(window, min_periods=min_periods).median()
    return (s - roll_med).abs().rolling(window, min_periods=1).median()


def _rolling_pctrank(s: pd.Series, window: int, min_periods: int) -> pd.Series:
    """
    Rolling percentile rank of the current value against the previous `window` values.
    Output in [0, 1].  O(N × window) — acceptable for a research harness.
    """
    return s.rolling(window, min_periods=min_periods).apply(
        lambda x: float((x[:-1] < x[-1]).mean()) if len(x) > 1 else 0.5,
        raw=True,
    )


# ── Classification ────────────────────────────────────────────────────────────

CLASSES: tuple[str, ...] = (
    "skewed",
    "signed",
    "continuous_nonstationary",
    "continuous_stationary",
)


def classify(factor: pd.Series) -> tuple[str, dict]:
    """
    Classify a raw factor series into one of four types (spec §5.1).

    Decision order (first match wins):
      1. Skewed/fat-tailed — high positive skew + mostly positive values.
      2. Signed/bidirectional — centred near 0, ~50% negative values.
      3. Non-stationary — ADF fails to reject unit root (p > 0.10).
      4. Stationary — default.

    Returns
    -------
    (label, stats)
        label : one of CLASSES
        stats : dict of summary statistics used in the classification decision
    """
    s = factor.dropna()
    if len(s) < 30:
        raise ValueError(
            f"Factor series too short to classify ({len(s)} obs < 30 minimum)."
        )

    mean     = float(s.mean())
    median   = float(s.median())
    std      = float(s.std(ddof=1))
    skewness = float(s.skew())
    kurt     = float(s.kurtosis())
    pct_neg  = float((s < 0).mean())
    autocorr = float(s.autocorr(1)) if len(s) > 2 else 0.0
    adf_t, adf_p = _adf_stat(s)

    stats = dict(
        mean=mean, median=median, std=std,
        skewness=skewness, excess_kurtosis=kurt,
        pct_negative=pct_neg, autocorr_lag1=autocorr,
        adf_t=adf_t, adf_p=adf_p,
    )

    # 1. Skewed / fat-tailed / log-normal: high positive skew, mostly positive
    if skewness > 2.0 and pct_neg < 0.20:
        return "skewed", stats

    # 2. Signed / bidirectional: symmetric around zero, sign carries meaning.
    #    Autocorrelation guard excludes mean-reverting AR(1) series (e.g. funding rate)
    #    which are centred near zero but classified as continuous_stationary.
    if 0.30 <= pct_neg <= 0.70 and std > 0 and abs(mean / std) < 0.5 and abs(autocorr) < 0.5:
        return "signed", stats

    # 3. Continuous, non-stationary: ADF fails to reject unit root
    if adf_p > 0.10:
        return "continuous_nonstationary", stats

    # 4. Default: stationary, bounded-ish
    return "continuous_stationary", stats


# ── Transform ─────────────────────────────────────────────────────────────────

def transform(
    factor: pd.Series,
    classification: str,
    window: int = 168,
) -> tuple[pd.Series, str]:
    """
    Apply the distribution-appropriate normalisation transform (spec §5.2).

    Parameters
    ----------
    factor         : raw factor series (any index)
    classification : one of CLASSES, typically from classify()
    window         : lookback for rolling statistics (bars; 168 ≈ 1 week hourly)

    Returns
    -------
    (normalised, justification)
        normalised    : past-only normalised factor, same index as factor
        justification : written explanation tying the transform to the classification
    """
    if classification not in CLASSES:
        raise ValueError(
            f"Unknown classification {classification!r}. Must be one of {CLASSES}."
        )

    min_p = max(window // 4, 5)

    if classification == "continuous_nonstationary":
        # First-difference removes the trend; robust z-score on the stationary increments.
        diff      = factor.diff()
        roll_med  = diff.rolling(window, min_periods=min_p).median()
        roll_mad  = _rolling_mad(diff, window, min_p)
        normalised = (diff - roll_med) / (roll_mad * 1.4826).clip(lower=1e-12)
        justification = (
            "Series is non-stationary (ADF p > 0.10). Applied first difference to "
            "remove the trend, then robust z-score (median / MAD × 1.4826) on the "
            "stationary increments. Thresholding raw non-stationary levels would "
            "produce spurious look-ahead-free signals that only work in-sample."
        )

    elif classification == "signed":
        # Centred bidirectional series: rolling-median centering + MAD scaling.
        roll_med  = factor.rolling(window, min_periods=min_p).median()
        roll_mad  = _rolling_mad(factor, window, min_p)
        normalised = (factor - roll_med) / (roll_mad * 1.4826).clip(lower=1e-12)
        justification = (
            "Series is signed/bidirectional (mean near 0, ~50% negative values). "
            "Applied rolling-median centering + MAD scaling. Symmetric thresholds are "
            "valid because positive and negative values have symmetric economic meaning. "
            "Robust scaling chosen over mean/std to limit influence of outlier spikes."
        )

    elif classification == "skewed":
        # Log-normal / fat-tailed: log1p if all non-negative, else percentile rank.
        if (factor.dropna() >= 0).all():
            log_f     = factor.apply(np.log1p)
            roll_med  = log_f.rolling(window, min_periods=min_p).median()
            roll_mad  = _rolling_mad(log_f, window, min_p)
            normalised = (log_f - roll_med) / (roll_mad * 1.4826).clip(lower=1e-12)
            justification = (
                "Series is positively skewed / log-normal (skewness > 2, < 20% negative). "
                "Applied log1p to compress the long right tail, then robust z-score "
                "(median / MAD). Raw z-score on a skewed series would give excessive weight "
                "to large outliers that are the norm in this distribution."
            )
        else:
            # Negative values present — cannot log-transform; use distribution-free rank
            pctrank    = _rolling_pctrank(factor, window, min_p)
            normalised = (pctrank - 0.5) * 2.0   # rescale [0, 1] → [-1, +1]
            justification = (
                "Series is skewed but contains negative values (log1p not applicable). "
                "Applied rolling percentile rank rescaled to [-1, +1]. This is "
                "distribution-free, robust to any outlier magnitude, and produces a "
                "stationary bounded output regardless of the underlying distribution."
            )

    else:  # continuous_stationary
        # Stationary, bounded-ish: robust rolling z-score.
        # Prefer median/MAD over mean/std when kurtosis may be elevated.
        roll_med  = factor.rolling(window, min_periods=min_p).median()
        roll_mad  = _rolling_mad(factor, window, min_p)
        normalised = (factor - roll_med) / (roll_mad * 1.4826).clip(lower=1e-12)
        justification = (
            "Series is stationary (ADF rejects unit root, p ≤ 0.10). Applied robust "
            "rolling z-score (median / MAD × 1.4826) with past-only window. Median/MAD "
            "chosen over mean/std to limit sensitivity to transient outlier spikes that "
            "are common in derivatives market data."
        )

    return normalised, justification


# ── Pipeline ──────────────────────────────────────────────────────────────────

def preprocess(
    factor: pd.Series,
    window: int = 168,
) -> tuple[pd.Series, str, str, dict]:
    """
    Classify and transform a raw factor in one call.

    Returns
    -------
    (normalised, classification, justification, stats)
    """
    classification, stats = classify(factor)
    normalised, justification = transform(factor, classification, window=window)
    return normalised, classification, justification, stats
