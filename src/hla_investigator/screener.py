"""Disease cohort screening module.

Maps clinical IDs to genotyping IDs via an alias mapping, then screens
transposed dosage files for allele carriers within a specified disease cohort.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class ScreeningResult:
    """Result of screening a disease cohort for HLA carriers."""

    cohort_size: int
    mapped_count: int
    carriers_found: Set[str] = field(default_factory=set)
    unmapped_ids: List[str] = field(default_factory=list)

    @property
    def carrier_rate(self) -> float:
        if self.mapped_count == 0:
            return 0.0
        return len(self.carriers_found) / self.mapped_count


class DiseaseScreener:
    """Screen a clinical cohort for HLA allele carriers.

    Parameters
    ----------
    mapping_csv : str or Path
        CSV mapping clinical IDs to genotyping IDs. Must have columns
        ``clinical_id`` and ``genotyping_id``.
    """

    def __init__(self, mapping_csv: str | Path) -> None:
        self._clinical_to_geno: Dict[str, str] = {}
        self._geno_to_clinical: Dict[str, str] = {}
        self._load_mapping(mapping_csv)

    def _load_mapping(self, csv_path: str | Path) -> None:
        with open(csv_path, newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                cid = row.get("clinical_id", "").strip()
                gid = row.get("genotyping_id", "").strip()
                if cid and gid:
                    self._clinical_to_geno[cid] = gid
                    self._geno_to_clinical[gid] = cid

    def screen(
        self,
        cohort_ids: List[str],
        dosage_path: str | Path,
        allele_column: str,
        sample_col: str = "IID",
        threshold: float = 0.0,
    ) -> ScreeningResult:
        """Screen a cohort of clinical IDs for carriers in dosage data.

        Parameters
        ----------
        cohort_ids : list of str
            Clinical IDs to screen.
        dosage_path : path
            Tab-separated dosage file.
        allele_column : str
            Column name of the target HLA allele.
        sample_col : str
            Column containing genotyping IDs.
        threshold : float
            Minimum dosage to classify as carrier.
        """
        # Map clinical → genotyping
        geno_to_clinical: Dict[str, str] = {}
        unmapped: List[str] = []
        for cid in cohort_ids:
            gid = self._clinical_to_geno.get(cid)
            if gid:
                geno_to_clinical[gid] = cid
            else:
                unmapped.append(cid)

        # Scan dosage file
        carriers: Set[str] = set()
        with open(dosage_path, newline="") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                gid = row.get(sample_col, "").strip()
                if gid in geno_to_clinical:
                    try:
                        dosage = float(row.get(allele_column, "0"))
                    except (ValueError, TypeError):
                        continue
                    if dosage > threshold:
                        carriers.add(geno_to_clinical[gid])

        return ScreeningResult(
            cohort_size=len(cohort_ids),
            mapped_count=len(geno_to_clinical),
            carriers_found=carriers,
            unmapped_ids=unmapped,
        )
