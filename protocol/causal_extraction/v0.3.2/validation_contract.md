# Validation contract

Classify only the strongest reported validation for the same causal link as the
fixed candidate. Use the same values as v0.3.0.

`validation_strength`:

- `none`
- `supportive_same_experiment`
- `link_specific_colocalization`
- `orthogonal_same_link`
- `independent_replication`
- `unclear`

Colocalization, replication, rescue, reverse perturbation, and orthogonal
assays may be validation evidence for a qualifying analysis. They do not count
when they concern a different exposure-outcome link. Return one value per
candidate. Do not classify any other property or return a causal Level.
