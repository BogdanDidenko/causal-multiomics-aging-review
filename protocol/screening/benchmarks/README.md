# Aging-specific Benchmark Candidates

All benchmark records come from the fresh aging-specific retrieval. Earlier
causal multi-omics decisions were not reused as labels.

## Access Status

- `title_abstract_calibration_v0.24.0_50.csv`: visible 50-record development
  set.
- `title_abstract_stability_holdout_v4_metadata_v0.24.0_25.csv`: evaluated once
  against frozen `v0.40.0`, then opened and used as diagnostic evidence.
- `title_abstract_stability_holdout_v5_v0.41.0_25.csv`: evaluated once against
  frozen `v0.50.0`, failed, and is now accessed diagnostic evidence.
- `title_abstract_regression_v0.41.0_remaining_66.csv`: untouched remainder
  reserved for a later calibration cycle.
- `title_abstract_holdout_v2_quarantined_25.csv`: invalidated after accidental
  partial disclosure and never valid as final evidence.

The `v5` selection was deterministic and disjoint from the accessed 50-record
development set and 25-record `v4` set. Its fixed SHA-256 is
`3caaa4406ece8ca0ac147b20f9e4b912f1323fbf925165517a790082c000f06c`.
Selection details, stratum counts, and the failed evaluation are recorded in
`calibration_cycle_v0.41.0_manifest.json`.

All expert fields remain blank. Sampling strata are retrieval diagnostics, not
eligibility labels. Stability evaluation therefore measures repeated-run
agreement, not accuracy against expert decisions.

The 60-paper full-text benchmark and 20-paper section-selector gold subset
remain pending until full texts have been retrieved and independently
annotated. They must not be synthesized from title/abstract predictions.
