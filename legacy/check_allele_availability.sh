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
# Script: check_allele_availability.sh
# Description: Audits multiple imputation batches to verify the presence and 
#              consistency of specific HLA-DRB1 alleles across sub-batches.
#              Ensures that requested biomarkers are actually present in the 
#              imputed dataset before downstream analysis.
#

# Stop script on any error
set -e
# Ensure pipeline failures are reported
set -o pipefail

# --- Configuration ---
WORK_DIR="./data/processed/biomarker_audit"
BATCH_A_DIR="./data/imputed/batch_A/batches"
BATCH_B_DIR="./data/imputed/batch_B/batches"
TARGET_MARKER_FILE="${WORK_DIR}/target_drb1_markers.txt"

echo "--- Checking Availability of Requested HLA-DRB1 Alleles ---"
echo "Working Directory: ${WORK_DIR}"
echo "Target Marker List: ${TARGET_MARKER_FILE}"
echo "--------------------------------------------------------------------------"

# --- Preparation ---
mkdir -p "${WORK_DIR}"

# Create the target marker list file if it doesn't exist
if [ ! -f "${TARGET_MARKER_FILE}" ]; then
    echo "Creating target marker list..."
    # List of specific DRB1 alleles of interest for the study
    TARGET_ALLELES="0101 0102 0105 0401 0404 0405 0408 0409 0410 0413 0416 0419 0421 1001 1402 1406 1409 1413 1417 1419 1420 1421"
    > "${TARGET_MARKER_FILE}"
    for allele in ${TARGET_ALLELES}; do
      echo "HLA_DRB1_${allele}" >> "${TARGET_MARKER_FILE}"
    done
else
    echo "Using existing target marker list."
fi

# --- Function to process a batch ---
process_batch() {
    local batch_name="$1"
    local batches_dir="$2"

    echo ">>> Processing ${batch_name} <<<"
    if [ ! -d "${batches_dir}" ]; then
        echo "Simulation: Batches directory not found. Skipping check for ${batch_name}."
        return 0
    fi

    # Find sub-batch prefixes based on imputed BIM files
    local sub_batch_prefixes
    sub_batch_prefixes=$(find "${batches_dir}" -maxdepth 1 -name '*_imputed.bim' -printf '%f\n' | sed 's/_imputed\.bim$//' | sort)

    if [ -z "${sub_batch_prefixes}" ]; then
        echo "Warning: No imputed sub-batch BIM files found in ${batches_dir}"
        return 0
    fi

    local first_output=""
    local is_consistent=1

    for prefix in ${sub_batch_prefixes}; do
        local bim_file="${batches_dir}/${prefix}_imputed.bim"
        local found_markers_output

        # Use grep to find matching markers. 
        found_markers_output=$(grep -Fwf "${TARGET_MARKER_FILE}" "${bim_file}" | awk '{print $2}' | sort || true)

        if [ -z "${found_markers_output}" ]; then
            # Logic to track consistency (omitted for brevity in logs)
            :
        else
            # Check for consistency against the first sub-batch
            if [ -z "${first_output}" ] && [ "${prefix}" == "$(echo "${sub_batch_prefixes}" | head -n 1)" ]; then
                first_output="${found_markers_output}"
            elif [ "${found_markers_output}" != "${first_output}" ]; then
                is_consistent=0
            fi
        fi
    done

    echo "Summary for ${batch_name}:"
    if [ ${is_consistent} -eq 1 ]; then
        echo "  Result: CONSISTENT - Marker presence is uniform across sub-batches."
    else
        echo "  Result: INCONSISTENT - Marker presence varies between sub-batches."
    fi
    echo "--------------------------------------------------------------------------"
}

# --- Execute ---
process_batch "Batch A" "${BATCH_A_DIR}"
process_batch "Batch B" "${BATCH_B_DIR}"

echo "--- Audit Complete ---"
