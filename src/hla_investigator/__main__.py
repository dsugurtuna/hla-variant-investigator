"""Command-line interface: ``python -m hla_investigator <command>``."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .auditor import DEFAULT_DRB1_ALLELES, DosageAuditor
from .carrier import CarrierIdentifier
from .quality import QualityValidator
from .screener import DiseaseScreener


def _fam_for(path: str) -> str | None:
    """SNP2HLA writes <prefix>.fam next to <prefix>.dosage."""
    if path.endswith(".dosage"):
        return path[: -len(".dosage")] + ".fam"
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hla_investigator")
    sub = parser.add_subparsers(dest="command", required=True)

    carriers = sub.add_parser("carriers", help="carriers of one allele")
    carriers.add_argument("files", nargs="+", help=".raw or .dosage files")
    carriers.add_argument("--allele", required=True)
    carriers.add_argument("--threshold", type=float, default=0.0)
    carriers.add_argument("--out", help="write carrier IDs here")

    audit = sub.add_parser("audit", help="expected markers present in each file")
    audit.add_argument("files", nargs="+", help=".raw, .dosage, .bim or .bgl.r2")
    audit.add_argument("--markers", nargs="+", default=DEFAULT_DRB1_ALLELES)

    quality = sub.add_parser("quality", help="r2 check across .bgl.r2 files")
    quality.add_argument("files", nargs="+")
    quality.add_argument("--markers", nargs="+", required=True)
    quality.add_argument("--min-r2", type=float, default=0.5)

    screen = sub.add_parser("screen", help="carriers within a clinical cohort")
    screen.add_argument("--map", required=True, help="clinical_id,genotyping_id CSV")
    screen.add_argument("--cohort", required=True, help="clinical IDs, one per line")
    screen.add_argument("--dosage", required=True, help=".raw or .dosage file")
    screen.add_argument("--allele", required=True)
    screen.add_argument("--threshold", type=float, default=0.0)

    args = parser.parse_args(argv)

    if args.command == "carriers":
        fams = [_fam_for(f) for f in args.files]
        result = CarrierIdentifier(args.threshold).identify_across_batches(
            args.files,
            args.allele,
            [f or "" for f in fams] if all(fams) else None,
        )
        for name, count in result.per_batch_counts.items():
            print(f"{name}: {count}")
        print(f"{result.allele}: {result.total_carriers} unique carriers")
        if args.out:
            CarrierIdentifier.export_carrier_list(result, args.out)
        return 0

    if args.command == "audit":
        report = DosageAuditor(args.markers).audit_batch(args.files)
        print(DosageAuditor.format_report(report))
        return 0 if report.all_consistent else 1

    if args.command == "quality":
        qreport = QualityValidator(args.markers, args.min_r2).validate(args.files)
        print(QualityValidator.format_report(qreport))
        return 0 if not qreport.confirmed_missing else 1

    cohort = [
        x.strip() for x in Path(args.cohort).read_text().splitlines() if x.strip()
    ]
    sresult = DiseaseScreener(args.map).screen(
        cohort, args.dosage, args.allele, args.threshold, _fam_for(args.dosage)
    )
    print(f"cohort {sresult.cohort_size}, mapped {sresult.mapped_count}")
    print(f"unmapped: {', '.join(sresult.unmapped_ids) or 'none'}")
    print(f"mapped but not genotyped: {', '.join(sresult.not_genotyped) or 'none'}")
    print(f"carriers: {', '.join(sorted(sresult.carriers_found)) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
