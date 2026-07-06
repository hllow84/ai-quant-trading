"""
walkforward.py — Rolling walk-forward validation with leakage control (spec §8.2).

Train-fit, test-apply contract
───────────────────────────────
  Factor classification AND normalisation statistics (median, MAD, log-median, …)
  are fitted on the training window ONLY, then applied FROZEN to the test window.
  Per-bar rolling being past-only within a single series pass is NOT sufficient:
  calling classify() or computing global stats on the full series leaks the test
  distribution back into the scaling used in training.

Purge + embargo
────────────────
  Last embargo_bars of the training window are excluded from fitting (purge).
  First embargo_bars of the test window are excluded from evaluation (embargo).
  Both are sized to at least the transform window (default 168 bars), so the
  largest rolling lookback can never straddle the train/test boundary.
  Gap between effective train end and test start = 2 × embargo_bars.

guard_look_ahead is called inside every fold's bt_run call (guard=True, the
engine default). If a signal shows anomalous correlation with next-bar returns,
the fold is skipped and its Sharpe recorded as NaN.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from research.backtest import run as _bt_run, LookAheadError
from research.metrics import sharpe as _sharpe, max_drawdown as _mdd
from research.preprocess import classify

_CONFIG_PATH = Path(__file__).parent.parent / "config" / "backtest.yaml"
_HOURS_PER_MONTH = 30 * 24   # approximate; converts config months → bars


# ── Config loader ─────────────────────────────────────────────────────────────

def _load_wf_config() -> dict:
    try:
        import yaml
        with open(_CONFIG_PATH) as fh:
            cfg = yaml.safe_load(fh)
    except Exception:
        cfg = {}
    wf    = cfg.get("walkforward", {})
    costs = cfg.get("costs", {})
    return {
        "train_bars":   int(wf.get("train_months", 6) * _HOURS_PER_MONTH),
        "test_bars":    int(wf.get("test_months",  3) * _HOURS_PER_MONTH),
        "step_bars":    int(wf.get("step_months",  3) * _HOURS_PER_MONTH),
        "embargo_bars": int(wf.get("embargo_bars", 168)),
        "fee_bps":      float(costs.get("default_fee_bps", 7.0)),
        "slippage_bps": float(costs.get("default_slippage_bps", 5.0)),
    }


# ── Frozen normaliser ─────────────────────────────────────────────────────────

def _series_mad(s: pd.Series) -> float:
    """Scalar MAD: median of absolute deviations from the median."""
    return float((s - s.median()).abs().median())


class FrozenNormalizer:
    """
    Fit normalisation statistics on the training window; apply them as frozen
    constants to any subsequent window (test, live).

    This prevents the test-period distribution from influencing the scaling used
    in training — a form of look-ahead that rolling-window stats alone do not
    prevent once classify() or global stats are computed on the full series.
    """

    MAD_SCALE = 1.4826   # converts MAD to σ-equivalent for Gaussian data

    def __init__(self) -> None:
        self.classification: str | None = None
        self._stats: dict = {}
        self._fitted = False

    # ── fit ──────────────────────────────────────────────────────────────────

    def fit(self, train: pd.Series) -> "FrozenNormalizer":
        """
        Classify and fit scaling statistics on training data only.
        Raises ValueError if training window is too short.
        """
        s = train.dropna()
        if len(s) < 30:
            raise ValueError(
                f"Training window too short ({len(s)} bars < 30) to fit normaliser."
            )
        self.classification, _ = classify(s)

        if self.classification == "continuous_nonstationary":
            diff = s.diff().dropna()
            self._stats = {
                "kind":             "diff_robust_z",
                "diff_median":      float(diff.median()),
                "diff_mad":         _series_mad(diff),
                "last_train_value": float(s.iloc[-1]),
            }

        elif self.classification in ("signed", "continuous_stationary"):
            self._stats = {
                "kind":   "robust_z",
                "median": float(s.median()),
                "mad":    _series_mad(s),
            }

        elif self.classification == "skewed":
            if (s >= 0).all():
                log_s = s.apply(np.log1p)
                self._stats = {
                    "kind":       "log_robust_z",
                    "log_median": float(log_s.median()),
                    "log_mad":    _series_mad(log_s),
                }
            else:
                self._stats = {
                    "kind":         "pctrank",
                    "train_values": s.values.copy(),
                }

        self._fitted = True
        return self

    # ── transform ─────────────────────────────────────────────────────────────

    def transform(
        self,
        data: pd.Series,
        prev_value: float | None = None,
    ) -> pd.Series:
        """
        Apply frozen statistics to new data.  No data from `data` enters the
        statistics — this is safe to call on test or live data.

        Parameters
        ----------
        data       : raw factor values to normalise
        prev_value : for continuous_nonstationary only — the bar immediately
                     before data.iloc[0], used so the first diff is defined.
                     If None, the first diff is NaN (signal warm-up handles it).
        """
        if not self._fitted:
            raise RuntimeError("Call fit() before transform().")

        cls = self.classification

        if cls == "continuous_nonstationary":
            if prev_value is not None:
                first_diff = float(data.iloc[0]) - prev_value
                rest_diff  = data.diff().iloc[1:]
                diff = pd.concat(
                    [pd.Series([first_diff], index=[data.index[0]]), rest_diff]
                )
            else:
                diff = data.diff()
            scale = max(self._stats["diff_mad"] * self.MAD_SCALE, 1e-12)
            return (diff - self._stats["diff_median"]) / scale

        elif cls in ("signed", "continuous_stationary"):
            scale = max(self._stats["mad"] * self.MAD_SCALE, 1e-12)
            return (data - self._stats["median"]) / scale

        elif cls == "skewed":
            if self._stats["kind"] == "log_robust_z":
                log_data = data.apply(lambda x: np.log1p(max(x, 0.0)))
                scale    = max(self._stats["log_mad"] * self.MAD_SCALE, 1e-12)
                return (log_data - self._stats["log_median"]) / scale
            else:
                train_vals = self._stats["train_values"]
                ranks      = data.apply(lambda x: float((train_vals < x).mean()))
                return (ranks - 0.5) * 2.0

        raise ValueError(f"Unknown classification: {cls!r}")


# ── Fold geometry ─────────────────────────────────────────────────────────────

@dataclass
class FoldSpec:
    """Integer bar-positions (iloc) for one walk-forward fold."""
    fold_idx:      int
    train_start:   int   # first bar of training window
    train_fit_end: int   # exclusive; purge removes [train_fit_end, train_fit_end+embargo)
    test_start:    int   # first bar of OOS evaluation (after embargo)
    test_end:      int   # exclusive

    @property
    def gap(self) -> int:
        """Bars between effective train end and test start (= 2 × embargo_bars)."""
        return self.test_start - self.train_fit_end


def _generate_folds(
    n_bars:      int,
    train_bars:  int,
    test_bars:   int,
    step_bars:   int,
    embargo_bars: int,
) -> list[FoldSpec]:
    """
    Generate fold boundaries for a rolling walk-forward.

    Each fold:
      train_fit_end  = fold_start + train_bars - embargo_bars   (purge last K)
      test_start     = fold_start + train_bars + embargo_bars   (skip first K)
      gap            = test_start - train_fit_end = 2 × embargo_bars

    A lookback window of size ≤ embargo_bars starting at test_start can reach
    back at most to fold_start + train_bars (the raw train end), which is still
    within the training window — no lookback straddles the boundary.
    """
    folds: list[FoldSpec] = []
    fold_start = 0
    fold_idx   = 0

    while True:
        train_fit_end = fold_start + train_bars - embargo_bars
        test_start    = fold_start + train_bars + embargo_bars
        test_end      = test_start + test_bars

        if test_end > n_bars:
            break
        if train_fit_end <= fold_start + 30:    # need ≥ 30 bars to classify
            break

        folds.append(FoldSpec(
            fold_idx      = fold_idx,
            train_start   = fold_start,
            train_fit_end = train_fit_end,
            test_start    = test_start,
            test_end      = test_end,
        ))
        fold_start += step_bars
        fold_idx   += 1

    return folds


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class WalkForwardResult:
    folds:              list[FoldSpec]
    fold_sharpes_is:    list[float]
    fold_sharpes_oos:   list[float]
    oos_returns:        pd.Series
    oos_equity:         pd.Series
    cv_sharpe:          float
    cv_max_drawdown:    float
    n_positive_folds:   int
    is_oos_degradation: float
    classification:     str | None
    bars_per_year:      int

    def report(self) -> str:
        """Per-fold Sharpe table + aggregate metrics."""
        lines = [
            "Walk-forward report",
            "=" * 52,
            f"{'Fold':>5}  {'Train bars':>10}  {'Test bars':>9}  {'IS SR':>7}  {'OOS SR':>7}",
            "-" * 52,
        ]
        for i, fold in enumerate(self.folds):
            sr_is  = self.fold_sharpes_is[i]
            sr_oos = self.fold_sharpes_oos[i]
            is_str  = f"{sr_is:>7.3f}"  if np.isfinite(sr_is)  else "    NaN"
            oos_str = f"{sr_oos:>7.3f}" if np.isfinite(sr_oos) else "    NaN"
            lines.append(
                f"{fold.fold_idx:>5}  {fold.train_fit_end - fold.train_start:>10}  "
                f"{fold.test_end - fold.test_start:>9}  {is_str}  {oos_str}"
            )
        lines += [
            "-" * 52,
            f"CV Sharpe (stitched OOS):  {self.cv_sharpe:>7.3f}",
            f"Max drawdown (OOS):        {self.cv_max_drawdown:>7.1%}",
            f"Positive folds:            {self.n_positive_folds}/{len(self.folds)}",
            f"IS->OOS degradation:       {self.is_oos_degradation:>+7.3f}",
            f"Classification (fold 0):   {self.classification}",
        ]
        return "\n".join(lines)


# ── Main entry point ──────────────────────────────────────────────────────────

def run(
    factor:        pd.Series,
    asset_returns: pd.Series,
    make_signal:   Callable[[pd.Series], pd.Series],
    funding_rates: pd.Series | None = None,
    train_bars:    int | None = None,
    test_bars:     int | None = None,
    step_bars:     int | None = None,
    embargo_bars:  int | None = None,
    fee_bps:       float | None = None,
    slippage_bps:  float | None = None,
    bars_per_year: int = 8_760,
) -> WalkForwardResult:
    """
    Rolling walk-forward validation.

    Parameters
    ----------
    factor        : raw factor series (same index as asset_returns)
    asset_returns : bar returns of the underlying asset
    make_signal   : callable(normalised_factor: pd.Series) → pd.Series of {-1, 0, +1}
                    called once per fold on both IS and OOS normalised data.
    funding_rates : optional perp funding rate (same index)
    train_bars … slippage_bps : override values from config/backtest.yaml
    bars_per_year : for Sharpe annualisation (default 8760 = hourly)

    Returns
    -------
    WalkForwardResult — per-fold metrics + stitched OOS equity curve
    """
    cfg          = _load_wf_config()
    train_bars   = train_bars   if train_bars   is not None else cfg["train_bars"]
    test_bars    = test_bars    if test_bars    is not None else cfg["test_bars"]
    step_bars    = step_bars    if step_bars    is not None else cfg["step_bars"]
    embargo_bars = embargo_bars if embargo_bars is not None else cfg["embargo_bars"]
    fee_bps      = fee_bps      if fee_bps      is not None else cfg["fee_bps"]
    slippage_bps = slippage_bps if slippage_bps is not None else cfg["slippage_bps"]

    n     = len(factor)
    folds = _generate_folds(n, train_bars, test_bars, step_bars, embargo_bars)

    if not folds:
        raise ValueError(
            f"No complete folds with n={n}, train={train_bars}, test={test_bars}, "
            f"embargo={embargo_bars}. Provide more data or reduce window sizes."
        )

    fold_sharpes_is:  list[float] = []
    fold_sharpes_oos: list[float] = []
    oos_ret_segments: list[pd.Series] = []
    first_cls: str | None = None

    for fold in folds:
        # ── Slice data ───────────────────────────────────────────────────────
        train_fac  = factor.iloc[fold.train_start : fold.train_fit_end]
        test_fac   = factor.iloc[fold.test_start  : fold.test_end]
        is_ret     = asset_returns.iloc[fold.train_start : fold.train_fit_end]
        oos_ret    = asset_returns.iloc[fold.test_start  : fold.test_end]
        is_fund    = (funding_rates.iloc[fold.train_start : fold.train_fit_end]
                      if funding_rates is not None else None)
        oos_fund   = (funding_rates.iloc[fold.test_start  : fold.test_end]
                      if funding_rates is not None else None)

        # ── Fit normaliser on training data ONLY ─────────────────────────────
        norm = FrozenNormalizer().fit(train_fac)
        if first_cls is None:
            first_cls = norm.classification

        # ── IS backtest ───────────────────────────────────────────────────────
        # IS transform: no prev_value; first diff bar = NaN → signal warm-up
        try:
            is_norm   = norm.transform(train_fac)
            is_sig    = make_signal(is_norm)
            is_res    = _bt_run(is_sig, is_ret, funding_rates=is_fund,
                                fee_bps=fee_bps, slippage_bps=slippage_bps)
            fold_sharpes_is.append(_sharpe(is_res["net_ret"], bars_per_year))
        except (LookAheadError, Exception):
            fold_sharpes_is.append(float("nan"))

        # ── OOS backtest ──────────────────────────────────────────────────────
        # OOS transform: pass last training value for correct first diff
        prev_val = float(train_fac.iloc[-1])
        try:
            oos_norm  = norm.transform(test_fac, prev_value=prev_val)
            oos_sig   = make_signal(oos_norm)
            oos_res   = _bt_run(oos_sig, oos_ret, funding_rates=oos_fund,
                                fee_bps=fee_bps, slippage_bps=slippage_bps)
            fold_sharpes_oos.append(_sharpe(oos_res["net_ret"], bars_per_year))
            oos_ret_segments.append(oos_res["net_ret"])
        except (LookAheadError, Exception):
            fold_sharpes_oos.append(float("nan"))

    # ── Stitch OOS equity ─────────────────────────────────────────────────────
    oos_returns_cat = (
        pd.concat(oos_ret_segments)
        if oos_ret_segments
        else pd.Series(dtype=float)
    )
    oos_equity = (1 + oos_returns_cat).cumprod()

    # ── Aggregate metrics ─────────────────────────────────────────────────────
    cv_sharpe    = _sharpe(oos_returns_cat, bars_per_year)
    cv_max_dd    = _mdd(oos_equity) if len(oos_equity) > 0 else 0.0
    valid_is     = [s for s in fold_sharpes_is  if np.isfinite(s)]
    valid_oos    = [s for s in fold_sharpes_oos if np.isfinite(s)]
    n_positive   = sum(1 for s in valid_oos if s > 0)
    is_oos_deg   = (float(np.mean(valid_is) - np.mean(valid_oos))
                    if valid_is and valid_oos else float("nan"))

    return WalkForwardResult(
        folds              = folds,
        fold_sharpes_is    = fold_sharpes_is,
        fold_sharpes_oos   = fold_sharpes_oos,
        oos_returns        = oos_returns_cat,
        oos_equity         = oos_equity,
        cv_sharpe          = cv_sharpe,
        cv_max_drawdown    = cv_max_dd,
        n_positive_folds   = n_positive,
        is_oos_degradation = is_oos_deg,
        classification     = first_cls,
        bars_per_year      = bars_per_year,
    )
