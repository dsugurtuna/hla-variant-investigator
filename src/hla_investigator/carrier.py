"""Find carriers of one HLA allele across sub-batches."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .dosage import read_dosages


@dataclass
class CarrierResult:
    """Carriers of one allele across all files read."""

    allele: str
    carriers: set[str] = field(default_factory=set)
    per_batch_counts: dict[str, int] = field(default_factory=dict)

    @property
    def total_carriers(self) -> int:
        return len(self.carriers)


class CarrierIdentifier:
    """Identify carriers from imputed dosages.

    Reads PLINK ``--recode A`` (.raw) files, or SNP2HLA ``.dosage`` files
    when a matching ``.fam`` is given, and keeps samples whose dosage of the
    present allele is above ``threshold``.

    Parameters
    ----------
    threshold : float
        Dosage above which a sample counts as a carrier. The default 0.0
        (any non-zero dosage) matches the original scripts; 0.5 is a common
        choice for imputed dosages.
    """

    def __init__(self, threshold: float = 0.0) -> None:
        self.threshold = threshold

    def identify_from_dosage(
        self,
        dosage_path: str | Path,
        allele_column: str,
        fam_path: str | Path | None = None,
    ) -> CarrierResult:
        """Carriers in one file."""
        dosages = read_dosages(dosage_path, allele_column, fam_path)
        return CarrierResult(
            allele=allele_column,
            carriers={iid for iid, d in dosages.items() if d > self.threshold},
        )

    def identify_across_batches(
        self,
        dosage_paths: Sequence[str | Path],
        allele_column: str,
        fam_paths: Sequence[str | Path] | None = None,
    ) -> CarrierResult:
        """Carriers across sub-batch files, each sample counted once."""
        if fam_paths is not None and len(fam_paths) != len(dosage_paths):
            raise ValueError("fam_paths must match dosage_paths one to one")
        combined = CarrierResult(allele=allele_column)
        for i, path in enumerate(dosage_paths):
            fam = fam_paths[i] if fam_paths is not None else None
            batch = self.identify_from_dosage(path, allele_column, fam)
            combined.carriers.update(batch.carriers)
            combined.per_batch_counts[Path(path).stem] = batch.total_carriers
        return combined

    @staticmethod
    def export_carrier_list(result: CarrierResult, output_path: str | Path) -> None:
        """Write carrier IDs, sorted, one per line."""
        with open(output_path, "w") as fh:
            for pid in sorted(result.carriers):
                fh.write(f"{pid}\n")
