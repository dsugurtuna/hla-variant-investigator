# Synthetic example data

Invented for the quickstart and tests; no value comes from a real cohort.

- Two SNP2HLA-style sub-batch outputs (`.dosage`, `.fam`, `.bgl.r2`) for 8 made-up samples (SYN01-SYN08). `sub_batch_002_imputed` lacks `HLA_DRB1_1501` and has a low r2 for `HLA_DRB1_0401`, so the audit and quality checks have something to find.
- `id_map.csv` maps made-up clinical IDs to genotyping IDs; `cohort.txt` is a clinical cohort list with one ID (CLIN99) that has no mapping.
