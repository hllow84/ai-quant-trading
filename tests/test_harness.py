"""
Acceptance tests §10.1–10.3  (FACTOR_RESEARCH_HARNESS_SPEC.md)

§10.1  Look-ahead trap  — a factor built from next-bar returns must not inflate Sharpe.
§10.2  Null-factor      — a shuffled random signal must produce Sharpe ≈ 0 after costs.
§10.3  Cost monotonicity — increasing fee or slippage must degrade Sharpe monotonically.

Run: pytest tests/test_harness.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from research.backtest import LookAheadError, guard_look_ahead, run as bt_run
from research.metrics import sharpe


RNG = np.random.default_rng(42)
N   = 5_000   # ~7 months of hourly bars


def _make_returns(n: int = N) -> pd.Series:
    idx = pd.date_range("2023-01-01", periods=n, freq="1h", tz="UTC")
    r   = RNG.normal(0.0001, 0.01, size=n)
    return pd.Series(r, index=idx, name="returns")


def _make_signal(n: int = N, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2023-01-01", periods=n, freq="1h", tz="UTC")
    return pd.Series(rng.choice([-1, 0, 1], size=n, p=[0.3, 0.4, 0.3]), index=idx)


# ── §10.1  Look-ahead trap ─────────────────────────────────────────────────────

class TestLookAheadTrap:

    def test_guard_catches_next_bar_factor(self):
        """
        guard_look_ahead() must raise LookAheadError when the raw factor IS
        next-bar return.  That factor has correlation ≈ 1.0 with future returns,
        which blows past the 0.5 threshold.

        Why the backtest engine's own shift(1) does NOT suffice on its own:
          position[t] = sign(return[t+1]).shift(1) = sign(return[t])
          gross_ret[t] = sign(return[t]) * return[t] = |return[t]| > 0 always
        → Sharpe explodes to ~100.  The guard must intercept BEFORE run() is called.
        """
        rets = _make_returns()
        look_ahead_factor = rets.shift(-1).fillna(0)

        with pytest.raises(LookAheadError):
            guard_look_ahead(look_ahead_factor, rets, threshold=0.5)

    def test_extra_forward_shift_does_not_improve_sharpe(self):
        """
        If the engine already lags correctly, shifting the signal one additional bar
        forward must NOT meaningfully improve Sharpe — it only discards information.
        Any improvement > 0.3 SR units suggests hidden look-ahead in the engine.
        """
        rets   = _make_returns()
        signal = _make_signal()

        base    = bt_run(signal,           rets, fee_bps=7, slippage_bps=5)
        forward = bt_run(signal.shift(1),  rets, fee_bps=7, slippage_bps=5)

        sr_base    = sharpe(base["net_ret"])
        sr_forward = sharpe(forward["net_ret"])

        assert sr_forward <= sr_base + 0.3, (
            f"Extra forward shift raised Sharpe from {sr_base:.3f} → {sr_forward:.3f}.  "
            f"Suggests residual look-ahead in the engine."
        )


# ── §10.2  Null-factor ─────────────────────────────────────────────────────────

class TestNullFactor:

    def test_null_factor_gross_sharpe_near_zero(self):
        """
        Without costs, an independently drawn random signal has no edge — mean gross
        Sharpe across 200 draws must be |mean| < 0.15.

        Each iteration draws a FRESH random signal (independent seeds) rather than
        permuting the same fixed signal, avoiding count-imbalance bias when the
        return series has a small positive drift.
        """
        rets = _make_returns()

        sharpes: list[float] = []
        for seed in range(200):
            rng_s  = np.random.default_rng(seed + 1000)
            vals   = rng_s.choice([-1, 0, 1], size=N, p=[0.3, 0.4, 0.3])
            signal = pd.Series(vals, index=rets.index)
            res    = bt_run(signal, rets, fee_bps=0, slippage_bps=0)
            sharpes.append(sharpe(res["net_ret"]))

        mean_sr = float(np.mean(sharpes))
        assert abs(mean_sr) < 0.15, (
            f"Null-factor GROSS mean Sharpe={mean_sr:.4f} — structural bias in engine."
        )

    def test_null_factor_costs_produce_negative_sharpe(self):
        """
        With realistic fees, a high-turnover random signal must have mean Sharpe < 0.

        High-turnover random signals (~0.84 avg |position.diff()| per bar) × 12 bps
        round-trip = ~1 bps drag per bar, which annualises to a large negative SR.
        If mean_sr >= 0, the cost subtraction has a sign error.
        """
        rets = _make_returns()

        sharpes: list[float] = []
        for seed in range(50):
            rng_s  = np.random.default_rng(seed + 1000)
            vals   = rng_s.choice([-1, 0, 1], size=N, p=[0.3, 0.4, 0.3])
            signal = pd.Series(vals, index=rets.index)
            res    = bt_run(signal, rets, fee_bps=7, slippage_bps=5)
            sharpes.append(sharpe(res["net_ret"]))

        mean_sr = float(np.mean(sharpes))
        assert mean_sr < 0, (
            f"Null-factor with costs has positive mean Sharpe={mean_sr:.4f} — "
            f"costs are not being subtracted correctly."
        )


# ── §10.3  Cost monotonicity ───────────────────────────────────────────────────

class TestCostMonotonicity:

    def test_sharpe_degrades_with_higher_fees(self):
        """
        Net Sharpe must be weakly decreasing as taker fee increases.
        Even 1e-9 tolerance allows for floating-point noise.
        """
        rets   = _make_returns()
        signal = _make_signal(seed=99)

        fee_schedule = [0, 3, 7, 15, 30, 60]
        sharpes: list[float] = []
        for fee in fee_schedule:
            res = bt_run(signal, rets, fee_bps=fee, slippage_bps=0)
            sharpes.append(sharpe(res["net_ret"]))

        for i in range(1, len(sharpes)):
            assert sharpes[i] <= sharpes[i - 1] + 1e-9, (
                f"Sharpe rose from {sharpes[i-1]:.5f} → {sharpes[i]:.5f} "
                f"when fee went from {fee_schedule[i-1]} → {fee_schedule[i]} bps.  "
                f"Fee is not being applied correctly."
            )

    def test_sharpe_degrades_with_higher_slippage(self):
        """Net Sharpe must be weakly decreasing as slippage increases."""
        rets   = _make_returns()
        signal = _make_signal(seed=99)

        slip_schedule = [0, 2, 5, 10, 25, 50]
        sharpes: list[float] = []
        for slip in slip_schedule:
            res = bt_run(signal, rets, fee_bps=0, slippage_bps=slip)
            sharpes.append(sharpe(res["net_ret"]))

        for i in range(1, len(sharpes)):
            assert sharpes[i] <= sharpes[i - 1] + 1e-9, (
                f"Sharpe rose from {sharpes[i-1]:.5f} → {sharpes[i]:.5f} "
                f"when slippage went from {slip_schedule[i-1]} → {slip_schedule[i]} bps.  "
                f"Slippage is not being applied correctly."
            )

    def test_zero_cost_beats_positive_cost(self):
        """Gross performance (zero cost) must beat net performance (with cost)."""
        rets   = _make_returns()
        signal = _make_signal(seed=99)

        gross = bt_run(signal, rets, fee_bps=0, slippage_bps=0)
        net   = bt_run(signal, rets, fee_bps=7, slippage_bps=5)

        sr_gross = sharpe(gross["net_ret"])
        sr_net   = sharpe(net["net_ret"])

        assert sr_gross >= sr_net - 1e-9, (
            f"Zero-cost Sharpe ({sr_gross:.4f}) is lower than cost-inclusive Sharpe ({sr_net:.4f}).  "
            f"Cost model has a sign error."
        )
