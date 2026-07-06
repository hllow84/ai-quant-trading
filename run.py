"""
run.py — CLI entry point for the full factor research pipeline (spec §9).

Usage
-----
  python run.py --factor <name> --asset BTC/USDT --venue binance \\
                --start 2020-01-01 --end 2025-12-31 [--direction both]

  # Smoke-test with synthetic data (no ccxt required):
  python run.py --factor synthetic_test --synthetic 10000

Pipeline sequence (spec §9):
  §9.1  Alpha story gate    — halt if no credible mechanism in config/factors.yaml
  §9.2  Distribution analysis — classify, transform, justify
  §9.3  Model selection     — spike / mean-drift / regime from spec
  §9.4  Signal construction — entry/exit/lag (done inside signal model)
  §9.5  Backtest            — full cost model, guard enabled
  §9.6  Optimize            — 2-D plateau selection if param grid defined
  §9.7  Walk-forward        — rolling CV Sharpe, purge/embargo, deflated SR
  §9.8  Verdict             — KEEP / OVERFIT / KILL
  §9.9  Persist             — strategies/<name>/report.md + notes/<name>.md
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

_ROOT          = Path(__file__).parent
_FACTORS_YAML  = _ROOT / "config" / "factors.yaml"
_DEFAULT_OUT   = _ROOT / "strategies"


# ── Alpha story gate ──────────────────────────────────────────────────────────

class NoAlphaStoryError(ValueError):
    """Raised when no credible alpha story exists for the requested factor."""


def _load_factor_spec(factor_name: str) -> dict:
    """Load factor spec from config/factors.yaml. Returns {} if absent."""
    try:
        import yaml
        with open(_FACTORS_YAML, encoding="utf-8") as fh:
            specs = yaml.safe_load(fh) or {}
    except Exception:
        specs = {}
    return dict(specs.get(factor_name) or {})


def _check_alpha_story(factor_name: str, spec: dict) -> None:
    """Gate: raise NoAlphaStoryError if no alpha story is defined."""
    if not spec:
        raise NoAlphaStoryError(
            f"No spec found for '{factor_name}' in config/factors.yaml. "
            "Add an alpha_story entry before running — no mechanism, no backtest."
        )
    if not spec.get("alpha_story", "").strip():
        raise NoAlphaStoryError(
            f"Factor '{factor_name}' has no alpha_story. "
            "State the mechanism, who is on the other side, and why the edge "
            "persists. No credible mechanism = no backtest."
        )


# ── Data loading ──────────────────────────────────────────────────────────────

def _make_synthetic(n: int, seed: int = 42) -> tuple[pd.Series, pd.Series, None]:
    """Generate n bars of synthetic AR(1) factor + uncorrelated returns."""
    rng  = np.random.default_rng(seed)
    idx  = pd.date_range("2020-01-01", periods=n, freq="h", tz="UTC")
    vals = np.zeros(n)
    vals[0] = rng.normal(0, 0.5)
    for i in range(1, n):
        vals[i] = 0.5 * vals[i - 1] + rng.normal(0, 0.5)
    factor  = pd.Series(vals, index=idx, name="synthetic")
    returns = pd.Series(rng.normal(0.0001, 0.005, n), index=idx, name="asset_return")
    return factor, returns, None


def _load_factor_data(
    spec: dict,
    asset: str,
    venue: str,
    start: str,
    end: str,
    synthetic_n: int | None,
) -> tuple[pd.Series, pd.Series, pd.Series | None]:
    """
    Return (factor, asset_returns, funding_rates).
    Uses synthetic data when synthetic_n is given or spec source == 'synthetic'.
    """
    if synthetic_n is not None:
        return _make_synthetic(synthetic_n)

    source = spec.get("source", "")

    if source == "synthetic":
        n = 8_760 * 3  # 3 years of 1h bars
        return _make_synthetic(n)

    if source in ("ccxt", "ccxt_spread", "ccxt_funding", "ccxt_ohlcv"):
        sys.path.insert(0, str(_ROOT))
        timeframe = spec.get("timeframe", "1h")

        if source == "ccxt_spread":
            from data.adapters.ccxt_adapter import fetch_ohlcv_spread, SpreadAlignmentError
            sym_a   = spec.get("symbol_a", asset)
            sym_b   = spec.get("symbol_b", asset)
            venue_a = spec.get("venue_a", venue)
            venue_b = spec.get("venue_b", "coinbase")
            factor, returns = fetch_ohlcv_spread(
                sym_a, sym_b, timeframe, start, end, venue_a, venue_b
            )
            # Binance USDT-margined perp funding for held position cost
            fund = None
            try:
                from data.adapters.ccxt_adapter import fetch_funding_rate_history
                perp_symbol = asset.split("/")[0] + "/USDT:USDT"
                fdf = fetch_funding_rate_history(perp_symbol, since=start, until=end, venue=venue)
                if fdf.empty:
                    print(
                        f"\nWARNING: Funding rate fetch returned empty for {perp_symbol} "
                        f"on {venue}. Proceeding with zero funding cost.",
                        file=sys.stderr,
                    )
                else:
                    n_intervals = len(fdf)
                    # Divide by 8: 8h rate distributed across 8 × 1h bars
                    fund = (fdf["funding_rate"].reindex(factor.index).ffill() / 8)
                    print(f"\nFunding loaded : {n_intervals} 8h intervals ({perp_symbol} / {venue})")
            except Exception as _fund_exc:
                print(
                    f"\nWARNING: Funding rate fetch failed ({_fund_exc}). "
                    "Proceeding with zero funding cost.",
                    file=sys.stderr,
                )
            return factor, returns, fund

        elif source == "ccxt_funding":
            from data.adapters.ccxt_adapter import fetch_funding_rate_history, fetch_ohlcv
            symbol_perp = spec.get("symbol", asset.split("/")[0] + "/USDT:USDT")
            # Asset returns from 1h OHLCV
            ohlcv   = fetch_ohlcv(asset, timeframe, since=start, until=end, venue=venue)
            returns = ohlcv["close"].pct_change().rename("asset_return")
            # Funding rate (8h native) ffilled to 1h — point-in-time correct
            fdf = fetch_funding_rate_history(symbol_perp, since=start, until=end, venue=venue)
            if fdf.empty:
                raise ValueError(f"No funding rate data for {symbol_perp} on {venue}.")
            factor = fdf["funding_rate"].reindex(returns.index).ffill().rename("funding_rate")
            # Cost model: per-1h share of the 8h settlement
            fund_cost = (factor / 8).rename("funding_rate_per_bar")
            return factor, returns, fund_cost

        elif source == "ccxt_ohlcv":
            from data.adapters.ccxt_adapter import fetch_ohlcv
            ohlcv   = fetch_ohlcv(asset, timeframe, since=start, until=end, venue=venue)
            returns = ohlcv["close"].pct_change().rename("asset_return")
            # Factor = 1h return (known at bar close; backtest engine applies the
            # 1-bar execution lag). mean_drift MA cross on this detects trend persistence.
            factor  = ohlcv["close"].pct_change().rename("price_momentum")
            return factor, returns, None  # pure spot, no funding cost

        elif source == "ccxt":
            raise NotImplementedError(
                "Source 'ccxt' is reserved. Use ccxt_ohlcv for single-asset price "
                "factors, ccxt_spread for two-venue spreads, or ccxt_funding for "
                "perpetual funding rate factors."
            )

    raise ValueError(
        f"Unknown source '{source}' for factor. "
        "Supported: ccxt_ohlcv, ccxt_spread, ccxt_funding, synthetic."
    )


# ── Signal factory ────────────────────────────────────────────────────────────

def _build_make_signal(
    spec: dict,
    param_overrides: dict | None = None,
    regime_mask: "pd.Series | None" = None,
) -> Callable[[pd.Series], pd.Series]:
    """Build make_signal(normalised_factor) → signal from spec.

    regime_mask: precomputed boolean Series (same index as full factor/returns),
    already lagged ≥1 bar. Only used when signal_model == 'regime_conditional'.
    """
    from research.signals import spike_capture, mean_drift

    model  = spec.get("signal_model", "spike_capture")
    params = dict(spec.get("signal_params", {}))
    if param_overrides:
        params.update(param_overrides)

    _SC_KEYS  = ("z_entry", "z_exit", "window")
    sc_params = {k: params[k] for k in _SC_KEYS if k in params}

    if model in ("spike_capture", "regime_conditional"):
        base_fn = lambda norm: spike_capture(norm, **sc_params)
        if model == "spike_capture" or regime_mask is None:
            return base_fn
        _mask = regime_mask  # closure — full-series boolean, pre-lagged ≥1 bar
        def _gated(norm: pd.Series) -> pd.Series:
            gate = _mask.reindex(norm.index).fillna(False).astype(int)
            return (base_fn(norm) * gate).astype(int)
        return _gated

    if model == "mean_drift":
        return lambda norm: mean_drift(norm, **params)
    raise ValueError(
        f"Unknown signal_model '{model}'. "
        "Supported: spike_capture, regime_conditional, mean_drift."
    )


def _signal_model_str(spec: dict) -> str:
    model  = spec.get("signal_model", "spike_capture")
    params = spec.get("signal_params", {})
    if model == "regime_conditional":
        _SC_KEYS  = ("z_entry", "z_exit", "window")
        sc_params = {k: params[k] for k in _SC_KEYS if k in params}
        rv_window   = params.get("rv_window",   336)
        rv_quantile = params.get("rv_quantile", 0.5)
        base_str = f"spike_capture({', '.join(f'{k}={v}' for k, v in sc_params.items())})"
        return (f"regime_conditional(base={base_str}, "
                f"gate=rv{rv_window}>=p{rv_quantile:.0%})")
    return f"{model}({', '.join(f'{k}={v}' for k, v in params.items())})"


# ── Regime helpers ────────────────────────────────────────────────────────────

def _rolling_pctrank_series(s: pd.Series, window: int) -> pd.Series:
    """Rolling percentile rank of current bar vs past window bars. Output in [0,1]."""
    min_p = max(window // 4, 5)
    return s.rolling(window, min_periods=min_p).apply(
        lambda x: float((x[:-1] < x[-1]).mean()) if len(x) > 1 else 0.5,
        raw=True,
    )


def _build_regime_mask(
    asset_returns: pd.Series,
    rv_window: int = 336,
    rv_quantile: float = 0.5,
    bars_per_year: int = 8_760,
) -> pd.Series:
    """
    Boolean regime mask derived from realized volatility (past-only, lagged 1 bar).

    Computation at each bar t:
      1. rv[t]  = std(returns[t-rv_window+1 .. t]) * sqrt(bars_per_year)
      2. pct[t] = percentile rank of rv[t] vs rv[t-rv_window+1 .. t-1]
      3. mask[t] = (pct[t] >= rv_quantile)
    Then mask is shifted 1 bar so signal at bar t sees the regime as of bar t-1.
    """
    min_p = max(rv_window // 4, 5)
    rv    = (
        asset_returns
        .rolling(rv_window, min_periods=min_p)
        .std()
        .mul(np.sqrt(bars_per_year))
    )
    pct  = _rolling_pctrank_series(rv, window=rv_window)
    # .shift(1) on bool Series yields object dtype in pandas (NaN can't be bool);
    # .fillna(False).astype(bool) restores proper bool dtype for safe ~ inversion.
    mask = (pct >= rv_quantile).shift(1).fillna(False).astype(bool)
    return mask


def _run_regime_analysis(
    factor:        pd.Series,
    asset_returns: pd.Series,
    spec:          dict,
    regime_mask:   pd.Series,
    funding_rates: "pd.Series | None",
    bars_per_year: int,
    gated_wf:      object,
    best_params:   "dict | None",
    wf_kw:         dict,
) -> str:
    """
    Run ungated spike_capture baseline through the same WF folds.
    Split stitched OOS returns by the precomputed regime mask.

    Returns formatted analysis text.

    The key test: if ungated signal has positive Sharpe in-regime and negative
    out-of-regime, the regime genuinely discriminates. If per-fold regime coverage
    correlates strongly (|r|>0.5) with fold performance, the gate is a calendar
    proxy — report as OVERFIT/KILL regardless of gated Sharpe.
    """
    from research import walkforward
    from research.metrics import sharpe as _sharpe

    base_make = _build_make_signal(spec, best_params, regime_mask=None)
    print("\n  Running ungated baseline walk-forward for in/out-regime comparison...")
    base_wf = walkforward.run(
        factor, asset_returns, base_make,
        funding_rates=funding_rates,
        bars_per_year=bars_per_year,
        **wf_kw,
    )

    # Align stitched OOS returns with regime mask (same datetime index)
    gated_oos     = gated_wf.oos_returns
    base_oos      = base_wf.oos_returns.reindex(gated_oos.index)
    oos_in_regime = regime_mask.reindex(gated_oos.index).fillna(False).astype(bool)

    n_total = len(oos_in_regime)
    n_in    = int(oos_in_regime.sum())
    n_out   = n_total - n_in
    pct_in  = n_in / n_total if n_total > 0 else 0.0

    # Ungated in/out Sharpe — the informative split
    base_in_ret  = base_oos[oos_in_regime]
    base_out_ret = base_oos[~oos_in_regime]
    sr_base_in   = _sharpe(base_in_ret,  bars_per_year) if len(base_in_ret)  > 10 else float("nan")
    sr_base_out  = _sharpe(base_out_ret, bars_per_year) if len(base_out_ret) > 10 else float("nan")

    # Gated in-regime Sharpe (gate is transparent in-regime, so ≈ base_in)
    gated_in_ret = gated_oos[oos_in_regime]
    sr_gated_in  = _sharpe(gated_in_ret, bars_per_year) if len(gated_in_ret) > 10 else float("nan")

    # Per-fold: regime coverage % and SR comparison
    folds     = gated_wf.folds
    fold_rows = []
    for i, fold in enumerate(folds):
        fold_regime = regime_mask.iloc[fold.test_start:fold.test_end]
        fold_pct    = float(fold_regime.mean())
        sr_g        = gated_wf.fold_sharpes_oos[i]
        sr_b        = base_wf.fold_sharpes_oos[i]
        fold_rows.append((fold.fold_idx, fold_pct, sr_b, sr_g))

    # Calendar proxy test: corr(regime coverage per fold, ungated fold SR)
    pcts       = [r[1] for r in fold_rows]
    srs_base   = [r[2] for r in fold_rows]
    valid      = [(p, s) for p, s in zip(pcts, srs_base) if np.isfinite(p) and np.isfinite(s)]
    if len(valid) >= 3:
        pv, sv = zip(*valid)
        corr = float(np.corrcoef(pv, sv)[0, 1])
    else:
        corr = float("nan")

    calendar_proxy = np.isfinite(corr) and abs(corr) > 0.5
    genuine_edge   = (
        np.isfinite(sr_base_in)  and sr_base_in  > 0.3 and
        np.isfinite(sr_base_out) and sr_base_out < 0.0
    )
    partial_edge   = (
        not genuine_edge and
        np.isfinite(sr_base_in) and np.isfinite(sr_base_out) and
        sr_base_in > sr_base_out + 0.3
    )

    if calendar_proxy:
        interp = (
            "CALENDAR PROXY: regime coverage correlates strongly with fold performance\n"
            "(|r|>0.5). The gate selects historically good calendar periods, not a\n"
            "live-observable market state. Hindsight masquerading as a signal. KILL."
        )
    elif genuine_edge:
        interp = (
            "GENUINE CONDITIONAL EDGE: ungated signal is positive in-regime and\n"
            "negative out-of-regime. The realized-vol gate discriminates on a live-\n"
            "observable indicator and is not a calendar proxy. Edge is legitimately\n"
            "conditional on regime."
        )
    elif partial_edge:
        interp = (
            "PARTIAL CONDITIONAL EDGE: in-regime SR > out-regime SR by >0.3, but\n"
            "out-regime SR is not clearly negative. Gate reduces low-quality trades\n"
            "without specifically blocking losing periods. Proceed with caution."
        )
    else:
        interp = (
            "NO GENUINE CONDITIONAL EDGE: regime does not meaningfully discriminate.\n"
            "In-regime and out-regime ungated SRs are similar or both non-positive.\n"
            "The regime gate does not add value."
        )

    sf = lambda x: f"{x:>+.3f}" if np.isfinite(x) else "   NaN"
    lines = [
        f"  OOS bars : {n_total:,} total  |  "
        f"{n_in:,} in-regime ({pct_in:.1%})  |  "
        f"{n_out:,} out-of-regime ({1-pct_in:.1%})",
        "",
        f"  {'Signal':<32}  {'In-regime SR':>12}  {'Out-regime SR':>13}",
        f"  {'-'*32}  {'-'*12}  {'-'*13}",
        f"  {'Ungated spike_capture':<32}  {sf(sr_base_in):>12}  {sf(sr_base_out):>13}",
        f"  {'Regime-gated (active bars only)':<32}  {sf(sr_gated_in):>12}  {'(gate=0)':>13}",
        "",
        f"  Regime-coverage / fold-SR corr : {corr:>+.3f}"
        + ("  [FAIL |r|>0.5 — calendar proxy]" if calendar_proxy else "  [OK |r|<=0.5]"),
        "",
        "  Per-fold breakdown:",
        f"  {'Fold':>5}  {'%In-regime':>10}  {'Ungated OOS SR':>14}  {'Gated OOS SR':>12}",
        f"  {'-'*5}  {'-'*10}  {'-'*14}  {'-'*12}",
    ]
    for fold_idx, pct, sr_b, sr_g in fold_rows:
        lines.append(
            f"  {fold_idx:>5}  {pct:>10.1%}  {sf(sr_b):>14}  {sf(sr_g):>12}"
        )
    lines += ["", "  Interpretation:"]
    for il in interp.split("\n"):
        lines.append(f"  {il}")

    return "\n".join(lines)


# ── Pipeline result ───────────────────────────────────────────────────────────

@dataclass
class PipelineResult:
    factor_name: str
    verdict:     str
    reasons:     list[str]
    wf_result:   object            # WalkForwardResult
    opt_result:  object            # OptimizeResult | None
    report_path: Path
    note_path:   Path


# ── Main pipeline function ────────────────────────────────────────────────────

def _hdr(title: str) -> None:
    bar = "=" * (len(title) + 4)
    print(f"\n{bar}\n  {title}\n{bar}")


def run_pipeline(
    factor_name:   str,
    factor:        pd.Series,
    asset_returns: pd.Series,
    spec:          dict,
    *,
    funding_rates: pd.Series | None = None,
    train_bars:    int | None = None,
    test_bars:     int | None = None,
    embargo_bars:  int | None = None,
    fee_bps:       float | None = None,
    slippage_bps:  float | None = None,
    direction:     str = "both",
    out_dir:       Path | None = None,
    notes_root:    Path | None = None,
    bars_per_year: int = 8_760,
) -> PipelineResult:
    """
    Execute the §9 pipeline on pre-loaded factor + returns.
    Prints progress to stdout.  Returns PipelineResult.

    This is the testable core — main() parses CLI args, loads data, calls this.

    Parameters
    ----------
    out_dir    : root directory for report artifacts (default: <project>/strategies)
    notes_root : root for notes/ directory (default: out_dir.parent)
    """
    from research import preprocess, backtest, walkforward, optimize as opt_mod
    from research.metrics import sharpe, max_drawdown
    from research.report import FactorReportData, save as _save, append_note, _verdict

    out_dir    = out_dir    or _DEFAULT_OUT
    notes_root = notes_root or out_dir.parent

    # ── §9.1 ─────────────────────────────────────────────────────────────────
    _hdr(f"Factor: {factor_name}")
    print(f"\nAlpha Story:\n{spec['alpha_story'].strip()}")

    # ── §9.2 Distribution analysis ────────────────────────────────────────────
    _hdr("§9.2 Distribution Analysis")
    norm_full, classification, justification, stats = preprocess.preprocess(factor)
    print(f"Classification : {classification}")
    print(f"Skewness       : {stats.get('skewness', float('nan')):.3f}")
    print(f"ADF p-value    : {stats.get('adf_p', float('nan')):.4f}")
    print(f"% Negative     : {stats.get('pct_negative', float('nan')):.1%}")
    print(f"Transform      : {justification}")

    # ── §9.3 Model selection ─────────────────────────────────────────────────
    _hdr("§9.3 Signal Model")
    model_str = _signal_model_str(spec)

    # Regime mask — computed once on full series (past-only, lagged ≥1 bar).
    # None for spike_capture / mean_drift; populated only for regime_conditional.
    regime_mask = None
    if spec.get("signal_model") == "regime_conditional":
        rv_window   = int(spec.get("signal_params", {}).get("rv_window",   336))
        rv_quantile = float(spec.get("signal_params", {}).get("rv_quantile", 0.5))
        regime_mask = _build_regime_mask(asset_returns, rv_window, rv_quantile, bars_per_year)
        n_in_full   = int(regime_mask.sum())
        print(f"Regime gate   : realized-vol (past {rv_window} bars) >= "
              f"{rv_quantile:.0%} rolling pct-rank, lagged 1 bar")
        print(f"In-regime bars: {n_in_full:,} / {len(regime_mask):,} "
              f"({float(regime_mask.mean()):.1%} of full series)")

    make_signal = _build_make_signal(spec, regime_mask=regime_mask)
    print(f"Model : {model_str}")

    # ── §9.5 Full-period backtest ─────────────────────────────────────────────
    _hdr("§9.5 Full-period Backtest")
    full_signal = make_signal(norm_full)
    bt_result   = backtest.run(
        full_signal, asset_returns,
        funding_rates = funding_rates,
        fee_bps       = fee_bps      if fee_bps      is not None else 7.0,
        slippage_bps  = slippage_bps if slippage_bps is not None else 5.0,
        direction     = direction,
    )
    print(f"Full-period Sharpe : {sharpe(bt_result['net_ret'], bars_per_year):.3f}")
    print(f"Max Drawdown       : {max_drawdown(bt_result['equity']):.1%}")
    total_fund_cost = float(bt_result['fund_cost'].sum())
    if total_fund_cost == 0.0:
        print("Funding cost       : 0.00000 (no funding data — costs understated)")
    else:
        funded_bars = int((bt_result['fund_cost'] != 0).sum())
        print(f"Funding cost       : {total_fund_cost:.5f} total  ({funded_bars} bars with non-zero funding)")

    # ── §9.6 Optimise ─────────────────────────────────────────────────────────
    _hdr("§9.6 Optimise")
    param_grid       = dict(spec.get("optimize", {}))
    opt_result       = None
    best_make_signal = make_signal

    _wf_kw: dict = {}
    if train_bars   is not None: _wf_kw["train_bars"]   = train_bars
    if test_bars    is not None: _wf_kw["test_bars"]     = test_bars
    if embargo_bars is not None: _wf_kw["embargo_bars"]  = embargo_bars
    if fee_bps      is not None: _wf_kw["fee_bps"]       = fee_bps
    if slippage_bps is not None: _wf_kw["slippage_bps"]  = slippage_bps

    if len(param_grid) == 2:
        opt_result = opt_mod.run(
            factor, asset_returns,
            make_signal   = lambda norm, **p: _build_make_signal(spec, p, regime_mask=regime_mask)(norm),
            param_grid    = param_grid,
            funding_rates = funding_rates,
            bars_per_year = bars_per_year,
            wf_kwargs     = _wf_kw if _wf_kw else None,
        )
        print(opt_result.report())
        best_make_signal = _build_make_signal(spec, opt_result.best_params, regime_mask=regime_mask)
    elif param_grid:
        print(f"Skipping optimize: param_grid has {len(param_grid)} key(s), need exactly 2.")
    else:
        print("No optimize grid in spec — skipping.")

    # ── §9.7 Walk-forward ─────────────────────────────────────────────────────
    _hdr("§9.7 Walk-forward Validation")
    wf_result = walkforward.run(
        factor, asset_returns, best_make_signal,
        funding_rates = funding_rates,
        bars_per_year = bars_per_year,
        **_wf_kw,
    )
    print(wf_result.report())

    # ── §9.8 Verdict ──────────────────────────────────────────────────────────
    _hdr("§9.8 Verdict")
    n_configs  = opt_result.n_configs if opt_result is not None else 1
    fac_stats  = {"raw_sample": factor.values[:500].tolist(), **stats}

    # Regime analysis runs before report_data creation so the text is embedded
    # in the saved report.  Prints immediately; verdict section follows.
    regime_analysis_text = ""
    if regime_mask is not None:
        _hdr("Regime Analysis — The Real Test")
        regime_analysis_text = _run_regime_analysis(
            factor        = factor,
            asset_returns = asset_returns,
            spec          = spec,
            regime_mask   = regime_mask,
            funding_rates = funding_rates,
            bars_per_year = bars_per_year,
            gated_wf      = wf_result,
            best_params   = opt_result.best_params if opt_result is not None else None,
            wf_kw         = _wf_kw,
        )
        print(regime_analysis_text)
        _hdr("§9.8 Verdict (continued)")

    report_data = FactorReportData(
        factor_name             = factor_name,
        asset                   = spec.get("asset", "BTC/USDT"),
        alpha_story             = spec["alpha_story"].strip(),
        classification          = classification,
        transform_justification = justification,
        factor_stats            = fac_stats,
        signal_model            = model_str,
        bt_result               = bt_result,
        wf_result               = wf_result,
        opt_result              = opt_result,
        point_in_time_clean     = bool(spec.get("point_in_time_clean", True)),
        bars_per_year           = bars_per_year,
        n_configs               = n_configs,
        regime_analysis_text    = regime_analysis_text,
    )
    verdict, reasons = _verdict(report_data)

    # Headline numbers — order is fixed: DSR, positive folds, IS->OOS degradation
    from research.metrics import deflated_sharpe_ratio
    oos_ret = wf_result.oos_returns.dropna()
    try:
        dsr_prob, e_max_sr = deflated_sharpe_ratio(
            sr_best             = wf_result.cv_sharpe,
            sr_trials           = (
                opt_result.sharpe_grid.flatten().tolist()
                if opt_result is not None else [wf_result.cv_sharpe]
            ),
            n_obs               = max(len(oos_ret), 2),
            skewness            = float(oos_ret.skew()) if len(oos_ret) > 3 else 0.0,
            excess_kurtosis     = float(oos_ret.kurtosis()) if len(oos_ret) > 3 else 0.0,
        )
        dsr_line = f"{dsr_prob:.4f}  (E[max SR]={e_max_sr:.3f})"
    except Exception:
        dsr_line = "n/a"

    n_folds   = len(wf_result.folds)
    pos_pct   = wf_result.n_positive_folds / n_folds if n_folds > 0 else 0.0
    degrad    = wf_result.is_oos_degradation

    # ── Headline numbers (user-requested order) ───────────────────────────────
    print()
    print("=" * 52)
    print(f"  RESULT: {factor_name}")
    print("=" * 52)
    print(f"  1. Deflated Sharpe prob  : {dsr_line}")
    print(f"  2. Positive folds        : {wf_result.n_positive_folds}/{n_folds} ({pos_pct:.0%})")
    print(f"  3. IS -> OOS degradation : {degrad:+.3f}")
    print(f"  Verdict                  : {verdict}")
    for r in reasons:
        print(f"     - {r}")
    print("=" * 52)

    # ── §9.9 Persist ──────────────────────────────────────────────────────────
    _hdr("§9.9 Persist")
    report_path = _save(report_data, root=out_dir)
    print(f"Report saved : {report_path}")

    note = (
        f"Verdict: {verdict}. "
        f"CV Sharpe = {wf_result.cv_sharpe:.3f}, "
        f"positive folds = {wf_result.n_positive_folds}/{len(wf_result.folds)}, "
        f"max DD = {wf_result.cv_max_drawdown:.1%}. "
        f"Classification: {classification}. Signal: {model_str}."
    )
    note_path = append_note(factor_name, note, root=notes_root)
    print(f"Note saved   : {note_path}")

    return PipelineResult(
        factor_name = factor_name,
        verdict     = verdict,
        reasons     = reasons,
        wf_result   = wf_result,
        opt_result  = opt_result,
        report_path = report_path,
        note_path   = note_path,
    )


# ── CLI ───────────────────────────────────────────────────────────────────────

def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="run.py",
        description="Run the full factor research pipeline (spec §9).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              python run.py --factor coinbase_premium_gap --asset BTC/USDT --venue binance
              python run.py --factor synthetic_test --synthetic 10000
              python run.py --factor synthetic_test --synthetic 3000 \\
                            --train-bars 500 --test-bars 200 --embargo-bars 50
        """),
    )
    p.add_argument("--factor",       required=True,
                   help="Factor name from config/factors.yaml")
    p.add_argument("--asset",        default="BTC/USDT",
                   help="Asset symbol (default BTC/USDT)")
    p.add_argument("--venue",        default="binance",
                   help="Reference venue for asset_returns (default binance)")
    p.add_argument("--start",        default="2020-01-01",
                   help="Fetch start date YYYY-MM-DD")
    p.add_argument("--end",          default="2025-12-31",
                   help="Fetch end date YYYY-MM-DD")
    p.add_argument("--direction",    default="both",
                   choices=["long", "short", "both"])
    p.add_argument("--synthetic",    type=int, default=None, metavar="N",
                   help="Use N bars of synthetic data (no ccxt fetch)")
    p.add_argument("--train-bars",   type=int, default=None,
                   help="Override walk-forward train window (bars)")
    p.add_argument("--test-bars",    type=int, default=None,
                   help="Override walk-forward test window (bars)")
    p.add_argument("--embargo-bars", type=int, default=None,
                   help="Override purge/embargo size (bars)")
    p.add_argument("--fee-bps",      type=float, default=None,
                   help="Override taker fee in bps")
    p.add_argument("--slippage-bps", type=float, default=None,
                   help="Override slippage in bps")
    p.add_argument("--out",          default=None,
                   help="Output root directory (default: strategies/)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 on success, 1 on error."""
    # Windows terminal defaults to cp1252; research module uses Unicode box chars.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = _parse_args(argv)

    # §9.1 — alpha story gate
    spec = _load_factor_spec(args.factor)
    try:
        _check_alpha_story(args.factor, spec)
    except NoAlphaStoryError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    # Load data
    try:
        factor, asset_returns, funding_rates = _load_factor_data(
            spec, args.asset, args.venue,
            args.start, args.end,
            synthetic_n=args.synthetic,
        )
    except Exception as exc:
        print(f"\nERROR loading factor data: {exc}", file=sys.stderr)
        return 1

    out_dir    = Path(args.out) if args.out else _DEFAULT_OUT
    notes_root = out_dir.parent

    try:
        run_pipeline(
            factor_name   = args.factor,
            factor        = factor,
            asset_returns = asset_returns,
            spec          = spec,
            funding_rates = funding_rates,
            train_bars    = args.train_bars,
            test_bars     = args.test_bars,
            embargo_bars  = args.embargo_bars,
            fee_bps       = args.fee_bps,
            slippage_bps  = args.slippage_bps,
            direction     = args.direction,
            out_dir       = out_dir,
            notes_root    = notes_root,
        )
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
