# HLA Variant Investigator

**A specialized toolkit for forensic analysis, carrier identification, and quality auditing of HLA imputation datasets.**

This repository contains a suite of Bash scripts designed to interrogate large-scale genomic datasets (specifically HLA imputation results) to identify specific allele carriers, audit data consistency, and validate imputation quality.

## 📂 Repository Contents

| Script | Description |
| :--- | :--- |
| `identify_carrier_cohorts.sh` | **Cohort Discovery**: Scans massive PLINK datasets to identify participants carrying specific HLA-DRB1 alleles. Uses efficient dosage extraction and parsing. |
| `check_allele_availability.sh` | **Data Integrity**: Audits multiple imputation batches to ensure that requested biomarkers are consistently present across all sub-batches. |
| `audit_dosage_headers.sh` | **Pipeline Forensics**: Inspects dosage file headers to verify column mapping and marker presence, essential for debugging pipeline failures. |
| `validate_imputation_quality.sh` | **Quality Control**: Cross-references expected marker lists against Beagle R-squared ($R^2$) quality files to detect missing or poorly imputed variants. |

## 🚀 Key Features

*   **High-Throughput Processing**: Optimized for handling large-scale Biobank datasets split into thousands of sub-batches.
*   **Robust Error Handling**: Implements strict error checking (`set -e`, `pipefail`) to prevent silent failures in critical pipelines.
*   **Automated Reporting**: Generates clear, concise summaries of carrier counts and data consistency.
*   **Forensic Auditing**: Tools specifically designed to "debug" data—finding out *why* a marker is missing or *where* a pipeline diverged.

## 🛠️ Usage Examples

### Identifying Carriers
To find all participants carrying the `HLA-DRB1*01:01` allele:
```bash
./identify_carrier_cohorts.sh
```
*Output: Generates a `final_carrier_list.txt` containing unique participant IDs.*

### Auditing Data Consistency
To check if a set of markers exists across all processed batches:
```bash
./check_allele_availability.sh
```

## ⚠️ Disclaimer
This code is provided for **educational and portfolio purposes**. It is a sanitized version of production scripts used in genomic research. All private data, internal paths, and proprietary keys have been removed.

---
*Created by [dsugurtuna](https://github.com/dsugurtuna)*
