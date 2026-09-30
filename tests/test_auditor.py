"""Tests for hla_investigator.auditor."""

from pathlib import Path

import pytest

from hla_investigator.auditor import AuditReport, DosageAuditor


@pytest.fixture()
def dosage_with_all(tmp_path: Path) -> Path:
    markers = ["FID", "IID"] + [f"HLA_DRB1_{a}" for a in ["0101", "0301", "0401"]]
    p = tmp_path / "complete.raw"
    p.write_text("\t".join(markers) + "\n")
    return p


@pytest.fixture()
def dosage_missing_one(tmp_path: Path) -> Path:
    markers = ["FID", "IID", "HLA_DRB1_0101", "HLA_DRB1_0301"]
    p = tmp_path / "partial.raw"
    p.write_text("\t".join(markers) + "\n")
    return p


class TestDosageAuditor:
    def test_audit_complete(self, dosage_with_all: Path) -> None:
        auditor = DosageAuditor(
            expected_markers=["HLA_DRB1_0101", "HLA_DRB1_0301", "HLA_DRB1_0401"]
        )
        found, missing = auditor.audit_file(dosage_with_all)
        assert len(found) == 3
        assert len(missing) == 0

    def test_audit_partial(self, dosage_missing_one: Path) -> None:
        auditor = DosageAuditor(
            expected_markers=["HLA_DRB1_0101", "HLA_DRB1_0301", "HLA_DRB1_0401"]
        )
        found, missing = auditor.audit_file(dosage_missing_one)
        assert len(found) == 2
        assert "HLA_DRB1_0401" in missing

    def test_audit_batch(self, dosage_with_all: Path, dosage_missing_one: Path) -> None:
        auditor = DosageAuditor(
            expected_markers=["HLA_DRB1_0101", "HLA_DRB1_0301", "HLA_DRB1_0401"]
        )
        report = auditor.audit_batch([dosage_with_all, dosage_missing_one])
        assert not report.all_consistent

    def test_format_report(self) -> None:
        report = AuditReport(
            expected_markers=["HLA_DRB1_0101"],
            found_markers={"batch1": {"HLA_DRB1_0101"}},
            missing_markers={"batch1": set()},
        )
        text = DosageAuditor.format_report(report)
        assert "Consistent: Yes" in text
