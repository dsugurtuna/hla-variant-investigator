"""Carrier identification module.

Identifies participants carrying specific HLA alleles from imputed dosage
data across multiple sub-batches.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CarrierResult:
    """Result of carrier identification for one allele across all batches."""

    allele: str
    carriers: set[str] = field(default_factory=set)
    per_batch_counts: dict[str, int] = field(default_factory=dict)

    @property
    def total_carriers(self) -> int:
        return len(self.carriers)


class CarrierIdentifier:
    """Identify HLA allele carriers from dosage files.

    Reads PLINK recoded dosage files (``--recode A`` output) and extracts
    participants whose dosage for the target allele exceeds a threshold.

    Parameters
    ----------
    threshold : float
        Minimum dosage value to classify a participant as a carrier.
        Default is 0.0 (any non-zero dosage).
    """

    def __init__(self, threshold: float = 0.0) -> None:
        self.threshold = threshold

    def identify_from_dosage(
        self,
        dosage_path: str | Path,
        allele_column: str,
        sample_col: str = "IID",
    ) -> CarrierResult:
        """Identify carriers from a single dosage file.

        Parameters
        ----------
        dosage_path : path
            Path to a tab-separated dosage file with a header row.
        allele_column : str
            Name of the column containing dosage values for the target allele.
        sample_col : str
            Name of the column containing participant IDs.
        """
        result = CarrierResult(allele=allele_column)
        with open(dosage_path, newline="") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            for row in reader:
                try:
                    dosage = float(row.get(allele_column, "0"))
                except (ValueError, TypeError):
                    continue
                if dosage > self.threshold:
                    pid = row.get(sample_col, "").strip()
                    if pid:
                        result.carriers.add(pid)
        return result

    def identify_across_batches(
        self,
        dosage_paths: list[str | Path],
        allele_column: str,
        sample_col: str = "IID",
    ) -> CarrierResult:
        """Identify carriers across multiple sub-batch dosage files.

        Deduplicates participants appearing in multiple batches.
        """
        combined = CarrierResult(allele=allele_column)
        for path in dosage_paths:
            batch_name = Path(path).stem
            batch_result = self.identify_from_dosage(path, allele_column, sample_col)
            combined.carriers.update(batch_result.carriers)
            combined.per_batch_counts[batch_name] = batch_result.total_carriers
        return combined

    @staticmethod
    def export_carrier_list(
        result: CarrierResult,
        output_path: str | Path,
    ) -> None:
        """Write carrier IDs to a plain-text file (one per line)."""
        with open(output_path, "w") as fh:
            for pid in sorted(result.carriers):
                fh.write(f"{pid}\n")
