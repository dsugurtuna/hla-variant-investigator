"""Screen a clinical cohort for carriers of an HLA allele.

Clinical IDs are mapped to genotyping IDs, carriers are found in the
dosage data, and results are mapped back to clinical IDs, so genotyping IDs
never leave the tool.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .dosage import read_dosages


@dataclass
class ScreeningResult:
    """Outcome of screening one cohort."""

    cohort_size: int
    mapped_count: int
    carriers_found: set[str] = field(default_factory=set)
    unmapped_ids: list[str] = field(default_factory=list)
    not_genotyped: list[str] = field(default_factory=list)

    @property
    def carrier_rate(self) -> float:
        """Carriers among mapped participants with genotype data."""
        screened = self.mapped_count - len(self.not_genotyped)
        return len(self.carriers_found) / screened if screened else 0.0


class DiseaseScreener:
    """Screen clinical IDs for allele carriers.

    Parameters
    ----------
    mapping_csv : path
        CSV with ``clinical_id`` and ``genotyping_id`` columns.
    """

    def __init__(self, mapping_csv: str | Path) -> None:
        self._clinical_to_geno: dict[str, str] = {}
        with open(mapping_csv, newline="") as fh:
            for row in csv.DictReader(fh):
                cid = (row.get("clinical_id") or "").strip()
                gid = (row.get("genotyping_id") or "").strip()
                if cid and gid:
                    self._clinical_to_geno[cid] = gid

    def screen(
        self,
        cohort_ids: Sequence[str],
        dosage_path: str | Path,
        allele_column: str,
        threshold: float = 0.0,
        fam_path: str | Path | None = None,
    ) -> ScreeningResult:
        """Return carriers (as clinical IDs) among ``cohort_ids``.

        ``dosage_path`` is a PLINK .raw file, or a SNP2HLA .dosage file when
        ``fam_path`` is given.
        """
        geno_to_clinical: dict[str, str] = {}
        unmapped: list[str] = []
        for cid in cohort_ids:
            gid = self._clinical_to_geno.get(cid)
            if gid:
                geno_to_clinical[gid] = cid
            else:
                unmapped.append(cid)

        dosages = read_dosages(dosage_path, allele_column, fam_path)
        carriers = {
            cid
            for gid, cid in geno_to_clinical.items()
            if dosages.get(gid, 0) > threshold
        }
        not_genotyped = sorted(
            cid for gid, cid in geno_to_clinical.items() if gid not in dosages
        )
        return ScreeningResult(
            cohort_size=len(cohort_ids),
            mapped_count=len(geno_to_clinical),
            carriers_found=carriers,
            unmapped_ids=unmapped,
            not_genotyped=not_genotyped,
        )
