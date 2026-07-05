"""
metrics.py — Performance metrics including Deflated Sharpe Ratio (DSR).

All Sharpe-family metrics operate on net returns (costs must already be applied).
DSR implementation: Bailey & Lopez de Prado (2014).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    from scipy import stats as _scipy_stats
    _SCIPY = True
except ImportError:
    _SCIPY = False


BARS_PER_YEAR: dict[str, int] = {
    "1m":  525_600,
    "5m":  105_120,
    "15m":  35_040,
    "1h":    8_760,
    "4h":    2_190,
    "1d":      365,
}


# ── Core metrics ───────────────────────────────────────────────────────────────

def sharpe(returns: pd.Series, bars_per_year: int = 8_760) -> float:
    """Annualised Sharpe ratio."""
    mu    = returns.mean()
    sigma = returns.std(ddof=1)
    if sigma == 0 or np.isnan(sigma):
        return 0.0
    return float(mu / sigma * np.sqrt(bars_per_year))


def sortino(returns: pd.Series, bars_per_year: int = 8_760) -> float:
    """Annualised Sortino ratio (downside std denominator)."""
    mu       = returns.mean()
    downside = returns[returns < 0]
    if len(downside) == 0:
        return np.inf
    dd = downside.std(ddof=1)
    if dd == 0:
        return 0.0
    return float(mu / dd * np.sqrt(bars_per_year))


def max_drawdown(equity: pd.Series) -> float:
    """Maximum peak-to-trough drawdown as a positive fraction."""
    running_max = equity.cummax()
    dd = (equity - running_max) / running_max
    return float(abs(dd.min()))


def calmar(returns: pd.Series, equity: pd.Series, bars_per_year: int = 8_760) -> float:
    """Annualised Calmar ratio: CAGR / max drawdown."""
    n = len(returns)
    if n < 2:
        return 0.0
    years        = n / bars_per_year
    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    cagr         = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0.0
    mdd          = max_drawdown(equity)
    return float(cagr / mdd) if mdd > 0 else np.inf


def hit_rate(returns: pd.Series) -> float:
    active = returns[returns != 0]
    if len(active) == 0:
        return 0.0
    return float((active > 0).mean())


def profit_factor(returns: pd.Series) -> float:
    wins   = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())
    if losses == 0:
        return np.inf
    return float(wins / losses)


# ── Deflated Sharpe Ratio ──────────────────────────────────────────────────────

def deflated_sharpe_ratio(
    sr_best: float,
    sr_trials: list[float] | np.ndarray,
    n_obs: int,
    skewness: float = 0.0,
    excess_kurtosis: float = 0.0,
) -> tuple[float, float]:
    """
    Deflated Sharpe Ratio — Bailey & Lopez de Prado (2014).

    Accounts for selection bias when sr_best is the maximum across N configurations.

    Parameters
    ----------
    sr_best          : best observed annualised Sharpe across all tested configs
    sr_trials        : array of Sharpe estimates for every config in the grid
    n_obs            : number of return observations in the evaluation period
    skewness         : skewness of the best strategy's net returns
    excess_kurtosis  : excess kurtosis (kurtosis - 3) of best strategy's net returns

    Returns
    -------
    (dsr_prob, expected_max_sr)
        dsr_prob       : P(true SR > E[max SR̃]) — close to 1 is good, close to 0 is noise
        expected_max_sr: expected max SR under the null across N iid Gaussian trials
    """
    if not _SCIPY:
        raise ImportError("scipy is required for DSR. Run: pip install scipy")

    sr_trials = np.asarray(sr_trials, dtype=float)
    N = len(sr_trials)
    if N == 0 or n_obs < 4:
        return 0.0, 0.0

    sr_mean = sr_trials.mean()
    sr_std  = sr_trials.std(ddof=1) if N > 1 else 1e-8

    gamma = 0.5772156649  # Euler–Mascheroni constant
    z1 = _scipy_stats.norm.ppf(1 - 1 / N)
    z2 = _scipy_stats.norm.ppf(1 - 1 / (N * np.e))
    e_max_sr = sr_mean + sr_std * ((1 - gamma) * z1 + gamma * z2)

    # Per-period SR for the non-normality adjustment (Mertens 2002)
    sr_per_period = sr_best / np.sqrt(max(n_obs, 1))
    var_sr = (
        1 + (1 - skewness * sr_per_period + (excess_kurtosis / 4) * sr_per_period ** 2)
    ) / max(n_obs, 1)

    se      = np.sqrt(max(var_sr, 1e-12))
    dsr_prob = float(_scipy_stats.norm.cdf((sr_best - e_max_sr) / se))
    return dsr_prob, float(e_max_sr)


# ── Full suite ─────────────────────────────────────────────────────────────────

def compute_all(
    net_ret: pd.Series,
    equity: pd.Series,
    turnover: pd.Series,
    bars_per_year: int = 8_760,
    n_configs: int = 1,
) -> dict:
    """
    Compute the full metric suite. Returns a flat dict ready for display or persistence.

    n_configs: total configurations tested in the parameter grid (DSR haircut input).
    """
    sr = sharpe(net_ret, bars_per_year)

    # DSR: conservative assumption — treat all N configs as having SR near sr_best
    dsr_prob, e_max_sr = deflated_sharpe_ratio(
        sr_best=sr,
        sr_trials=[sr] * n_configs,
        n_obs=len(net_ret),
        skewness=float(net_ret.skew()),
        excess_kurtosis=float(net_ret.kurtosis()),
    )

    return {
        "sharpe":          sr,
        "sortino":         sortino(net_ret, bars_per_year),
        "calmar":          calmar(net_ret, equity, bars_per_year),
        "max_drawdown":    max_drawdown(equity),
        "hit_rate":        hit_rate(net_ret),
        "profit_factor":   profit_factor(net_ret),
        "avg_turnover":    float(turnover.mean()),
        "dsr_prob":        dsr_prob,
        "expected_max_sr": e_max_sr,
        "n_configs":       n_configs,
        "n_obs":           len(net_ret),
    }
