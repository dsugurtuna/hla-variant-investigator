"""HLA Variant Investigator — forensic analysis toolkit for HLA imputation datasets."""

__version__ = "2.0.0"

from .carrier import CarrierIdentifier, CarrierResult
from .auditor import DosageAuditor, AuditReport
from .screener import DiseaseScreener, ScreeningResult
from .quality import QualityValidator, QualityReport

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
