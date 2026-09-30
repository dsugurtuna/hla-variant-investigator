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
            absent={"B"},
            quality_scores={"A": 0.9},
        )
        text = QualityValidator.format_report(report)
        assert "50.0%" in text
        assert "- B" in text


def test_absent_and_low_quality_are_separate(tmp_path: Path) -> None:
    r2 = tmp_path / "a.bgl.r2"
    r2.write_text("HLA_DRB1_0101 0.95\nHLA_DRB1_0701 0.30\n")
    report = QualityValidator(
        ["HLA_DRB1_0101", "HLA_DRB1_0701", "HLA_DRB1_1602"], min_r2=0.5
    ).validate([r2])
    assert report.absent == {"HLA_DRB1_1602"}
    assert report.below_threshold == {"HLA_DRB1_0701"}
    assert report.confirmed_missing == {"HLA_DRB1_0701", "HLA_DRB1_1602"}


def test_lowest_r2_across_sub_batches_counts(tmp_path: Path) -> None:
    good = tmp_path / "b1.bgl.r2"
    good.write_text("HLA_DRB1_0401 0.97\nHLA_DRB1_1501 0.99\n")
    poor = tmp_path / "b2.bgl.r2"
    poor.write_text("HLA_DRB1_0401 0.41\n")
    report = QualityValidator(["HLA_DRB1_0401", "HLA_DRB1_1501"], min_r2=0.5).validate(
        [good, poor]
    )
    assert report.quality_scores["HLA_DRB1_0401"] == 0.41
    assert report.below_threshold == {"HLA_DRB1_0401"}
    # Missing from one sub-batch counts as absent.
    assert report.absent == {"HLA_DRB1_1501"}
