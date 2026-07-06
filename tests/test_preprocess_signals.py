"""
Acceptance tests for Step 3 — preprocess.py + signals.py.

Verifies:
  §P1  Classification: each synthetic series type is correctly labelled.
  §P2  Transform: output is valid, NaN-free after warm-up, past-only.
  §S1  spike_capture: output values, index, no all-zero on noisy input.
  §S2  mean_drift: output values, warm-up zero, non-zero on trending input.
  §S3  regime_conditional: gating only suppresses; never adds signals.
  §E2E end-to-end: preprocess → signal → backtest pipeline runs without error.

Run: pytest tests/test_preprocess_signals.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from research.preprocess import CLASSES, classify, transform, preprocess
from research.signals import spike_capture, mean_drift, regime_conditional
from research.backtest import run as bt_run
from research.metrics import sharpe


# ── Synthetic series helpers ──────────────────────────────────────────────────

RNG = np.random.default_rng(7)
N   = 2_000
IDX = pd.date_range("2023-01-01", periods=N, freq="1h", tz="UTC")


def _stationary_series() -> pd.Series:
    """Funding-rate-like: AR(1) mean-reverting, low skew, ~50% negative."""
    s = np.zeros(N)
    s[0] = RNG.normal(0, 0.01)
    for i in range(1, N):
        s[i] = 0.92 * s[i - 1] + RNG.normal(0, 0.005)
    return pd.Series(s, index=IDX)


def _nonstationary_series() -> pd.Series:
    """OI-like: random walk — clearly non-stationary."""
    increments = np.abs(RNG.normal(100, 10, N))   # always positive increments
    return pd.Series(np.cumsum(increments) + 1_000, index=IDX)


def _signed_series() -> pd.Series:
    """CVD-like: symmetric around zero, ~50% negative."""
    return pd.Series(RNG.normal(0, 50, N), index=IDX)


def _skewed_series() -> pd.Series:
    """Transfer-volume-like: log-normal, heavily right-skewed."""
    return pd.Series(np.exp(RNG.normal(3, 1, N)), index=IDX)


def _asset_returns() -> pd.Series:
    """Synthetic hourly log-returns."""
    return pd.Series(RNG.normal(0.0001, 0.01, N), index=IDX)


# ── §P1  Classification ───────────────────────────────────────────────────────

class TestClassify:

    def test_stationary_classified(self):
        label, _ = classify(_stationary_series())
        assert label == "continuous_stationary", f"Got {label!r}"

    def test_nonstationary_classified(self):
        label, _ = classify(_nonstationary_series())
        assert label == "continuous_nonstationary", f"Got {label!r}"

    def test_signed_classified(self):
        label, _ = classify(_signed_series())
        assert label == "signed", f"Got {label!r}"

    def test_skewed_classified(self):
        label, _ = classify(_skewed_series())
        assert label == "skewed", f"Got {label!r}"

    def test_label_is_in_classes(self):
        for factory in [_stationary_series, _nonstationary_series,
                        _signed_series, _skewed_series]:
            label, _ = classify(factory())
            assert label in CLASSES, f"{label!r} not in CLASSES"

    def test_stats_dict_required_keys(self):
        _, stats = classify(_stationary_series())
        required = {"mean", "std", "skewness", "pct_negative", "autocorr_lag1", "adf_p"}
        missing  = required - set(stats.keys())
        assert not missing, f"Missing keys in stats dict: {missing}"

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="too short"):
            classify(pd.Series([1.0, 2.0, 3.0]))


# ── §P2  Transform ────────────────────────────────────────────────────────────

_TRANSFORM_CASES = [
    ("continuous_stationary",    _stationary_series),
    ("continuous_nonstationary", _nonstationary_series),
    ("signed",                   _signed_series),
    ("skewed",                   _skewed_series),
]


class TestTransform:

    @pytest.mark.parametrize("cls,factory", _TRANSFORM_CASES)
    def test_returns_series_and_justification(self, cls, factory):
        norm, justification = transform(factory(), cls, window=168)
        assert isinstance(norm, pd.Series), "normalised must be pd.Series"
        assert isinstance(justification, str) and len(justification) > 20

    @pytest.mark.parametrize("cls,factory", _TRANSFORM_CASES)
    def test_index_preserved(self, cls, factory):
        f = factory()
        norm, _ = transform(f, cls, window=168)
        assert norm.index.equals(f.index), "Index must be preserved by transform"

    @pytest.mark.parametrize("cls,factory", _TRANSFORM_CASES)
    def test_no_nan_after_warmup(self, cls, factory):
        """Beyond the warm-up period there must be no NaN."""
        f       = factory()
        norm, _ = transform(f, cls, window=168)
        warmup  = 168 // 4 + 10    # conservative buffer beyond min_periods
        tail    = norm.iloc[warmup:]
        nan_frac = tail.isna().mean()
        assert nan_frac == 0.0, (
            f"[{cls}] NaN fraction after warm-up = {nan_frac:.4f} "
            f"({tail.isna().sum()} NaN values)"
        )

    def test_past_only_no_look_ahead(self):
        """
        Inserting a synthetic outlier at bar T must not alter normalised values
        at bars < T.  Strictly backward-looking rolling windows guarantee this.
        """
        f             = _stationary_series().copy()
        norm_orig, _  = transform(f, "continuous_stationary", window=50)

        f_tampered           = f.copy()
        f_tampered.iloc[500] = f.iloc[500] + 200 * f.std()
        norm_tampered, _     = transform(f_tampered, "continuous_stationary", window=50)

        pre_orig      = norm_orig.iloc[:500]
        pre_tampered  = norm_tampered.iloc[:500]
        # Use NaN-aware equality: NaN == NaN should count as equal (both series are NaN
        # in the same warm-up positions, but NaN != NaN in pandas/numpy by default).
        equal = (pre_orig == pre_tampered) | (pre_orig.isna() & pre_tampered.isna())
        assert equal.all(), (
            "Transform altered values BEFORE the injected outlier — look-ahead present."
        )

    def test_unknown_classification_raises(self):
        with pytest.raises(ValueError):
            transform(_stationary_series(), "not_a_real_class")


# ── §S1  spike_capture ────────────────────────────────────────────────────────

class TestSpikeCapture:

    def test_output_in_set(self):
        f   = _stationary_series()
        sig = spike_capture(f, z_entry=2.0, z_exit=0.5, window=100)
        assert set(sig.dropna().unique()).issubset({-1, 0, 1}), (
            f"spike_capture returned values outside {{-1, 0, 1}}: {set(sig.unique())}"
        )

    def test_index_preserved(self):
        f   = _stationary_series()
        sig = spike_capture(f)
        assert sig.index.equals(f.index)

    def test_nonzero_signal_generated(self):
        """Noisy series should produce at least some entries."""
        f   = _signed_series()
        sig = spike_capture(f, z_entry=1.5, window=100)
        assert (sig != 0).any(), "spike_capture produced all-zero signal on noisy series"

    def test_z_exit_gte_z_entry_raises(self):
        with pytest.raises(ValueError, match="z_exit"):
            spike_capture(_stationary_series(), z_entry=1.0, z_exit=2.0)

    def test_no_signal_before_warmup(self):
        """During initial warm-up (insufficient rolling data), signal must stay 0."""
        f   = _stationary_series()
        sig = spike_capture(f, z_entry=2.0, z_exit=0.5, window=100)
        # Before min_periods (window//4 = 25) the z-score is NaN → no entry possible
        assert (sig.iloc[:20] == 0).all(), "Non-zero signal before rolling window warm-up"


# ── §S2  mean_drift ───────────────────────────────────────────────────────────

class TestMeanDrift:

    def test_output_in_set(self):
        f   = _stationary_series()
        sig = mean_drift(f, fast=24, slow=100)
        assert set(sig.dropna().unique()).issubset({-1, 0, 1}), (
            f"mean_drift returned values outside {{-1, 0, 1}}: {set(sig.unique())}"
        )

    def test_index_preserved(self):
        assert mean_drift(_stationary_series()).index.equals(IDX)

    def test_warm_up_is_zero(self):
        """Bars before the slow MA has min_periods data must be 0."""
        sig = mean_drift(_stationary_series(), fast=24, slow=100)
        assert (sig.iloc[:99] == 0).all(), (
            "mean_drift non-zero before slow MA warm-up (min_periods=slow)."
        )

    def test_trending_factor_nonzero(self):
        trending = pd.Series(np.linspace(0.0, 10.0, N), index=IDX)
        sig      = mean_drift(trending, fast=10, slow=50)
        assert (sig.iloc[50:] != 0).any(), (
            "mean_drift produced all-zero signal on strictly trending factor"
        )

    def test_slow_lte_fast_raises(self):
        with pytest.raises(ValueError):
            mean_drift(_stationary_series(), fast=100, slow=50)


# ── §S3  regime_conditional ───────────────────────────────────────────────────

class TestRegimeConditional:

    def test_gating_only_suppresses(self):
        """
        regime_conditional can only remove signal bars, never add new ones.
        For every bar: |gated[t]| ≤ |base_signal[t]|
        """
        f      = _signed_series()
        base   = spike_capture(f, z_entry=1.5, window=100)
        gated  = regime_conditional(f, base, n_regimes=2, favourable_regimes=(0,))
        assert (gated.abs() <= base.abs()).all(), (
            "Regime gating added a signal that was not in base_signal."
        )

    def test_output_in_set(self):
        f     = _stationary_series()
        base  = mean_drift(f, fast=10, slow=50)
        gated = regime_conditional(f, base)
        assert set(gated.dropna().unique()).issubset({-1, 0, 1})

    def test_index_preserved(self):
        f     = _stationary_series()
        base  = mean_drift(f, fast=10, slow=50)
        gated = regime_conditional(f, base)
        assert gated.index.equals(f.index)

    def test_all_regimes_favourable_matches_base(self):
        """Allowing all regimes should return the same signal as base."""
        f     = _signed_series()
        base  = spike_capture(f, z_entry=1.5, window=100)
        gated = regime_conditional(
            f, base, n_regimes=2, favourable_regimes=(0, 1)
        )
        assert (gated == base).all(), (
            "Gating with all regimes favourable should not alter the base signal."
        )

    def test_no_regimes_favourable_gives_zero(self):
        """Allowing no regimes should zero out all signals."""
        f     = _signed_series()
        base  = spike_capture(f, z_entry=1.5, window=100)
        gated = regime_conditional(f, base, n_regimes=2, favourable_regimes=())
        assert (gated == 0).all(), (
            "Gating with no favourable regimes should produce all-zero signal."
        )

    def test_separate_regime_indicator(self):
        """regime_indicator can be a different series from factor."""
        f         = _signed_series()
        vol_proxy = _stationary_series()
        base      = mean_drift(f, fast=10, slow=50)
        gated     = regime_conditional(
            f, base, regime_indicator=vol_proxy, n_regimes=2
        )
        assert set(gated.dropna().unique()).issubset({-1, 0, 1})


# ── §E2E  Full pipeline ───────────────────────────────────────────────────────

class TestEndToEnd:

    def test_preprocess_returns_four_tuple(self):
        for factory in [_stationary_series, _nonstationary_series,
                        _signed_series, _skewed_series]:
            result = preprocess(factory(), window=168)
            assert len(result) == 4
            norm, cls, justification, stats = result
            assert cls in CLASSES
            assert isinstance(norm, pd.Series)
            assert isinstance(justification, str)
            assert isinstance(stats, dict)

    def test_preprocess_spike_backtest_runs(self):
        """
        Full pipeline: classify → transform → spike_capture → backtest.
        Must complete without error and return finite metrics.
        """
        raw_factor = _signed_series()
        rets       = _asset_returns()

        norm, cls, _, _ = preprocess(raw_factor, window=100)
        sig              = spike_capture(norm, z_entry=1.5, window=100)

        result = bt_run(sig, rets, fee_bps=7, slippage_bps=5)

        sr = sharpe(result["net_ret"])
        assert np.isfinite(sr), f"Sharpe is not finite: {sr}"

    def test_preprocess_mean_drift_backtest_runs(self):
        raw_factor = _nonstationary_series()
        rets       = _asset_returns()

        norm, _, _, _ = preprocess(raw_factor, window=100)
        sig            = mean_drift(norm, fast=12, slow=100)

        result = bt_run(sig, rets, fee_bps=7, slippage_bps=5)
        sr     = sharpe(result["net_ret"])
        assert np.isfinite(sr), f"Sharpe is not finite: {sr}"

    def test_preprocess_regime_backtest_runs(self):
        raw_factor = _skewed_series()
        rets       = _asset_returns()

        norm, _, _, _ = preprocess(raw_factor, window=100)
        base          = spike_capture(norm, z_entry=1.5, window=100)
        sig           = regime_conditional(norm, base, n_regimes=2)

        result = bt_run(sig, rets, fee_bps=7, slippage_bps=5)
        sr     = sharpe(result["net_ret"])
        assert np.isfinite(sr), f"Sharpe is not finite: {sr}"
