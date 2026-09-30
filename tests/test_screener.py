"""Tests for hla_investigator.screener."""

from pathlib import Path

import pytest

from hla_investigator.screener import DiseaseScreener


@pytest.fixture()
def mapping(tmp_path: Path) -> Path:
    p = tmp_path / "map.csv"
    p.write_text("clinical_id,genotyping_id\nCLIN1,G1\nCLIN2,G2\nCLIN3,G3\nCLIN4,G4\n")
    return p


@pytest.fixture()
def raw(tmp_path: Path) -> Path:
    p = tmp_path / "x.raw"
    p.write_text(
        "FID IID PAT MAT SEX PHENOTYPE HLA_DRB1_0401_P\n"
        "G1 G1 0 0 1 -9 1\n"
        "G2 G2 0 0 1 -9 0\n"
        "G3 G3 0 0 1 -9 2\n"
    )
    return p


def test_screen_maps_back_to_clinical_ids(mapping: Path, raw: Path) -> None:
    result = DiseaseScreener(mapping).screen(
        ["CLIN1", "CLIN2", "CLIN3", "CLIN4", "UNKNOWN"], raw, "HLA_DRB1_0401"
    )
    assert result.carriers_found == {"CLIN1", "CLIN3"}
    assert result.unmapped_ids == ["UNKNOWN"]
    assert result.not_genotyped == ["CLIN4"]
    assert result.cohort_size == 5
    assert result.mapped_count == 4
    # 2 carriers among the 3 mapped participants that have genotypes.
    assert result.carrier_rate == pytest.approx(2 / 3)


def test_screen_threshold(mapping: Path, raw: Path) -> None:
    result = DiseaseScreener(mapping).screen(
        ["CLIN1", "CLIN3"], raw, "HLA_DRB1_0401", threshold=1.5
    )
    assert result.carriers_found == {"CLIN3"}
