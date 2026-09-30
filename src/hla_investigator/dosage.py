"""Readers for per-sample HLA allele dosages.

Two layouts are supported:

* PLINK ``--recode A`` (``.raw``): one row per sample, whitespace-delimited,
  header ``FID IID PAT MAT SEX PHENOTYPE <marker>_<counted allele> ...``.
  PLINK counts the A1 allele, which is not always the one you want.
* SNP2HLA ``.dosage``: one row per marker, ``marker allele1 allele2`` then one
  value per sample in ``.fam`` order, equal to ``2*P(11) + P(12)``, the
  expected count of allele1.

SNP2HLA codes HLA allele markers (``HLA_DRB1_0401`` and so on) as binary
presence (``P``) / absence (``A``). Both readers return the expected count of
the *present* allele, flipping ``x -> 2 - x`` when the counted allele is ``A``.
That orientation is only applied to ``HLA_`` markers, because ``A`` means
adenine for ordinary SNPs.
"""

from __future__ import annotations

from pathlib import Path

PRESENT = "P"
ABSENT = "A"
RAW_SAMPLE_COLS = frozenset({"FID", "IID", "PAT", "MAT", "SEX", "PHENOTYPE"})


def _orient(marker: str, counted_allele: str, value: float) -> float:
    if marker.startswith("HLA_") and counted_allele == ABSENT:
        return 2.0 - value
    return value


def find_raw_column(header: list[str], marker: str) -> tuple[int, str]:
    """Locate ``marker`` in a .raw header.

    Accepts the bare marker name or PLINK's ``<marker>_<allele>`` form and
    returns ``(column index, counted allele)``; the allele is "" for a bare
    name.
    """
    for i, col in enumerate(header):
        if col == marker:
            return i, ""
        if col.startswith(marker + "_"):
            allele = col[len(marker) + 1 :]
            if allele.isalpha():
                return i, allele
    raise KeyError(f"marker {marker!r} not found in header")


def read_plink_raw(path: str | Path, marker: str) -> dict[str, float]:
    """Return ``{IID: dosage of the present allele}`` from a PLINK .raw file.

    Samples with a missing value (``NA``) are omitted.
    """
    with open(path) as fh:
        header = fh.readline().split()
        col, allele = find_raw_column(header, marker)
        iid_col = header.index("IID") if "IID" in header else 1
        out: dict[str, float] = {}
        for line in fh:
            parts = line.split()
            if len(parts) <= col or parts[col] == "NA":
                continue
            out[parts[iid_col]] = _orient(marker, allele, float(parts[col]))
    return out


def read_fam_iids(fam_path: str | Path) -> list[str]:
    """Return the IIDs (column 2) of a PLINK .fam file, in order."""
    with open(fam_path) as fh:
        return [line.split()[1] for line in fh if line.strip()]


def read_snp2hla_dosage(
    dosage_path: str | Path, fam_path: str | Path, marker: str
) -> dict[str, float]:
    """Return ``{IID: dosage of the present allele}`` from a SNP2HLA .dosage.

    ``fam_path`` must be the .fam written by the same SNP2HLA run, because the
    dosage columns carry no sample IDs.
    """
    iids = read_fam_iids(fam_path)
    with open(dosage_path) as fh:
        for line in fh:
            parts = line.split()
            if not parts or parts[0] != marker:
                continue
            allele1 = parts[1]
            values = parts[3:]
            if len(values) != len(iids):
                raise ValueError(
                    f"{marker}: {len(values)} dosage values but {len(iids)} "
                    "samples in the .fam file"
                )
            return {
                iid: _orient(marker, allele1, float(v))
                for iid, v in zip(iids, values, strict=True)
            }
    raise KeyError(f"marker {marker!r} not found in {dosage_path}")


def read_r2(path: str | Path) -> dict[str, float]:
    """Parse a Beagle ``.bgl.r2`` file into ``{marker: r2}``.

    Non-numeric values (for example ``NaN`` for monomorphic markers in older
    Beagle versions) are skipped.
    """
    scores: dict[str, float] = {}
    with open(path) as fh:
        for line in fh:
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                value = float(parts[1])
            except ValueError:
                continue
            if value == value:  # drop NaN
                scores[parts[0]] = value
    return scores


def _strip_counted_allele(column: str) -> str:
    """``HLA_DRB1_0401_P`` -> ``HLA_DRB1_0401``; other names unchanged."""
    head, _, tail = column.rpartition("_")
    if head.startswith("HLA_") and tail in (PRESENT, ABSENT) and head.count("_") >= 2:
        return head
    return column


def read_markers(path: str | Path) -> list[str]:
    """List the markers in a file, whatever its layout.

    * PLINK ``.raw``: header columns after the six sample columns, with the
      counted-allele suffix removed.
    * ``.bim``: the variant ID column.
    * SNP2HLA ``.dosage`` and Beagle ``.bgl.r2``: the first column of each row.
    """
    path = Path(path)
    with open(path) as fh:
        first = fh.readline().split()
        if first[:2] == ["FID", "IID"]:
            return [_strip_counted_allele(c) for c in first if c not in RAW_SAMPLE_COLS]
        rows = [first, *(line.split() for line in fh)]
    column = 1 if path.suffix == ".bim" else 0
    return [r[column] for r in rows if len(r) > column]


def read_dosages(
    path: str | Path, marker: str, fam_path: str | Path | None = None
) -> dict[str, float]:
    """Present-allele dosages from a .raw file, or a .dosage file plus .fam."""
    if fam_path is not None:
        return read_snp2hla_dosage(path, fam_path, marker)
    return read_plink_raw(path, marker)
