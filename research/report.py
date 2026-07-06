"""
report.py — Charts and markdown report writer (spec §9.9).

Saves all artifacts to strategies/<factor_name>/ and optionally
appends a paragraph to notes/<factor_name>.md (the accumulating knowledge base).

Usage
-----
    from research.report import FactorReportData, save, append_note

    data = FactorReportData(
        factor_name             = "coinbase_premium_gap",
        asset                   = "BTC/USDT",
        alpha_story             = "...",
        classification          = "signed",
        transform_justification = "...",
        factor_stats            = preprocess_stats,
        signal_model            = "spike_capture(z_entry=2.0)",
        bt_result               = backtest.run(...),
        wf_result               = walkforward.run(...),
        opt_result              = optimize.run(...),   # optional
        point_in_time_clean     = True,
    )
    report_path = save(data)
    append_note("coinbase_premium_gap", "Mean-reversion signal, CV Sharpe 1.2, KEEP.")
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from datetime import timezone as _tz

if TYPE_CHECKING:
    from research.walkforward import WalkForwardResult
    from research.optimize import OptimizeResult


# ── Report data container ─────────────────────────────────────────────────────

@dataclass
class FactorReportData:
    """Collects all pipeline outputs needed to produce a full factor report."""
    factor_name:             str
    asset:                   str
    alpha_story:             str
    classification:          str
    transform_justification: str
    factor_stats:            dict
    signal_model:            str
    bt_result:               dict
    wf_result:               "WalkForwardResult"
    opt_result:              "OptimizeResult | None" = None
    point_in_time_clean:     bool = True
    bars_per_year:           int  = 8_760
    n_configs:               int  = 1
    regime_analysis_text:    str  = ""


# ── Verdict logic ─────────────────────────────────────────────────────────────

_KEEP_SHARPE          = 1.0
_KEEP_POSITIVE_PCT    = 0.60
_OVERFIT_DEGRADATION  = 0.40
_KILL_SHARPE          = 0.0


def _verdict(data: FactorReportData) -> tuple[str, list[str]]:
    """
    Returns (verdict_label, reason_strings).
    verdict_label: "KEEP" | "OVERFIT" | "KILL"
    """
    wf        = data.wf_result
    n_folds   = len(wf.folds)
    pos_pct   = wf.n_positive_folds / n_folds if n_folds > 0 else 0.0

    kill_flags   = 0
    overfit_flags = 0
    reasons: list[str] = []

    if wf.cv_sharpe <= _KILL_SHARPE:
        kill_flags += 1
        reasons.append(f"CV Sharpe = {wf.cv_sharpe:.3f} <= 0 (KILL)")

    if np.isfinite(wf.is_oos_degradation) and abs(wf.is_oos_degradation) > _OVERFIT_DEGRADATION:
        overfit_flags += 1
        reasons.append(
            f"IS->OOS degradation = {wf.is_oos_degradation:+.3f} "
            f"> {_OVERFIT_DEGRADATION} (OVERFIT)"
        )

    if pos_pct < 0.50:
        overfit_flags += 1
        reasons.append(
            f"Positive folds = {wf.n_positive_folds}/{n_folds} "
            f"= {pos_pct:.0%} < 50% (OVERFIT)"
        )

    if data.opt_result is not None and data.opt_result.plateau_size == 1:
        overfit_flags += 1
        reasons.append("Single-cell plateau (OVERFIT)")

    if kill_flags > 0:
        verdict = "KILL"
    elif overfit_flags >= 2:
        verdict = "OVERFIT"
    elif overfit_flags == 1 and wf.cv_sharpe < _KEEP_SHARPE:
        verdict = "OVERFIT"
    elif wf.cv_sharpe >= _KEEP_SHARPE and pos_pct >= _KEEP_POSITIVE_PCT and overfit_flags == 0:
        verdict = "KEEP"
    else:
        verdict = "OVERFIT"

    if not reasons:
        reasons.append(
            f"CV Sharpe = {wf.cv_sharpe:.3f}, "
            f"positive folds = {wf.n_positive_folds}/{n_folds}"
        )

    return verdict, reasons


# ── Chart helpers ─────────────────────────────────────────────────────────────

def _save_equity_chart(wf: "WalkForwardResult", save_path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        return

    eq = wf.oos_equity
    if len(eq) == 0:
        return

    fig, axes = plt.subplots(
        2, 1, figsize=(10, 6), sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )
    ax_eq, ax_dd = axes

    ax_eq.plot(eq.index, eq.values, color="#1a73e8", linewidth=1.2, label="OOS equity")
    ax_eq.axhline(1.0, color="grey", linewidth=0.7, linestyle="--")
    ax_eq.set_ylabel("Equity (start = 1)")
    ax_eq.legend(fontsize=8)
    ax_eq.set_title(f"Walk-forward OOS equity  |  CV Sharpe = {wf.cv_sharpe:.3f}")

    running_max = eq.cummax()
    dd = (eq - running_max) / running_max
    ax_dd.fill_between(dd.index, dd.values, 0, color="#e84040", alpha=0.6)
    ax_dd.set_ylabel("Drawdown")
    ax_dd.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))

    if hasattr(eq.index, "year"):
        ax_dd.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate(rotation=30)

    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches="tight")
    plt.close()


def _save_folds_chart(wf: "WalkForwardResult", save_path: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    n     = len(wf.folds)
    if n == 0:
        return
    x     = np.arange(n)
    width = 0.35
    is_s  = [s if np.isfinite(s) else 0.0 for s in wf.fold_sharpes_is]
    oos_s = [s if np.isfinite(s) else 0.0 for s in wf.fold_sharpes_oos]

    fig, ax = plt.subplots(figsize=(max(6, n * 1.2), 4))
    ax.bar(x - width / 2, is_s,  width, label="IS Sharpe",  color="#4472c4", alpha=0.85)
    ax.bar(x + width / 2, oos_s, width, label="OOS Sharpe", color="#ed7d31", alpha=0.85)
    ax.axhline(0,   color="black", linewidth=0.7)
    ax.axhline(1.0, color="green", linewidth=0.7, linestyle="--", label="Keep threshold")
    ax.set_xticks(x)
    ax.set_xticklabels([f"Fold {i}" for i in range(n)], fontsize=9)
    ax.set_ylabel("Annualised Sharpe")
    ax.set_title("Per-fold IS vs OOS Sharpe")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches="tight")
    plt.close()


def _save_distribution_chart(
    factor_stats: dict,
    classification: str,
    factor_name: str,
    save_path: Path,
) -> None:
    raw = factor_stats.get("raw_sample")
    if raw is None:
        return
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    vals = np.asarray(raw, dtype=float)
    vals = vals[np.isfinite(vals)]
    if len(vals) == 0:
        return

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(
        vals,
        bins=min(60, max(10, len(vals) // 20)),
        color="#4472c4", alpha=0.75, edgecolor="white",
    )
    ax.set_xlabel(factor_name)
    ax.set_ylabel("Count")
    ax.set_title(f"Factor distribution  |  classification: {classification}")
    plt.tight_layout()
    plt.savefig(save_path, dpi=120, bbox_inches="tight")
    plt.close()


# ── Markdown builder ──────────────────────────────────────────────────────────

def _format_stats_table(stats: dict) -> str:
    if not stats:
        return "_(no stats provided)_"
    rows = ["| Stat | Value |", "|------|-------|"]
    for k, v in stats.items():
        if k == "raw_sample":
            continue
        if isinstance(v, float):
            rows.append(f"| {k} | {v:.4f} |")
        else:
            rows.append(f"| {k} | {v} |")
    return "\n".join(rows)


def _format_metrics_table(bt: dict, n_configs: int, bars_per_year: int) -> str:
    from research.metrics import sharpe, sortino, calmar, max_drawdown as mdd
    from research.metrics import hit_rate, profit_factor

    sr  = sharpe(bt["net_ret"], bars_per_year)
    so  = sortino(bt["net_ret"], bars_per_year)
    ca  = calmar(bt["net_ret"], bt["equity"], bars_per_year)
    md  = mdd(bt["equity"])
    hr  = hit_rate(bt["net_ret"])
    pf  = profit_factor(bt["net_ret"])
    avg_to = float(bt["turnover"].mean())
    n_obs  = len(bt["net_ret"])

    rows = [
        "| Metric | Value |",
        "|--------|-------|",
        f"| Sharpe (annualised) | {sr:.3f} |",
        f"| Sortino | {so:.3f} |",
        f"| Calmar | {ca:.3f} |",
        f"| Max drawdown | {md:.1%} |",
        f"| Hit rate | {hr:.1%} |",
        f"| Profit factor | {pf:.2f} |",
        f"| Avg turnover / bar | {avg_to:.4f} |",
        f"| Observations | {n_obs:,} |",
    ]

    try:
        from research.metrics import deflated_sharpe_ratio
        import scipy  # noqa: F401
        dsr_prob, e_max_sr = deflated_sharpe_ratio(
            sr_best   = sr,
            sr_trials = [sr] * n_configs,
            n_obs     = n_obs,
            skewness          = float(bt["net_ret"].skew()),
            excess_kurtosis   = float(bt["net_ret"].kurtosis()),
        )
        rows += [
            f"| DSR probability | {dsr_prob:.4f} |",
            f"| E[max SR] ({n_configs} configs) | {e_max_sr:.3f} |",
        ]
    except (ImportError, Exception):
        rows.append("| DSR | _(scipy unavailable)_ |")

    return "\n".join(rows)


def _build_markdown(data: FactorReportData, artifacts_dir: Path) -> str:
    verdict, reasons = _verdict(data)
    ts = datetime.now(_tz.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Contamination warning — present when data is NOT point-in-time clean
    contamination_block = ""
    if not data.point_in_time_clean:
        contamination_block = (
            "> **WARNING: POINT-IN-TIME CONTAMINATION**\n"
            "> This data source does not serve immutable / point-in-time vintages.\n"
            "> Metrics may be overstated due to retroactive data revisions.\n"
            "> Do not promote to live research until validated on immutable data.\n\n"
        )

    wf       = data.wf_result
    n_folds  = len(wf.folds)
    pos_pct  = wf.n_positive_folds / n_folds if n_folds > 0 else 0.0

    dir_name = artifacts_dir.name

    opt_block = ""
    if data.opt_result is not None:
        opt_block = (
            "## Optimisation\n\n"
            "```\n"
            + data.opt_result.report()
            + "\n```\n\n"
        )

    reason_md = "\n".join(f"- {r}" for r in reasons)

    verdict_marker = {"KEEP": "KEEP", "OVERFIT": "OVERFIT (flagged)", "KILL": "KILL"}.get(
        verdict, verdict
    )

    lines = [
        f"# Factor Report: {data.factor_name}",
        "",
        f"**Asset:** {data.asset}  ",
        f"**Generated:** {ts}  ",
        f"**Verdict:** **{verdict_marker}**",
        "",
    ]

    if contamination_block:
        lines.append(contamination_block)

    lines += [
        "## Alpha Story",
        "",
        data.alpha_story,
        "",
        "## Distribution Analysis",
        "",
        f"**Classification:** `{data.classification}`",
        "",
        "**Transform justification:**",
        data.transform_justification,
        "",
        "**Summary statistics:**",
        "",
        _format_stats_table(data.factor_stats),
        "",
        f"![Factor distribution]({dir_name}/factor_distribution.png)",
        "",
        "## Signal Model",
        "",
        data.signal_model,
        "",
        "## Full-sample Backtest Metrics",
        "",
        _format_metrics_table(data.bt_result, data.n_configs, data.bars_per_year),
        "",
        "## Walk-forward Validation",
        "",
        "```",
        wf.report(),
        "```",
        "",
        f"![Walk-forward OOS equity]({dir_name}/equity_curve.png)",
        "",
        f"![Per-fold Sharpe]({dir_name}/walkforward_folds.png)",
        "",
    ]

    if data.regime_analysis_text:
        lines += [
            "## Regime Analysis — The Real Test",
            "",
            "```",
            data.regime_analysis_text,
            "```",
            "",
        ]

    if opt_block:
        lines.append(opt_block)

    lines += [
        f"## Verdict: {verdict_marker}",
        "",
        reason_md,
        "",
        "**Decision thresholds:**",
        f"- Keep: CV Sharpe >= {_KEEP_SHARPE}, positive folds >= {_KEEP_POSITIVE_PCT:.0%}, "
        "degradation <= 40%",
        "- Overfit flag: IS->OOS degradation > 40%, single-cell plateau, or < 50% positive folds",
        "- Kill: OOS Sharpe <= 0",
        "",
        "---",
        "*Generated by crypto-factor-lab research harness*",
    ]

    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

def save(
    data: FactorReportData,
    root: str | Path = "strategies",
) -> Path:
    """
    Write all charts and report.md to <root>/<factor_name>/.

    Charts saved:
      equity_curve.png       — OOS equity + drawdown panel
      walkforward_folds.png  — IS vs OOS Sharpe per fold
      factor_distribution.png — factor histogram (if raw_sample in factor_stats)
      heatmap.png            — parameter grid (if opt_result provided)

    Returns path to report.md.
    """
    root    = Path(root)
    out_dir = root / data.factor_name
    out_dir.mkdir(parents=True, exist_ok=True)

    _save_equity_chart(data.wf_result, out_dir / "equity_curve.png")
    _save_folds_chart(data.wf_result,  out_dir / "walkforward_folds.png")
    _save_distribution_chart(
        data.factor_stats,
        data.classification,
        data.factor_name,
        out_dir / "factor_distribution.png",
    )

    if data.opt_result is not None:
        try:
            from research.optimize import plot_heatmap
            plot_heatmap(data.opt_result, save_path=str(out_dir / "heatmap.png"))
        except Exception:
            pass

    md = _build_markdown(data, out_dir)
    report_path = out_dir / "report.md"
    report_path.write_text(md, encoding="utf-8")
    return report_path


def append_note(
    factor_name: str,
    note: str,
    root: str | Path = ".",
) -> Path:
    """
    Append one paragraph to notes/<factor_name>.md (creates if absent).

    This is the accumulating knowledge base described in spec §9.9 — one line
    per factor summarising what was learned, to inform future factor choices.
    """
    notes_dir = Path(root) / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    note_path = notes_dir / f"{factor_name}.md"
    ts    = datetime.now(_tz.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"\n\n---\n*{ts}*\n\n{note.strip()}\n"
    with open(note_path, "a", encoding="utf-8") as fh:
        fh.write(entry)
    return note_path
