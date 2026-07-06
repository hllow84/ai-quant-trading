"""
test_cli.py — Acceptance tests for run.py (Step 6 CLI).

Tests:
  §CLI1  Alpha story gate: unknown/empty factor halts cleanly.
  §CLI2  Synthetic smoke: full pipeline runs end-to-end on synthetic data
         and produces all expected output files.
  §CLI3  main() return codes: 0 on success, 1 on gate failure.
  §CLI4  Demo: full stdout output visible when run with -s.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from run import (
    NoAlphaStoryError,
    PipelineResult,
    _check_alpha_story,
    _load_factor_spec,
    _load_factor_data,
    _build_make_signal,
    run_pipeline,
    main,
)


# ── §CLI1  Alpha story gate ───────────────────────────────────────────────────

class TestAlphaStoryGate:
    def test_unknown_factor_raises(self):
        """Factor not in factors.yaml must raise NoAlphaStoryError."""
        spec = _load_factor_spec("no_such_factor_xyz_99")
        with pytest.raises(NoAlphaStoryError):
            _check_alpha_story("no_such_factor_xyz_99", spec)

    def test_missing_alpha_story_field_raises(self):
        """Spec without alpha_story key must raise NoAlphaStoryError."""
        spec = {"source": "synthetic", "signal_model": "spike_capture"}
        with pytest.raises(NoAlphaStoryError):
            _check_alpha_story("some_factor", spec)

    def test_empty_alpha_story_raises(self):
        """Spec with blank alpha_story must raise NoAlphaStoryError."""
        spec = {"alpha_story": "   ", "source": "synthetic"}
        with pytest.raises(NoAlphaStoryError):
            _check_alpha_story("some_factor", spec)

    def test_valid_alpha_story_passes(self):
        """Spec with a non-empty alpha story must not raise."""
        spec = {"alpha_story": "Funding rate spikes predict reversal."}
        _check_alpha_story("some_factor", spec)  # should not raise

    def test_known_spec_loads(self):
        """synthetic_test must be present in config/factors.yaml with an alpha story."""
        spec = _load_factor_spec("synthetic_test")
        assert spec, "synthetic_test spec not found in factors.yaml"
        assert spec.get("alpha_story", "").strip(), "synthetic_test has no alpha_story"


# ── §CLI2  Full pipeline smoke test on synthetic data ─────────────────────────

class TestSyntheticPipeline:
    """
    Runs the full §9 pipeline with a small synthetic dataset.
    Uses very small WF windows so the test completes in a few seconds.
    """

    TRAIN  = 500
    TEST   = 200
    EMBARGO = 50
    N      = 3_000   # ~3.75 folds with these window sizes

    def _run(self, tmp_path: Path) -> PipelineResult:
        factor_name = "synthetic_test"
        spec        = _load_factor_spec(factor_name)
        _check_alpha_story(factor_name, spec)

        factor, returns, funding = _load_factor_data(
            spec, "BTC/USDT", "binance",
            "2020-01-01", "2021-01-01",
            synthetic_n=self.N,
        )
        return run_pipeline(
            factor_name   = factor_name,
            factor        = factor,
            asset_returns = returns,
            spec          = spec,
            train_bars    = self.TRAIN,
            test_bars     = self.TEST,
            embargo_bars  = self.EMBARGO,
            out_dir       = tmp_path,
            notes_root    = tmp_path,
        )

    def test_returns_pipeline_result(self, tmp_path):
        """run_pipeline returns a PipelineResult with all fields populated."""
        result = self._run(tmp_path)
        assert isinstance(result, PipelineResult)

    def test_verdict_is_valid(self, tmp_path):
        """Verdict must be one of KEEP / OVERFIT / KILL."""
        result = self._run(tmp_path)
        assert result.verdict in ("KEEP", "OVERFIT", "KILL"), (
            f"Unexpected verdict: {result.verdict!r}"
        )

    def test_report_md_created(self, tmp_path):
        """Pipeline must write report.md under <out_dir>/synthetic_test/."""
        result = self._run(tmp_path)
        assert result.report_path.exists(), f"report.md not found at {result.report_path}"

    def test_report_md_has_verdict(self, tmp_path):
        """report.md must contain the verdict label."""
        result = self._run(tmp_path)
        content = result.report_path.read_text(encoding="utf-8")
        assert result.verdict in content, "Verdict label missing from report.md"

    def test_report_md_has_walkforward_table(self, tmp_path):
        """report.md must include the walk-forward summary table."""
        result = self._run(tmp_path)
        content = result.report_path.read_text(encoding="utf-8")
        assert "CV Sharpe" in content
        assert "Walk-forward" in content

    def test_note_file_created(self, tmp_path):
        """append_note must write notes/synthetic_test.md."""
        result = self._run(tmp_path)
        assert result.note_path.exists(), f"note not found at {result.note_path}"

    def test_note_contains_verdict(self, tmp_path):
        """Note must mention the verdict."""
        result = self._run(tmp_path)
        content = result.note_path.read_text(encoding="utf-8")
        assert result.verdict in content

    def test_equity_chart_saved(self, tmp_path):
        """equity_curve.png must be written (matplotlib is installed)."""
        result = self._run(tmp_path)
        chart  = result.report_path.parent / "equity_curve.png"
        assert chart.exists(), f"equity_curve.png not found at {chart}"

    def test_optimize_result_present(self, tmp_path):
        """With a 2-key optimize grid in the spec, opt_result must be populated."""
        result = self._run(tmp_path)
        assert result.opt_result is not None, (
            "opt_result is None — optimization step was skipped but spec has a 2-key grid"
        )
        assert result.opt_result.n_configs == 9   # 3×3 grid

    def test_wf_has_at_least_one_fold(self, tmp_path):
        """Walk-forward must produce at least 1 fold with the synthetic data size."""
        result = self._run(tmp_path)
        assert len(result.wf_result.folds) >= 1


# ── §CLI3  main() return codes ────────────────────────────────────────────────

class TestMainReturnCodes:
    def test_main_returns_1_for_unknown_factor(self, capsys):
        """main() must return 1 when the factor has no alpha story."""
        rc = main(["--factor", "no_such_factor_xyz_99"])
        assert rc == 1

    def test_main_returns_0_on_synthetic(self, tmp_path, capsys):
        """main() must return 0 on a successful synthetic pipeline run."""
        rc = main([
            "--factor",       "synthetic_test",
            "--synthetic",    "3000",
            "--train-bars",   "500",
            "--test-bars",    "200",
            "--embargo-bars", "50",
            "--out",          str(tmp_path),
        ])
        assert rc == 0

    def test_main_creates_report_on_success(self, tmp_path, capsys):
        """A zero-return main() run must produce report.md."""
        main([
            "--factor",       "synthetic_test",
            "--synthetic",    "3000",
            "--train-bars",   "500",
            "--test-bars",    "200",
            "--embargo-bars", "50",
            "--out",          str(tmp_path),
        ])
        assert (tmp_path / "synthetic_test" / "report.md").exists()


# ── §CLI4  Demo (stdout visible with -s) ─────────────────────────────────────

class TestDemo:
    """
    Full end-to-end output on synthetic data.
    Run with:  pytest tests/test_cli.py::TestDemo -v -s
    """

    def test_full_pipeline_demo(self, tmp_path, capsys):
        """Prints the complete pipeline output so you can inspect it."""
        factor_name = "synthetic_test"
        spec        = _load_factor_spec(factor_name)
        factor, returns, _ = _load_factor_data(
            spec, "BTC/USDT", "binance",
            "2020-01-01", "2021-01-01",
            synthetic_n=3_000,
        )
        with capsys.disabled():
            result = run_pipeline(
                factor_name   = factor_name,
                factor        = factor,
                asset_returns = returns,
                spec          = spec,
                train_bars    = 500,
                test_bars     = 200,
                embargo_bars  = 50,
                out_dir       = tmp_path,
                notes_root    = tmp_path,
            )
            print(f"\n{'='*52}")
            print(f"  DEMO COMPLETE")
            print(f"  Verdict     : {result.verdict}")
            print(f"  CV Sharpe   : {result.wf_result.cv_sharpe:.3f}")
            print(f"  Report path : {result.report_path}")
            print(f"{'='*52}")

        assert result.verdict in ("KEEP", "OVERFIT", "KILL")
