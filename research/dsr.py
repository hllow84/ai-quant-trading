"""
dsr.py — Correctly-specified Deflated Sharpe Ratio.

WHY THIS MODULE EXISTS
----------------------
`research/metrics.py::deflated_sharpe_ratio` returned 0.0000 or 1.0000 and
almost nothing in between across every study in this repo. That is the
signature of a broken discriminator, not of a universe with no edge. Two
independent defects were found on 2026-07-21:

BUG 1 — UNITS INCONSISTENCY IN THE STANDARD ERROR (the saturation cause).
    The numerator (sr_best - E[max SR]) is in ANNUALISED Sharpe units, but the
    denominator was the standard error of the PER-PERIOD Sharpe:

        var_sr = (1 + (1 - skew*sr_pp + (ek/4)*sr_pp**2)) / n_obs

    That SE is smaller than the annualised one by ~sqrt(periods_per_year).
    Measured on the real index run: SE 0.0313 where it should be 0.3376, i.e.
    10.8x too small. Every z-score was inflated ~11-16x, so DSR collapsed to a
    step function at E[max SR]: 0.0000 below, 1.0000 above, nothing useful in
    between. This module keeps EVERYTHING in annualised units.

    It also restores the Mertens (2002) variance, which the old code mis-stated
    as `1 + (1 - ...)` = `2 - ...`, dropping the 0.5*SR^2 term and adding a
    spurious +1.

        Var(SR_pp) = (1 + 0.5*SR_pp^2 - skew*SR_pp + (ekurt/4)*SR_pp^2) / n_obs
        SE(SR_ann) = sqrt(ann_factor * Var(SR_pp))

BUG 2 — CONTAMINATED DEFLATION POOL.
    E[max SR] is driven by the MEAN and STD of the trial Sharpes. The pool held
    every config ever run, including M5 configs at Sharpe -14.6 that were
    structurally doomed by cost-to-risk. Those inflate the pool std (sigma=3.39
    over 237 trials), and E[max SR] scales with sigma:

        E[max SR] = mu + sigma * ((1-gamma)*z_1 + gamma*z_2)

    giving E[max SR] = +6.78 annualised — a bar no real strategy can clear. The
    haircut was being set by how badly the WORST configs failed, which is
    backwards. Pool selection now happens explicitly via the helpers below.

    Bailey & Lopez de Prado's intent is to deflate against the trials actually
    searched over when selecting the winner. Choosing the pool is therefore a
    judgement call that must be STATED, not hidden. Two are provided:

      structural_pool()  — PREFERRED. Selects on a priori structure (timeframe
                           and family cells that were serious candidates before
                           any result was seen). Contains no outcome
                           information, so it does not bias the null.

      floor_pool()       — Selects trials with Sharpe >= a stated floor.
                           CAUTION: this is selection ON THE OUTCOME. Dropping
                           the left tail raises mu and cuts sigma, which lowers
                           E[max SR] and makes passing EASIER. Report it as a
                           sensitivity check, never as the headline gate.

    Neither pool may be chosen after seeing which one lets a config pass.

Reference: Bailey & Lopez de Prado (2014), "The Deflated Sharpe Ratio".
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

EULER_GAMMA = 0.5772156649015329

# Daily-aggregated returns are used everywhere in the FTMO/sweep harness, so the
# annualisation factor is trading days per year regardless of the SIGNAL
# timeframe. An H4 strategy and a D1 strategy both produce one return per
# calendar trading day, so both annualise at 252 -- the per-TF correction people
# expect is already handled upstream by build_daily_returns().
TRADING_DAYS_PER_YEAR = 252


def expected_max_sharpe(sr_trials: np.ndarray | list[float]) -> tuple[float, int, float, float]:
    """
    E[max Sharpe] under the null that all N trials are iid Gaussian with the
    pool's own mean and std. Returns (e_max_sr, N, pool_mean, pool_std).
    All values in the same (annualised) units as the input.
    """
    sr = np.asarray(sr_trials, dtype=float)
    sr = sr[np.isfinite(sr)]
    N = len(sr)
    if N == 0:
        return float("nan"), 0, float("nan"), float("nan")
    if N == 1:
        return float(sr[0]), 1, float(sr[0]), 0.0

    mu = float(sr.mean())
    sigma = float(sr.std(ddof=1))
    z1 = stats.norm.ppf(1.0 - 1.0 / N)
    z2 = stats.norm.ppf(1.0 - 1.0 / (N * np.e))
    e_max = mu + sigma * ((1.0 - EULER_GAMMA) * z1 + EULER_GAMMA * z2)
    return float(e_max), N, mu, sigma


def deflated_sharpe(
    sr_best: float,
    sr_trials: np.ndarray | list[float],
    n_obs: int,
    ann_factor: int = TRADING_DAYS_PER_YEAR,
    skewness: float = 0.0,
    excess_kurtosis: float = 0.0,
) -> dict:
    """
    Deflated Sharpe Ratio with consistent ANNUALISED units throughout.

    sr_best   : annualised Sharpe of the selected config
    sr_trials : annualised Sharpes of every config in the deflation pool
    n_obs     : number of return observations (daily bars) behind sr_best
    ann_factor: periods per year for those observations (252 for daily)

    Returns a dict with dsr, e_max_sr, se_ann, z, and pool diagnostics, so the
    caller can show WHY a config passed or failed rather than just the verdict.
    """
    e_max, N, pool_mu, pool_sd = expected_max_sharpe(sr_trials)
    if N == 0 or n_obs < 4 or not np.isfinite(sr_best):
        return dict(dsr=float("nan"), e_max_sr=e_max, se_ann=float("nan"),
                    z=float("nan"), pool_n=N, pool_mean=pool_mu, pool_std=pool_sd)

    # Mertens (2002) variance of the per-period Sharpe, then scaled to annual.
    sr_pp = sr_best / np.sqrt(ann_factor)
    var_pp = (
        1.0
        + 0.5 * sr_pp ** 2
        - skewness * sr_pp
        + (excess_kurtosis / 4.0) * sr_pp ** 2
    ) / n_obs
    se_ann = float(np.sqrt(max(ann_factor * var_pp, 1e-16)))

    z = (sr_best - e_max) / se_ann
    return dict(dsr=float(stats.norm.cdf(z)), e_max_sr=e_max, se_ann=se_ann,
                z=float(z), pool_n=N, pool_mean=pool_mu, pool_std=pool_sd)


# ── Deflation pools ────────────────────────────────────────────────────────────

def structural_pool(df: pd.DataFrame, timeframes: list[str], families: list[str],
                    sharpe_col: str = "sharpe") -> np.ndarray:
    """
    PREFERRED pool. Selects on a priori STRUCTURE — the timeframe and family
    cells that were genuine candidates before any result was seen — so it
    carries no outcome information and does not bias the null.

    Use this when the honest description of the search is "we were looking for a
    swing trend system", not "we ran everything and picked the best".
    """
    m = df["timeframe"].isin(timeframes) & df["family"].isin(families)
    return pd.to_numeric(df.loc[m, sharpe_col], errors="coerce").dropna().to_numpy()


def floor_pool(sr_all: np.ndarray | list[float], floor: float = -1.0) -> np.ndarray:
    """
    SENSITIVITY-CHECK pool. Keeps trials with Sharpe >= `floor`, dropping configs
    that were never deployable candidates.

    CAUTION — this selects on the OUTCOME. Cutting the left tail raises the pool
    mean and shrinks its std, which LOWERS E[max SR] and makes passing easier.
    It is reported alongside the structural pool to show sensitivity, and must
    not be used as the headline gate.
    """
    sr = np.asarray(sr_all, dtype=float)
    return sr[np.isfinite(sr) & (sr >= floor)]
