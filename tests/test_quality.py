"""Tests for hla_investigator.quality."""

from pathlib import Path

import pytest

from hla_investigator.quality import QualityReport, QualityValidator


@pytest.fixture()
def r2_file(tmp_path: Path) -> Path:
    p = tmp_path / "imputed.bgl.r2"
    p.write_text("HLA_DRB1_0101 0.95\nHLA_DRB1_0301 0.82\nHLA_DRB1_0701 0.30\n")
    return p


class TestQualityValidator:
    def test_all_present(self, r2_file: Path) -> None:
        qv = QualityValidator(expected_markers=["HLA_DRB1_0101", "HLA_DRB1_0301"])
        report = qv.validate([r2_file])
        assert report.completeness_rate == 1.0
        assert len(report.confirmed_missing) == 0

    def test_some_missing(self, r2_file: Path) -> None:
        qv = QualityValidator(expected_markers=["HLA_DRB1_0101", "HLA_DRB1_9999"])
        report = qv.validate([r2_file])
        assert "HLA_DRB1_9999" in report.confirmed_missing
        assert report.completeness_rate == pytest.approx(0.5)

    def test_min_r2_threshold(self, r2_file: Path) -> None:
        qv = QualityValidator(
            expected_markers=["HLA_DRB1_0101", "HLA_DRB1_0701"],
            min_r2=0.5,
        )
        report = qv.validate([r2_file])
        # 0101 (0.95) passes, 0701 (0.30) fails threshold
        assert "HLA_DRB1_0101" in report.confirmed_present
        assert "HLA_DRB1_0701" in report.confirmed_missing

    def test_format_report(self) -> None:
        report = QualityReport(
            expected_markers=["A", "B"],
            confirmed_present={"A"},
            confirmed_missing={"B"},
            quality_scores={"A": 0.9},
        )
        text = QualityValidator.format_report(report)
        assert "50.0%" in text
        assert "- B" in text
