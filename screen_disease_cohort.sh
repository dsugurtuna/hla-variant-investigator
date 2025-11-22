#!/bin/bash
#
# Portfolio/Educational Purpose Only
# -----------------------------------------------------------------------------
# Script: screen_disease_cohort.sh
# Description: Identifies participants from a specific clinical cohort (e.g., RA)
#              who carry a target HLA allele.
#              Handles complex ID mapping (Clinical ID -> Genotyping ID) and
#              parses transposed dosage files (Markers x Participants).
#

set -euo pipefail

# --- Configuration ---
# In production, these would be arguments or env vars
COHORT_LIST_FILE="./data/raw/clinical_cohort_ids.csv"
ID_MAPPING_FILE="./data/raw/id_map.csv"
DOSAGE_DIR="./data/imputed/batches"
TARGET_ALLELE="HLA_DRB1_04"
OUTPUT_FILE="./data/results/cohort_carrier_list.txt"

# --- Setup ---
mkdir -p "$(dirname "$OUTPUT_FILE")"
mkdir -p "./tmp"

# Simulation: Create dummy data if missing
if [ ! -f "$COHORT_LIST_FILE" ]; then
    mkdir -p "$(dirname "$COHORT_LIST_FILE")"
    echo "Clinical_ID" > "$COHORT_LIST_FILE"
    echo "CLIN001" >> "$COHORT_LIST_FILE"
    echo "CLIN002" >> "$COHORT_LIST_FILE"
fi
if [ ! -f "$ID_MAPPING_FILE" ]; then
    echo "Clinical_ID,Genotyping_ID" > "$ID_MAPPING_FILE"
    echo "CLIN001,GENO_A1" >> "$ID_MAPPING_FILE"
    echo "CLIN002,GENO_A2" >> "$ID_MAPPING_FILE"
fi
if [ ! -d "$DOSAGE_DIR" ]; then
    mkdir -p "$DOSAGE_DIR"
    # Create dummy dosage file (Transposed: Row=Allele, Cols=Participants)
    # We need a .fam file to map columns to IDs
    echo "FAM1 GENO_A1 0 0 0 -9" > "$DOSAGE_DIR/batch_01.fam"
    echo "FAM1 GENO_A2 0 0 0 -9" >> "$DOSAGE_DIR/batch_01.fam"
    # Dosage: Allele, then dosage for P1, dosage for P2...
    # P1 (GENO_A1) has dosage 0.0, P2 (GENO_A2) has dosage 1.9
    echo -e "HLA_DRB1_04\t0.0\t1.9" > "$DOSAGE_DIR/batch_01_imputed.dosage"
fi

echo "--- Step 1: Map Clinical IDs to Genotyping IDs ---"
# Uses the reusable AWK utility
# We only want to search for participants who are in our Clinical Cohort
awk -f utils/id_mapper.awk "$ID_MAPPING_FILE" "$COHORT_LIST_FILE" > "./tmp/target_genotyping_ids.txt"

TARGET_COUNT=$(wc -l < "./tmp/target_genotyping_ids.txt" | tr -d ' ')
echo "Mapped $TARGET_COUNT participants from Clinical Cohort to Genotyping IDs."

echo "--- Step 2: Scan Dosage Files for Target Allele ---"
echo "Target Allele: $TARGET_ALLELE"

# Clear output
> "./tmp/matches_internal.txt"

# Loop through batches
# Note: This script handles the specific format where .fam files define column headers
for fam_file in "$DOSAGE_DIR"/*.fam; do
    [ -e "$fam_file" ] || continue
    
    batch_name=$(basename "$fam_file" .fam)
    dosage_file="${DOSAGE_DIR}/${batch_name}_imputed.dosage"
    
    if [ -f "$dosage_file" ]; then
        echo "Scanning batch: $batch_name..."
        
        # AWK Logic:
        # 1. Load target Genotyping IDs into a hash.
        # 2. Find the row for the target allele.
        # 3. For that row, iterate columns.
        # 4. Map column index -> Participant ID using the .fam file.
        # 5. Check if Participant is in Target List AND has Dosage > 0.
        
        awk -v allele="$TARGET_ALLELE" -v fam="$fam_file" '
            BEGIN { FS="\t" }
            
            # Load Target IDs
            NR==FNR { targets[$1]=1; next }
            
            # Process Dosage File Row
            $1 == allele {
                # Read .fam file to get IDs for all columns
                # .fam file is space-delimited, ID is 2nd column
                p_idx = 0
                while ((getline line < fam) > 0) {
                    p_idx++
                    split(line, parts, " ")
                    p_ids[p_idx] = parts[2]
                }
                close(fam)
                
                # Iterate dosage columns (starting at 2)
                # Dosage col 2 corresponds to .fam line 1
                for (i=2; i<=NF; i++) {
                    pid = p_ids[i-1]
                    dosage = $i
                    
                    if ((pid in targets) && (dosage > 0)) {
                        print pid
                    }
                }
            }
        ' "./tmp/target_genotyping_ids.txt" "$dosage_file" >> "./tmp/matches_internal.txt"
    fi
done

echo "--- Step 3: Map Matches back to Clinical IDs ---"
awk -f utils/id_mapper.awk "$ID_MAPPING_FILE" "./tmp/matches_internal.txt" > "$OUTPUT_FILE"

FINAL_COUNT=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')
echo "✅ Found $FINAL_COUNT carriers in the clinical cohort."
echo "Results saved to: $OUTPUT_FILE"

# Cleanup
rm -rf "./tmp"
