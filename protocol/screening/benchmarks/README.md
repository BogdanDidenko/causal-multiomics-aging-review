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
- `title_abstract_stability_holdout_v6_v0.51.0_25.csv`: evaluated once against
  frozen `v0.91.0`, failed, and is now accessed evaluation evidence that must
  not be used for calibration.
- `title_abstract_calibration_v0.92.0_16.csv`: visible calibration subset
  sampled from the 41 records that remained untouched after v6.
- `title_abstract_stability_holdout_v7_v0.92.0_25.csv`: evaluated exactly once
  against frozen `v0.95.0`, failed, and is now accessed evaluation evidence
  that must not be used for calibration.
- `title_abstract_holdout_v2_quarantined_25.csv`: invalidated after accidental
  partial disclosure and never valid as final evidence.

The `v5` selection was deterministic and disjoint from the accessed 50-record
development set and 25-record `v4` set. Its fixed SHA-256 is
`3caaa4406ece8ca0ac147b20f9e4b912f1323fbf925165517a790082c000f06c`.
Selection details, stratum counts, and the failed evaluation are recorded in
`calibration_cycle_v0.41.0_manifest.json`.

The v7 split is deterministic and recorded in
`calibration_cycle_v0.92.0_manifest.json`. The sealed file has SHA-256
`17fa64ed5893f6a9c44803d18b87dae9677b760e1d6e264a761b4066270faca5`.
It is reserved for one evaluation after the complete `v0.95.0` candidate is
frozen in Git. That evaluation was run after freeze commit `6a6f1a7`; it
failed with `0.96` final-route and `0.80` decisive and all-tracked agreement.

All expert fields remain blank. Sampling strata are retrieval diagnostics, not
eligibility labels. Stability evaluation therefore measures repeated-run
agreement, not accuracy against expert decisions.

The 60-paper full-text benchmark and 20-paper section-selector gold subset
remain pending until full texts have been retrieved and independently
annotated. They must not be synthesized from title/abstract predictions.
