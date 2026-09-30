"""HLA Variant Investigator — forensic analysis toolkit for HLA imputation datasets."""

__version__ = "2.0.0"

from .auditor import AuditReport, DosageAuditor
from .carrier import CarrierIdentifier, CarrierResult
from .quality import QualityReport, QualityValidator
from .screener import DiseaseScreener, ScreeningResult

__all__ = [
    "CarrierIdentifier",
    "CarrierResult",
    "DosageAuditor",
    "AuditReport",
    "DiseaseScreener",
    "ScreeningResult",
    "QualityValidator",
    "QualityReport",
]
