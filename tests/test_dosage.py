"""Tests for hla_investigator.dosage."""

from pathlib import Path

from hla_investigator.dosage import read_dosages, read_markers


def test_raw_counted_allele_orientation(tmp_path: Path) -> None:
    raw = tmp_path / "x.raw"
    raw.write_text(
        "FID IID PAT MAT SEX PHENOTYPE HLA_DRB1_0401_P HLA_DRB1_1501_A\n"
        "F1 S1 0 0 1 -9 1 2\n"
        "F2 S2 0 0 2 -9 0 NA\n"
    )
    assert read_dosages(raw, "HLA_DRB1_0401") == {"S1": 1.0, "S2": 0.0}
    assert read_dosages(raw, "HLA_DRB1_1501") == {"S1": 0.0}
    assert read_markers(raw) == ["HLA_DRB1_0401", "HLA_DRB1_1501"]


def test_markers_from_each_layout(tmp_path: Path) -> None:
    bim = tmp_path / "x.bim"
    bim.write_text("6\tHLA_DRB1_0401\t0\t32660000\tP\tA\n6\trs1\t0\t1\tA\tG\n")
    dosage = tmp_path / "x.dosage"
    dosage.write_text("HLA_DRB1_0401\tP\tA\t1.0\n")
    r2 = tmp_path / "x.bgl.r2"
    r2.write_text("HLA_DRB1_0401 0.9\n")
    assert read_markers(bim) == ["HLA_DRB1_0401", "rs1"]
    assert read_markers(dosage) == ["HLA_DRB1_0401"]
    assert read_markers(r2) == ["HLA_DRB1_0401"]


def test_snp2hla_dosage_with_fam(tmp_path: Path) -> None:
    dosage = tmp_path / "x.dosage"
    dosage.write_text("HLA_DRB1_0401\tA\tP\t2.0\t0.5\n")
    fam = tmp_path / "x.fam"
    fam.write_text("F1 S1 0 0 1 -9\nF2 S2 0 0 1 -9\n")
    # allele1 is A (absent), so present-allele dosage is 2 - value.
    assert read_dosages(dosage, "HLA_DRB1_0401", fam) == {"S1": 0.0, "S2": 1.5}
