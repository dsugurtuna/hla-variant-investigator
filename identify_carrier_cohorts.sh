#!/bin/bash
#
# Portfolio/Educational Purpose Only
# -----------------------------------------------------------------------------
# This script is part of a bioinformatics portfolio demonstrating technical
# competencies in genomic data processing and pipeline engineering.
#
# It contains sanitized code derived from production workflows. All internal
# paths, keys, and proprietary data have been removed or replaced with
# generic placeholders.
#
# Disclaimer: This code is for demonstration purposes and is not intended
# for clinical use without validation.
# -----------------------------------------------------------------------------
#
# Script: identify_carrier_cohorts.sh
# Description: Identifies participants carrying specific HLA-DRB1 alleles 
#              from large-scale imputed datasets. Uses PLINK to extract 
#              dosages and AWK to filter for carriers (dosage > 0).
#

set -e
set -o pipefail

# --- Configuration ---
STUDY_DIR="./data/processed/cohort_identification"
RESULTS_BASE="./data/imputed/batch_A"
BATCHES_DIR="${RESULTS_BASE}/batches"
TARGET_MARKER_FILE="${STUDY_DIR}/target_drb1_markers.txt"
FINAL_LIST="${STUDY_DIR}/final_carrier_list.txt"
TEMP_COMBINED="${STUDY_DIR}/temp_combined_carriers.txt"
NUM_THREADS=4

echo "--- Starting HLA-DRB1 Carrier Identification ---"
echo "Study Directory: ${STUDY_DIR}"

# --- Preparation ---
mkdir -p "${STUDY_DIR}"

# Create target marker list if missing
if [ ! -f "${TARGET_MARKER_FILE}" ]; then
    echo "Creating target marker list..."
    TARGET_ALLELES="0101 0102 0105 0401 0404 0405 0408 0409 0410 0413 0416 0419 0421 1001 1402 1406 1409 1413 1417 1419 1420 1421"
    > "${TARGET_MARKER_FILE}"
    for allele in ${TARGET_ALLELES}; do
      echo "HLA_DRB1_${allele}" >> "${TARGET_MARKER_FILE}"
    done
fi

# Check input directory
if [ ! -d "${BATCHES_DIR}" ]; then
    echo "Simulation: Input directory not found. Creating mock data for demonstration."
    mkdir -p "${BATCHES_DIR}"
    touch "${BATCHES_DIR}/batch_01_imputed.bim" "${BATCHES_DIR}/batch_01_imputed.bed" "${BATCHES_DIR}/batch_01_imputed.fam"
fi

# Find sub-batches
SUB_BATCH_PREFIXES=$(find "${BATCHES_DIR}" -maxdepth 1 -name '*_imputed.bim' -printf '%f\n' | sed 's/_imputed\.bim$//' | sort)

if [ -z "${SUB_BATCH_PREFIXES}" ]; then
    echo "Error: No sub-batches found."
    exit 1
fi

> "${TEMP_COMBINED}"

# --- Process Each Sub-batch ---
for prefix in ${SUB_BATCH_PREFIXES}; do
    echo "Processing sub-batch: ${prefix}..."
    BFILE_PATH="${BATCHES_DIR}/${prefix}_imputed"
    PRESENT_MARKERS_TEMP="${STUDY_DIR}/temp_present_${prefix}.txt"
    RECODE_PREFIX="${STUDY_DIR}/temp_recode_${prefix}"
    RAW_FILE="${RECODE_PREFIX}.raw"
    CARRIERS_TEMP="${STUDY_DIR}/temp_carriers_${prefix}.txt"

    # Mocking PLINK execution for portfolio if binary is missing
    if ! command -v plink &> /dev/null; then
        echo "  [Simulation] PLINK not installed. Skipping actual extraction."
        continue
    fi

    # Identify present markers
    grep -Fwf "${TARGET_MARKER_FILE}" "${BFILE_PATH}.bim" | awk '{print $2}' | sort > "${PRESENT_MARKERS_TEMP}"

    if [ ! -s "${PRESENT_MARKERS_TEMP}" ]; then
        echo "  No target markers found in this sub-batch."
        rm -f "${PRESENT_MARKERS_TEMP}"
        continue
    fi

    # Extract dosages
    plink --bfile "${BFILE_PATH}" \
          --extract "${PRESENT_MARKERS_TEMP}" \
          --recode A \
          --out "${RECODE_PREFIX}" \
          --threads ${NUM_THREADS} > /dev/null 2>&1

    if [ ! -f "${RAW_FILE}" ]; then
        echo "  PLINK execution failed or produced no output."
        continue
    fi

    # Parse .raw file for carriers (Dosage > 0)
    awk '
    BEGIN { carrier_count = 0 }
    NR > 1 { 
        is_carrier = 0;
        for (i = 7; i <= NF; i++) {
            if ($i != "NA" && $i > 0) {
                is_carrier = 1;
                break; 
            }
        }
        if (is_carrier) {
            print $1, $2; 
            carrier_count++;
        }
    }
    END {
        print "  Found " carrier_count " carriers." > "/dev/stderr"
    }
    ' "${RAW_FILE}" > "${CARRIERS_TEMP}"

    cat "${CARRIERS_TEMP}" >> "${TEMP_COMBINED}"
    
    # Cleanup per batch
    rm -f "${PRESENT_MARKERS_TEMP}" "${RECODE_PREFIX}"* "${CARRIERS_TEMP}"

done

# --- Finalization ---
if [ -s "${TEMP_COMBINED}" ]; then
    sort -u "${TEMP_COMBINED}" > "${FINAL_LIST}"
    echo "Total unique carriers identified: $(wc -l < "${FINAL_LIST}")"
else
    echo "No carriers found."
fi

rm -f "${TEMP_COMBINED}"
echo "--- Identification Complete ---"
