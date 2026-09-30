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


def test_audit_real_raw_header_with_counted_alleles(tmp_path: Path) -> None:
    p = tmp_path / "sub1.raw"
    p.write_text(
        "FID IID PAT MAT SEX PHENOTYPE HLA_DRB1_0101_P HLA_DRB1_0301_A rs1_G\n"
    )
    auditor = DosageAuditor(expected_markers=["HLA_DRB1_0101", "HLA_DRB1_0301"])
    found, missing = auditor.audit_file(p)
    assert found == {"HLA_DRB1_0101", "HLA_DRB1_0301"}
    assert missing == set()


def test_audit_bim_file(tmp_path: Path) -> None:
    p = tmp_path / "sub1_imputed.bim"
    p.write_text("6\tHLA_DRB1_0101\t0\t32660000\tP\tA\n")
    auditor = DosageAuditor(expected_markers=["HLA_DRB1_0101", "HLA_DRB1_0401"])
    assert auditor.audit_file(p) == ({"HLA_DRB1_0101"}, {"HLA_DRB1_0401"})
