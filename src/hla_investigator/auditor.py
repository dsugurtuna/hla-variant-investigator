"""Check that expected HLA markers are present in every sub-batch file."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .dosage import read_markers

# HLA-DRB1 alleles at four-digit (two-field) resolution, as named in SNP2HLA
# output (HLA_DRB1_0401 is DRB1*04:01). A default panel for audits; pass your
# own list for other genes or reference panels.
DEFAULT_DRB1_ALLELES = [
    f"HLA_DRB1_{a}"
    for a in [
        "0101", "0301", "0401", "0402", "0403", "0404", "0405",
        "0701", "0801", "0802", "0901", "1001", "1101", "1104",
        "1201", "1301", "1302", "1401", "1501", "1502", "1601", "1602",
    ]
]  # fmt: skip


@dataclass
class AuditReport:
    """Markers found and missing per file."""

    expected_markers: list[str]
    found_markers: dict[str, set[str]] = field(default_factory=dict)
    missing_markers: dict[str, set[str]] = field(default_factory=dict)

    @property
    def all_consistent(self) -> bool:
        """True if every file contains every expected marker."""
        return all(not m for m in self.missing_markers.values())


class DosageAuditor:
    """Audit marker presence across .raw, .dosage, .bim or .bgl.r2 files."""

    def __init__(self, expected_markers: list[str] | None = None) -> None:
        self.expected_markers = expected_markers or DEFAULT_DRB1_ALLELES

    def audit_file(self, file_path: str | Path) -> tuple[set[str], set[str]]:
        """Return ``(found, missing)`` expected markers for one file."""
        present = set(read_markers(file_path))
        expected = set(self.expected_markers)
        return expected & present, expected - present

    def audit_batch(self, file_paths: Sequence[str | Path]) -> AuditReport:
        """Audit several files (one per sub-batch)."""
        report = AuditReport(expected_markers=list(self.expected_markers))
        for fp in file_paths:
            name = Path(fp).name
            found, missing = self.audit_file(fp)
            report.found_markers[name] = found
            report.missing_markers[name] = missing
        return report

    @staticmethod
    def format_report(report: AuditReport) -> str:
        lines = [
            "HLA Marker Audit",
            "=" * 40,
            f"Expected markers: {len(report.expected_markers)}",
            f"Consistent: {'Yes' if report.all_consistent else 'No'}",
            "",
        ]
        for name in sorted(report.found_markers):
            missing = report.missing_markers[name]
            lines.append(
                f"  {name}: {len(report.found_markers[name])} found, "
                f"{len(missing)} missing"
            )
            lines.extend(f"    - {m}" for m in sorted(missing))
        return "\n".join(lines)
