"""Dosage header auditing module.

Inspects imputation output files for expected HLA markers, checks header
consistency, and reports allele availability across sub-batches.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# Standard DRB1 two-digit alleles expected in a complete imputation
DEFAULT_DRB1_ALLELES = [
    f"HLA_DRB1_{a}"
    for a in [
        "0101",
        "0301",
        "0401",
        "0402",
        "0403",
        "0404",
        "0405",
        "0701",
        "0801",
        "0802",
        "0901",
        "1001",
        "1101",
        "1104",
        "1201",
        "1301",
        "1302",
        "1401",
        "1501",
        "1502",
        "1601",
        "1602",
    ]
]


@dataclass
class AuditReport:
    """Report from a dosage header audit."""

    expected_markers: list[str]
    found_markers: dict[str, set[str]] = field(default_factory=dict)
    missing_markers: dict[str, set[str]] = field(default_factory=dict)

    @property
    def all_consistent(self) -> bool:
        """True if every batch contains all expected markers."""
        return all(len(m) == 0 for m in self.missing_markers.values())


class DosageAuditor:
    """Audit HLA dosage files for marker presence and consistency.

    Parameters
    ----------
    expected_markers : list of str, optional
        Markers to check for. Defaults to the standard DRB1 panel.
    """

    def __init__(self, expected_markers: list[str] | None = None) -> None:
        self.expected_markers = expected_markers or DEFAULT_DRB1_ALLELES

    def _read_header(self, path: Path) -> list[str]:
        """Read the first line of a file and return column names."""
        with open(path) as fh:
            first_line = fh.readline().strip()
        return first_line.split("\t")

    def audit_file(self, file_path: str | Path) -> tuple[set[str], set[str]]:
        """Audit a single file. Returns (found, missing) marker sets."""
        headers = set(self._read_header(Path(file_path)))
        expected = set(self.expected_markers)
        found = headers & expected
        missing = expected - headers
        return found, missing

    def audit_batch(self, file_paths: list[str | Path]) -> AuditReport:
        """Audit multiple dosage files for marker consistency.

        Parameters
        ----------
        file_paths : list of paths
            Dosage files (one per sub-batch) to audit.

        Returns
        -------
        AuditReport
        """
        report = AuditReport(expected_markers=list(self.expected_markers))
        for fp in file_paths:
            name = Path(fp).stem
            found, missing = self.audit_file(fp)
            report.found_markers[name] = found
            report.missing_markers[name] = missing
        return report

    @staticmethod
    def format_report(report: AuditReport) -> str:
        """Format a human-readable audit report."""
        lines = [
            "HLA Dosage Header Audit",
            "=" * 40,
            f"Expected markers: {len(report.expected_markers)}",
            f"Consistent: {'Yes' if report.all_consistent else 'No'}",
            "",
        ]
        for batch in sorted(report.found_markers.keys()):
            found = len(report.found_markers[batch])
            missing = len(report.missing_markers[batch])
            lines.append(f"  {batch}: {found} found, {missing} missing")
            if missing > 0:
                for m in sorted(report.missing_markers[batch]):
                    lines.append(f"    - {m}")
        return "\n".join(lines)
