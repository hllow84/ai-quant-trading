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

    if source in ("ccxt", "ccxt_spread"):
        sys.path.insert(0, str(_ROOT))
        from data.adapters.ccxt_adapter import fetch_ohlcv

        timeframe = spec.get("timeframe", "1h")
        ohlcv     = fetch_ohlcv(asset, timeframe, since=start, until=end, exchange=venue)
        returns   = ohlcv["close"].pct_change().rename("asset_return")

        if source == "ccxt_spread":
            sym_a   = spec.get("symbol_a", asset)
            sym_b   = spec.get("symbol_b", asset)
            venue_a = spec.get("venue_a", venue)
            venue_b = spec.get("venue_b", "coinbase")
            df_a    = fetch_ohlcv(sym_a, timeframe, start, end, venue_a)
            df_b    = fetch_ohlcv(sym_b, timeframe, start, end, venue_b)
            factor  = (df_b["close"] - df_a["close"]).rename("spread")
        else:
            raise NotImplementedError(
                f"Direct ccxt metric for source='{source}' not yet implemented. "
                "Use ccxt_spread or synthetic."
            )

        fund = None
        try:
            from data.adapters.ccxt_adapter import fetch_funding_rate_history
            fdf  = fetch_funding_rate_history(asset, since=start, until=end, exchange=venue)
            fund = fdf.get("fundingRate")
        except Exception:
            pass

        return factor, returns, fund

    raise ValueError(
        f"Unknown source '{source}' for factor. "
        "Supported: ccxt, ccxt_spread, synthetic."
    )


# ── Signal factory ────────────────────────────────────────────────────────────

def _build_make_signal(
    spec: dict,
    param_overrides: dict | None = None,
) -> Callable[[pd.Series], pd.Series]:
    """Build make_signal(normalised_factor) → signal from spec."""
    from research.signals import spike_capture, mean_drift

    model  = spec.get("signal_model", "spike_capture")
    params = dict(spec.get("signal_params", {}))
    if param_overrides:
        params.update(param_overrides)

    if model == "spike_capture":
        return lambda norm: spike_capture(norm, **params)
    if model == "mean_drift":
        return lambda norm: mean_drift(norm, **params)
    raise ValueError(
        f"Unknown signal_model '{model}'. Supported: spike_capture, mean_drift."
    )


def _signal_model_str(spec: dict) -> str:
    model  = spec.get("signal_model", "spike_capture")
    params = spec.get("signal_params", {})
    return f"{model}({', '.join(f'{k}={v}' for k, v in params.items())})"


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
    model_str   = _signal_model_str(spec)
    make_signal = _build_make_signal(spec)
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
            make_signal   = lambda norm, **p: _build_make_signal(spec, p)(norm),
            param_grid    = param_grid,
            funding_rates = funding_rates,
            bars_per_year = bars_per_year,
            wf_kwargs     = _wf_kw if _wf_kw else None,
        )
        print(opt_result.report())
        best_make_signal = _build_make_signal(spec, opt_result.best_params)
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
    )
    verdict, reasons = _verdict(report_data)
    print(f"\nVerdict: {verdict}")
    for r in reasons:
        print(f"  - {r}")

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
