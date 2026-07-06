"""
test_report.py — Acceptance tests for research/report.py.

Covers:
  §10.6 — Point-in-time flag emits contamination warning in the report.
  Verdict logic: KEEP / OVERFIT / KILL paths.
  File creation: report.md, charts.
  append_note: creates and appends to notes file.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.report import (
    FactorReportData,
    _verdict,
    save,
    append_note,
)
from research.walkforward import WalkForwardResult, FoldSpec


# ── Minimal fixture factories ─────────────────────────────────────────────────

def _make_oos_returns(n: int = 200, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(0.001, 0.01, n))


def _make_wf_result(
    cv_sharpe: float = 1.5,
    n_folds: int = 3,
    n_positive: int = 3,
    is_oos_degradation: float = 0.1,
) -> WalkForwardResult:
    folds = [
        FoldSpec(fold_idx=i, train_start=0, train_fit_end=100,
                 test_start=200, test_end=300)
        for i in range(n_folds)
    ]
    oos_ret = _make_oos_returns(n_folds * 100)
    oos_eq  = (1 + oos_ret).cumprod()
    return WalkForwardResult(
        folds              = folds,
        fold_sharpes_is    = [0.5] * n_folds,
        fold_sharpes_oos   = [0.4] * n_folds,
        oos_returns        = oos_ret,
        oos_equity         = oos_eq,
        cv_sharpe          = cv_sharpe,
        cv_max_drawdown    = 0.15,
        n_positive_folds   = n_positive,
        is_oos_degradation = is_oos_degradation,
        classification     = "signed",
        bars_per_year      = 8_760,
    )


def _make_bt_result(n: int = 500, seed: int = 1) -> dict:
    rng = np.random.default_rng(seed)
    net_ret  = pd.Series(rng.normal(0.001, 0.01, n))
    equity   = (1 + net_ret).cumprod()
    turnover = pd.Series(rng.uniform(0, 0.5, n))
    return {
        "net_ret":  net_ret,
        "equity":   equity,
        "turnover": turnover,
        "position": pd.Series(np.zeros(n)),
        "gross_ret": net_ret + 0.001,
        "fee_cost":  pd.Series(np.zeros(n)),
        "slip_cost": pd.Series(np.zeros(n)),
        "fund_cost": pd.Series(np.zeros(n)),
    }


def _make_data(
    cv_sharpe: float = 1.5,
    n_folds: int = 3,
    n_positive: int = 3,
    is_oos_degradation: float = 0.1,
    point_in_time_clean: bool = True,
    with_raw_sample: bool = False,
) -> FactorReportData:
    stats = {"mean": 0.0, "std": 1.0, "skewness": 0.1, "pct_neg": 0.48}
    if with_raw_sample:
        rng = np.random.default_rng(7)
        stats["raw_sample"] = rng.normal(0, 1, 500).tolist()

    return FactorReportData(
        factor_name             = "test_factor",
        asset                   = "BTC/USDT",
        alpha_story             = "Funding rate spikes predict short-term reversal.",
        classification          = "signed",
        transform_justification = "Centred at zero; robust-z scaling.",
        factor_stats            = stats,
        signal_model            = "spike_capture(z_entry=2.0, window=168)",
        bt_result               = _make_bt_result(),
        wf_result               = _make_wf_result(
            cv_sharpe          = cv_sharpe,
            n_folds            = n_folds,
            n_positive         = n_positive,
            is_oos_degradation = is_oos_degradation,
        ),
        point_in_time_clean     = point_in_time_clean,
        n_configs               = 9,
    )


# ── §10.6 Point-in-time contamination flag ────────────────────────────────────

class TestPointInTimeFlag:
    def test_warning_present_when_not_clean(self):
        """§10.6 — non-immutable data must emit contamination warning."""
        data = _make_data(point_in_time_clean=False)
        from research.report import _build_markdown
        md = _build_markdown(data, Path("strategies/test_factor"))
        assert "POINT-IN-TIME CONTAMINATION" in md, (
            "Contamination warning not found in report for non-clean data"
        )

    def test_no_warning_when_clean(self):
        """Clean data must NOT emit the contamination warning."""
        data = _make_data(point_in_time_clean=True)
        from research.report import _build_markdown
        md = _build_markdown(data, Path("strategies/test_factor"))
        assert "POINT-IN-TIME CONTAMINATION" not in md


# ── Verdict logic ─────────────────────────────────────────────────────────────

class TestVerdictLogic:
    def test_keep_when_all_criteria_met(self):
        """CV Sharpe >= 1, positive folds >= 60%, low degradation -> KEEP."""
        data    = _make_data(cv_sharpe=1.5, n_folds=5, n_positive=4, is_oos_degradation=0.10)
        verdict, _ = _verdict(data)
        assert verdict == "KEEP", f"Expected KEEP, got {verdict}"

    def test_kill_when_cv_sharpe_zero(self):
        """CV Sharpe <= 0 must produce KILL regardless of other metrics."""
        data    = _make_data(cv_sharpe=-0.5, n_folds=4, n_positive=3, is_oos_degradation=0.05)
        verdict, _ = _verdict(data)
        assert verdict == "KILL"

    def test_overfit_when_high_degradation(self):
        """IS->OOS degradation > 0.40 and Sharpe < keep threshold -> OVERFIT."""
        data    = _make_data(cv_sharpe=0.8, n_folds=4, n_positive=3, is_oos_degradation=0.50)
        verdict, _ = _verdict(data)
        assert verdict == "OVERFIT"

    def test_overfit_when_few_positive_folds(self):
        """< 50% positive folds plus sub-threshold Sharpe -> OVERFIT."""
        data    = _make_data(cv_sharpe=0.7, n_folds=6, n_positive=2, is_oos_degradation=0.15)
        verdict, _ = _verdict(data)
        assert verdict == "OVERFIT"

    def test_reasons_not_empty(self):
        """_verdict always returns at least one reason string."""
        for cv_sharpe, n_pos, deg in [
            (1.5, 4, 0.1), (-0.2, 2, 0.5), (0.5, 1, 0.6),
        ]:
            _, reasons = _verdict(
                _make_data(cv_sharpe=cv_sharpe, n_folds=4,
                           n_positive=n_pos, is_oos_degradation=deg)
            )
            assert len(reasons) >= 1

    def test_kill_reason_mentions_sharpe(self):
        """KILL reason should mention the CV Sharpe value."""
        data = _make_data(cv_sharpe=-0.3)
        _, reasons = _verdict(data)
        assert any("CV Sharpe" in r for r in reasons)


# ── File creation ─────────────────────────────────────────────────────────────

class TestSaveArtifacts:
    def test_report_md_created(self, tmp_path):
        """save() must write report.md under <root>/<factor_name>/."""
        data = _make_data()
        path = save(data, root=tmp_path)
        assert path.exists(), "report.md not created"
        assert path.name == "report.md"
        assert path.parent.name == "test_factor"

    def test_report_md_contains_factor_name(self, tmp_path):
        """report.md must mention the factor name."""
        data = _make_data()
        path = save(data, root=tmp_path)
        content = path.read_text(encoding="utf-8")
        assert "test_factor" in content

    def test_report_md_contains_verdict(self, tmp_path):
        """report.md must include the verdict label."""
        data    = _make_data(cv_sharpe=1.5, n_folds=4, n_positive=4)
        path    = save(data, root=tmp_path)
        content = path.read_text(encoding="utf-8")
        assert "KEEP" in content

    def test_equity_chart_created(self, tmp_path):
        """save() must write equity_curve.png when matplotlib is available."""
        data = _make_data()
        save(data, root=tmp_path)
        chart = tmp_path / "test_factor" / "equity_curve.png"
        try:
            import matplotlib  # noqa: F401
            assert chart.exists(), "equity_curve.png not created"
        except ImportError:
            pytest.skip("matplotlib not installed")

    def test_folds_chart_created(self, tmp_path):
        """save() must write walkforward_folds.png."""
        data = _make_data()
        save(data, root=tmp_path)
        chart = tmp_path / "test_factor" / "walkforward_folds.png"
        try:
            import matplotlib  # noqa: F401
            assert chart.exists(), "walkforward_folds.png not created"
        except ImportError:
            pytest.skip("matplotlib not installed")

    def test_distribution_chart_created_when_raw_sample_given(self, tmp_path):
        """Distribution chart saved only when raw_sample is in factor_stats."""
        data = _make_data(with_raw_sample=True)
        save(data, root=tmp_path)
        chart = tmp_path / "test_factor" / "factor_distribution.png"
        try:
            import matplotlib  # noqa: F401
            assert chart.exists(), "factor_distribution.png not created"
        except ImportError:
            pytest.skip("matplotlib not installed")

    def test_distribution_chart_absent_without_raw_sample(self, tmp_path):
        """No distribution chart if raw_sample not provided."""
        data = _make_data(with_raw_sample=False)
        save(data, root=tmp_path)
        chart = tmp_path / "test_factor" / "factor_distribution.png"
        assert not chart.exists()

    def test_contamination_warning_in_saved_file(self, tmp_path):
        """§10.6 — saved report.md must include contamination warning when not clean."""
        data    = _make_data(point_in_time_clean=False)
        path    = save(data, root=tmp_path)
        content = path.read_text(encoding="utf-8")
        assert "POINT-IN-TIME CONTAMINATION" in content

    def test_walkforward_table_in_report(self, tmp_path):
        """report.md must include the walk-forward summary table."""
        data    = _make_data()
        path    = save(data, root=tmp_path)
        content = path.read_text(encoding="utf-8")
        assert "CV Sharpe" in content
        assert "Walk-forward" in content


# ── append_note ───────────────────────────────────────────────────────────────

class TestAppendNote:
    def test_creates_notes_file(self, tmp_path):
        """append_note creates the notes directory and file on first call."""
        path = append_note("my_factor", "First observation.", root=tmp_path)
        assert path.exists()
        assert path.name == "my_factor.md"
        assert path.parent.name == "notes"

    def test_note_text_present(self, tmp_path):
        """The note text appears in the file."""
        append_note("my_factor", "Signal decayed after halving.", root=tmp_path)
        content = (tmp_path / "notes" / "my_factor.md").read_text(encoding="utf-8")
        assert "Signal decayed after halving." in content

    def test_appends_multiple_notes(self, tmp_path):
        """Calling append_note twice keeps both entries."""
        append_note("my_factor", "First note.",  root=tmp_path)
        append_note("my_factor", "Second note.", root=tmp_path)
        content = (tmp_path / "notes" / "my_factor.md").read_text(encoding="utf-8")
        assert "First note." in content
        assert "Second note." in content

    def test_timestamp_in_note(self, tmp_path):
        """Each note entry includes a UTC timestamp."""
        append_note("my_factor", "Timestamped note.", root=tmp_path)
        content = (tmp_path / "notes" / "my_factor.md").read_text(encoding="utf-8")
        assert "UTC" in content

    def test_different_factors_separate_files(self, tmp_path):
        """Different factor names produce separate note files."""
        append_note("factor_a", "Note A.", root=tmp_path)
        append_note("factor_b", "Note B.", root=tmp_path)
        assert (tmp_path / "notes" / "factor_a.md").exists()
        assert (tmp_path / "notes" / "factor_b.md").exists()
