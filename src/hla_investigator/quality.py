"""Imputation quality validation module.

Cross-references expected HLA markers against Beagle R-squared quality
files to verify imputation completeness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


@dataclass
class QualityReport:
    """Report from quality validation."""

    expected_markers: List[str]
    confirmed_present: Set[str] = field(default_factory=set)
    confirmed_missing: Set[str] = field(default_factory=set)
    quality_scores: Dict[str, float] = field(default_factory=dict)

    @property
    def completeness_rate(self) -> float:
        if len(self.expected_markers) == 0:
            return 0.0
        return len(self.confirmed_present) / len(self.expected_markers)


class QualityValidator:
    """Validate HLA imputation quality from Beagle R-squared files.

    Parameters
    ----------
    expected_markers : list of str
        HLA markers to look for in quality files.
    min_r2 : float
        Minimum R-squared threshold for acceptable quality.
    """

    def __init__(
        self,
        expected_markers: List[str],
        min_r2: float = 0.0,
    ) -> None:
        self.expected_markers = expected_markers
        self.min_r2 = min_r2

    def _parse_r2_file(self, path: Path) -> Dict[str, float]:
        """Parse a Beagle .bgl.r2 file. Returns marker → R² mapping."""
        scores: Dict[str, float] = {}
        with open(path) as fh:
            for line in fh:
                parts = line.strip().split()
                if len(parts) >= 2:
                    marker = parts[0]
                    try:
                        r2 = float(parts[1])
                    except ValueError:
                        continue
                    scores[marker] = r2
        return scores

    def validate(self, r2_paths: List[str | Path]) -> QualityReport:
        """Validate quality across one or more R-squared files.

        Parameters
        ----------
        r2_paths : list of paths
            Beagle .bgl.r2 files to scan.

        Returns
        -------
        QualityReport
        """
        all_scores: Dict[str, float] = {}
        for rp in r2_paths:
            all_scores.update(self._parse_r2_file(Path(rp)))

        expected_set = set(self.expected_markers)
        present = set()
        missing = set()
        filtered_scores: Dict[str, float] = {}

        for marker in expected_set:
            if marker in all_scores:
                if all_scores[marker] >= self.min_r2:
                    present.add(marker)
                    filtered_scores[marker] = all_scores[marker]
                else:
                    missing.add(marker)
            else:
                missing.add(marker)

        return QualityReport(
            expected_markers=list(expected_set),
            confirmed_present=present,
            confirmed_missing=missing,
            quality_scores=filtered_scores,
        )

    @staticmethod
    def format_report(report: QualityReport) -> str:
        """Format a human-readable quality report."""
        lines = [
            "HLA Imputation Quality Report",
            "=" * 40,
            f"Expected markers:   {len(report.expected_markers)}",
            f"Confirmed present:  {len(report.confirmed_present)}",
            f"Confirmed missing:  {len(report.confirmed_missing)}",
            f"Completeness:       {report.completeness_rate:.1%}",
        ]
        if report.confirmed_missing:
            lines.append("\nMissing markers:")
            for m in sorted(report.confirmed_missing):
                lines.append(f"  - {m}")
        return "\n".join(lines)
