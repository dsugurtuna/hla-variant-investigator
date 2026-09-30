"""CLI tests against examples/."""

from pathlib import Path

import pytest

from hla_investigator.__main__ import main

EX = Path(__file__).resolve().parent.parent / "examples"
SUB1 = str(EX / "sub_batch_001_imputed")
SUB2 = str(EX / "sub_batch_002_imputed")


def test_carriers(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        ["carriers", SUB1 + ".dosage", SUB2 + ".dosage", "--allele", "HLA_DRB1_0401",
         "--threshold", "0.5"]
    )  # fmt: skip
    out = capsys.readouterr().out
    assert code == 0
    assert "HLA_DRB1_0401: 4 unique carriers" in out


def test_audit_finds_missing_marker(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        ["audit", SUB1 + ".dosage", SUB2 + ".dosage", "--markers", "HLA_DRB1_0401",
         "HLA_DRB1_1501"]
    )  # fmt: skip
    assert code == 1
    assert "- HLA_DRB1_1501" in capsys.readouterr().out


def test_quality(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        ["quality", SUB1 + ".bgl.r2", SUB2 + ".bgl.r2", "--markers", "HLA_DRB1_0401",
         "--min-r2", "0.8"]
    )  # fmt: skip
    assert code == 1
    assert "HLA_DRB1_0401  (r2 0.41)" in capsys.readouterr().out


def test_screen(capsys: pytest.CaptureFixture[str]) -> None:
    main(
        ["screen", "--map", str(EX / "id_map.csv"), "--cohort", str(EX / "cohort.txt"),
         "--dosage", SUB1 + ".dosage", "--allele", "HLA_DRB1_0401", "--threshold",
         "0.5"]
    )  # fmt: skip
    out = capsys.readouterr().out
    assert "unmapped: CLIN99" in out
    assert "carriers: CLIN02, CLIN03" in out
