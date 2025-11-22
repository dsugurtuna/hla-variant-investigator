#!/usr/bin/awk -f
#
# Portfolio/Educational Purpose Only
# -----------------------------------------------------------------------------
# Script: id_mapper.awk
# Description: A reusable AWK utility for mapping between different ID schemes
#              (e.g., Clinical IDs <-> Genotyping IDs).
#
# Usage: awk -f id_mapper.awk mapping_file.csv input_list.txt
#
# Input Format:
#   - mapping_file.csv: Col 1 = External ID, Col 2 = Internal ID
#   - input_list.txt:   List of IDs to translate (Col 1)
#

BEGIN {
    FS = "[\t, ]+"
}

function dequote(s) {
    gsub(/"/, "", s)
    return s
}

# Phase 1: Read the Mapping File (First file argument)
NR == FNR {
    # Skip header if present (heuristic: if col 1 is "ID" or similar)
    if (FNR == 1 && tolower($1) ~ /id/) next
    
    # Store mapping: External -> Internal
    # Adjust indices based on your specific mapping file structure
    # Here assuming: Col 1 = External, Col 2 = Internal
    ext_id = dequote($1)
    int_id = dequote($2)
    
    if (ext_id != "" && int_id != "") {
        map_ext_to_int[ext_id] = int_id
        map_int_to_ext[int_id] = ext_id
    }
    next
}

# Phase 2: Process the Input List (Second file argument)
{
    query_id = dequote($1)
    
    # Check if it's an External ID -> Print Internal
    if (query_id in map_ext_to_int) {
        print map_ext_to_int[query_id]
    }
    # Check if it's an Internal ID -> Print External
    else if (query_id in map_int_to_ext) {
        print map_int_to_ext[query_id]
    }
}
