"""Check expected HLA markers against Beagle r2 values."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .dosage import read_r2


@dataclass
class QualityReport:
    """Which expected markers were imputed, and how well."""

    expected_markers: list[str]
    confirmed_present: set[str] = field(default_factory=set)
    absent: set[str] = field(default_factory=set)
    below_threshold: set[str] = field(default_factory=set)
    quality_scores: dict[str, float] = field(default_factory=dict)

    @property
    def confirmed_missing(self) -> set[str]:
        """Absent or below the r2 threshold."""
        return self.absent | self.below_threshold

    @property
    def completeness_rate(self) -> float:
        if not self.expected_markers:
            return 0.0
        return len(self.confirmed_present) / len(self.expected_markers)


class QualityValidator:
    """Validate imputation quality from one or more ``.bgl.r2`` files.

    With several files (one per sub-batch) a marker's score is its lowest
    r2 across files, so one poorly imputed sub-batch is not hidden by the
    others. A marker missing from any file is reported as absent.
    """

    def __init__(self, expected_markers: list[str], min_r2: float = 0.0) -> None:
        self.expected_markers = list(expected_markers)
        self.min_r2 = min_r2

    def validate(self, r2_paths: Sequence[str | Path]) -> QualityReport:
        per_file = [read_r2(p) for p in r2_paths]
        report = QualityReport(expected_markers=self.expected_markers)
        for marker in self.expected_markers:
            scores = [f[marker] for f in per_file if marker in f]
            if not per_file or len(scores) < len(per_file):
                report.absent.add(marker)
                continue
            worst = min(scores)
            report.quality_scores[marker] = worst
            if worst >= self.min_r2:
                report.confirmed_present.add(marker)
            else:
                report.below_threshold.add(marker)
        return report

    @staticmethod
    def format_report(report: QualityReport) -> str:
        lines = [
            "HLA Imputation Quality Report",
            "=" * 40,
            f"Expected markers:   {len(report.expected_markers)}",
            f"Confirmed present:  {len(report.confirmed_present)}",
            f"Absent:             {len(report.absent)}",
            f"Below r2 threshold: {len(report.below_threshold)}",
            f"Completeness:       {report.completeness_rate:.1%}",
        ]
        for title, markers in (
            ("Absent", report.absent),
            ("Below r2 threshold", report.below_threshold),
        ):
            if markers:
                lines.append(f"\n{title}:")
                for m in sorted(markers):
                    score = report.quality_scores.get(m)
                    suffix = f"  (r2 {score:.2f})" if score is not None else ""
                    lines.append(f"  - {m}{suffix}")
        return "\n".join(lines)
