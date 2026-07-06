"""
signals.py — Signal model families for the factor research harness (spec §6).

Three families:
  spike_capture      — rolling z-score threshold; mean-reversion bet on the factor.
  mean_drift         — fast/slow MA cross of the factor.
  regime_conditional — base signal gated by a regime classifier.

All functions output pd.Series of {-1, 0, +1}.
The caller passes a normalised factor from preprocess.py.
The backtest engine (backtest.run) applies the mandatory shift(1) lag; do NOT
pre-shift the signal before passing it to run().
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ── Spike-capture ──────────────────────────────────────────────────────────────

def spike_capture(
    factor: pd.Series,
    *,
    z_entry: float = 2.0,
    z_exit: float = 0.5,
    window: int = 168,
) -> pd.Series:
    """
    Spike-capture signal model (spec §6 — "use when the story is a burst of X").

    Computes a rolling z-score of the factor, enters a mean-reversion bet when
    |z| > z_entry, and holds until |z| < z_exit (back-to-normal criterion).
    The hysteresis band [z_exit, z_entry) keeps the position stable between
    entry and exit events.

    Convention (contrarian / mean-reversion default):
      z > +z_entry  →  signal = -1  (factor is abnormally HIGH → expect it to fall)
      z < -z_entry  →  signal = +1  (factor is abnormally LOW → expect it to rise)
      |z| < z_exit  →  signal =  0  (factor back to normal → exit)

    Flip the returned series with -signal if your alpha story says the factor
    spike predicts continuation rather than mean-reversion.

    Parameters
    ----------
    factor  : normalised factor from preprocess.transform()
    z_entry : enter when |z| exceeds this threshold (default 2.0)
    z_exit  : exit when |z| falls below this threshold (default 0.5); must < z_entry
    window  : rolling window for z-score computation (bars)
    """
    if z_exit >= z_entry:
        raise ValueError(
            f"z_exit ({z_exit}) must be strictly less than z_entry ({z_entry})."
        )

    min_p     = max(window // 4, 5)
    roll_mean = factor.rolling(window, min_periods=min_p).mean()
    roll_std  = factor.rolling(window, min_periods=min_p).std(ddof=1).clip(lower=1e-12)
    z         = (factor - roll_mean) / roll_std

    in_band = z.abs() < z_exit

    # Build raw signal: NaN in the hysteresis zone so ffill can hold prior position.
    # Explicit exit (0) takes priority over forward-filled entry via assignment order.
    sig = pd.Series(np.nan, index=factor.index, dtype=float)
    sig[z < -z_entry] =  1.0   # abnormally low factor → long
    sig[z >  z_entry] = -1.0   # abnormally high factor → short
    sig[in_band]      =  0.0   # back-to-normal → exit (overrides any same-bar entry)

    # Forward-fill: hold position in the hysteresis zone [z_exit, z_entry)
    sig = sig.ffill().fillna(0)
    return sig.round().astype(int)


# ── Mean-drift ────────────────────────────────────────────────────────────────

def mean_drift(
    factor: pd.Series,
    *,
    fast: int = 24,
    slow: int = 168,
) -> pd.Series:
    """
    Mean-drift (MA cross) signal model (spec §6 — "sustained accumulation/pressure").

    Generates a directional bet aligned with the persistent trend of the factor:
      fast MA > slow MA  →  +1 (factor trending up)
      fast MA < slow MA  →  -1 (factor trending down)
      warm-up period     →   0 (insufficient history)

    Parameters
    ----------
    factor : normalised factor from preprocess.transform()
    fast   : fast MA window in bars (default 24 ≈ 1 day hourly)
    slow   : slow MA window in bars (default 168 ≈ 1 week hourly); must > fast
    """
    if slow <= fast:
        raise ValueError(f"slow ({slow}) must be greater than fast ({fast}).")

    ma_fast = factor.rolling(fast, min_periods=fast).mean()
    ma_slow = factor.rolling(slow, min_periods=slow).mean()
    diff    = ma_fast - ma_slow

    signal = diff.apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return signal.fillna(0).astype(int)


# ── Regime classifier helpers ─────────────────────────────────────────────────

def _quantile_regime(
    indicator: pd.Series,
    *,
    window: int = 168,
    n_quantiles: int = 2,
) -> pd.Series:
    """
    Classify each bar into a regime (0 … n_quantiles-1) based on the rolling
    quantile rank of the indicator. Lower index = lower regime (calmer / lower value).
    Past-only by construction.
    """
    min_p = max(window // 4, 5)
    pct = indicator.rolling(window, min_periods=min_p).apply(
        lambda x: float((x[:-1] < x[-1]).mean()) if len(x) > 1 else 0.5,
        raw=True,
    )
    edges  = np.linspace(0.0, 1.0, n_quantiles + 1)
    regime = pd.Series(0, index=indicator.index, dtype=int)
    for i in range(n_quantiles):
        lo, hi = edges[i], edges[i + 1]
        if i == n_quantiles - 1:
            mask = (pct >= lo) & (pct <= hi)
        else:
            mask = (pct >= lo) & (pct < hi)
        regime[mask] = i
    regime[pct.isna()] = 0
    return regime


def _hmm_regime(
    indicator: pd.Series,
    *,
    n_states: int = 2,
) -> pd.Series:
    """
    Gaussian HMM regime classification via hmmlearn.
    Falls back to quantile regime if hmmlearn is not installed.
    States are re-ordered so that state 0 = lowest mean (quietest regime).
    """
    try:
        from hmmlearn import hmm as _hmm  # type: ignore[import]
    except ImportError:
        return _quantile_regime(indicator, n_quantiles=n_states)

    obs   = indicator.dropna().values.reshape(-1, 1)
    model = _hmm.GaussianHMM(
        n_components=n_states, covariance_type="diag",
        n_iter=100, random_state=42,
    )
    model.fit(obs)
    raw_states = model.predict(obs)

    # Re-order states: 0 = lowest mean
    means = [obs[raw_states == s].mean() if (raw_states == s).any() else 0.0
             for s in range(n_states)]
    order = np.argsort(means)
    remap = {old: new for new, old in enumerate(order)}
    states = np.array([remap[s] for s in raw_states])

    regime                   = pd.Series(0, index=indicator.index, dtype=int)
    regime[indicator.notna()] = states
    return regime


# ── Regime-conditional ────────────────────────────────────────────────────────

def regime_conditional(
    factor: pd.Series,
    base_signal: pd.Series,
    *,
    regime_indicator: pd.Series | None = None,
    favourable_regimes: tuple[int, ...] = (0,),
    n_regimes: int = 2,
    window: int = 168,
    method: str = "quantile",
) -> pd.Series:
    """
    Regime-conditional signal: gate a base signal to fire only in favourable regimes
    (spec §6 — "use when the edge only holds in some market states").

    This model can only suppress signals, never generate new ones — the returned
    series has |gated[t]| ≤ |base_signal[t]| for all t.

    Parameters
    ----------
    factor              : factor series (used to derive regimes when regime_indicator is None)
    base_signal         : signal to gate — output of spike_capture or mean_drift
    regime_indicator    : separate indicator for regime classification (e.g. realised vol);
                          defaults to factor if None
    favourable_regimes  : tuple of regime indices in which the base signal is allowed
    n_regimes           : total number of regime states
    window              : rolling lookback for quantile regime (ignored for HMM)
    method              : 'quantile' (default, no extra deps) or 'hmm' (requires hmmlearn)
    """
    indicator = regime_indicator if regime_indicator is not None else factor

    if method == "hmm":
        regime = _hmm_regime(indicator, n_states=n_regimes)
    else:
        regime = _quantile_regime(indicator, window=window, n_quantiles=n_regimes)

    in_favourable = regime.isin(favourable_regimes)
    gated         = base_signal.reindex(factor.index).fillna(0).copy()
    gated[~in_favourable] = 0
    return gated.astype(int)
