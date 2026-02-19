"""Tests for hla_investigator.carrier."""

from pathlib import Path

import pytest

from hla_investigator.carrier import CarrierIdentifier


@pytest.fixture()
def dosage_file(tmp_path: Path) -> Path:
    p = tmp_path / "dosage.raw"
    p.write_text(
        "FID\tIID\tHLA_DRB1_0101\tHLA_DRB1_0301\n"
        "S001\tS001\t1.5\t0.0\n"
        "S002\tS002\t0.0\t0.8\n"
        "S003\tS003\t0.0\t0.0\n"
    )
    return p


class TestCarrierIdentifier:
    def test_identify_from_dosage(self, dosage_file: Path) -> None:
        ci = CarrierIdentifier()
        result = ci.identify_from_dosage(dosage_file, "HLA_DRB1_0101")
        assert result.total_carriers == 1
        assert "S001" in result.carriers

    def test_threshold(self, dosage_file: Path) -> None:
        ci = CarrierIdentifier(threshold=1.0)
        result = ci.identify_from_dosage(dosage_file, "HLA_DRB1_0101")
        assert result.total_carriers == 1
        # S001 has 1.5 > 1.0
        ci_high = CarrierIdentifier(threshold=2.0)
        result2 = ci_high.identify_from_dosage(dosage_file, "HLA_DRB1_0101")
        assert result2.total_carriers == 0

    def test_across_batches(self, tmp_path: Path) -> None:
        b1 = tmp_path / "batch1.raw"
        b1.write_text("FID\tIID\tHLA_DRB1_0101\nS001\tS001\t1.0\n")
        b2 = tmp_path / "batch2.raw"
        b2.write_text("FID\tIID\tHLA_DRB1_0101\nS001\tS001\t0.5\nS002\tS002\t1.2\n")
        ci = CarrierIdentifier()
        result = ci.identify_across_batches([b1, b2], "HLA_DRB1_0101")
        assert result.total_carriers == 2  # S001 + S002, deduplicated
        assert result.per_batch_counts["batch1"] == 1
        assert result.per_batch_counts["batch2"] == 2

    def test_export_carrier_list(self, dosage_file: Path, tmp_path: Path) -> None:
        ci = CarrierIdentifier()
        result = ci.identify_from_dosage(dosage_file, "HLA_DRB1_0301")
        out = tmp_path / "carriers.txt"
        CarrierIdentifier.export_carrier_list(result, out)
        lines = out.read_text().strip().split("\n")
        assert lines == ["S002"]
