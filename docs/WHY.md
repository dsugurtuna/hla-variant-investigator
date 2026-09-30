# Why it's built this way

## The problem

After HLA imputation, most requests are small and specific: who carries this allele, is it present in every sub-batch, can we trust it. They cut across many files and two ID schemes, and a quiet mistake (the wrong allele counted, a missing sub-batch, an unmapped ID) produces a confident but wrong list.

## Design choices

**Why convert every dosage to the "present" allele?** Because SNP2HLA codes HLA alleles as presence (`P`) or absence (`A`), and both PLINK `--recode A` and SNP2HLA's `.dosage` count whichever allele comes first. If that is `A`, a dosage of 2 means "definitely not a carrier". The readers check the counted allele and flip `x -> 2 - x` when needed, for `HLA_` markers only.

**Why one reader for everything?** Because carriers, audits and screening must agree about what a file says. Three separate parsers were how the original version ended up reading tab-separated headers that PLINK never writes.

**Why take the lowest r2 across sub-batches?** Because imputation quality can differ by sub-batch, and the people in a poor sub-batch are affected by it. An average would hide them.

**Why separate "absent" from "below threshold"?** Because they have different fixes. An absent allele is usually missing from the reference panel; a low-r2 allele was imputed, just not well.

**Why report screening results in clinical IDs, and list the unmapped?** Because the requester works in clinical IDs, genotyping IDs are more sensitive, and "not found" must not be confused with "not a carrier".

**Why exit codes on `audit` and `quality`?** So a delivery pipeline can stop on a failed check instead of relying on someone reading the output.

## Questions worth asking

**"What threshold makes someone a carrier?"**
It depends on the use. The default (any non-zero dosage) matches the original scripts and maximises sensitivity for a first-pass list; 0.5 is a common screening cut-off for imputed data. Either way it is a screening call on an imputed value. For anything clinical, confirm by lab HLA typing.

**"Four-digit resolution: is HLA_DRB1_0401 the same as DRB1\*04:01?"**
In SNP2HLA naming, yes: it is the two-field allele DRB1\*04:01. Reference panels differ in which alleles they contain, so an allele can be absent simply because the panel never had it. That is why the quality check reports absent markers separately.

**"What about ancestry? Is imputation equally good for everyone?"**
No. Imputation accuracy depends on how well the reference panel represents the sample's ancestry, and r2 is an estimate, not a guarantee. The quality check surfaces low r2 but cannot detect a panel mismatch on its own; checking r2 by ancestry group, and validating against typed samples, is the honest answer.

## What's next

- Detect duplicate or conflicting entries in the ID map.
- Screen several alleles at once.
- Show each carrier's dosage so borderline calls are visible.
