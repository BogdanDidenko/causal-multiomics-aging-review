# Review context contract

Classify only how the fixed candidate relates to aging and to the report's
multi-omics workflow. Use the same definitions as v0.3.0.

`aging_role`:

- `lifespan_or_longevity_outcome`
- `biological_or_chronological_aging_outcome`
- `cellular_senescence_outcome`
- `age_related_disease_or_decline_outcome`
- `mechanistic_support_for_aging_link`

`multiomics_role`:

- `omics_exposure_in_causal_design`
- `multiomics_outcomes_under_causal_design`
- `omics_candidate_followed_by_perturbation`
- `formal_cross_omics_directed_model`
- `report_level_multiomics_support`

Choose the value for this candidate's design-level unit, rather than the broad
topic or overall conclusion of the paper. Return one value per field and
candidate. Do not classify any other property.
