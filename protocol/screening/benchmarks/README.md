# Aging-specific Benchmark Candidates

Benchmark records must be sampled only from the fresh aging-specific corpus.
Earlier causal multi-omics decisions are not reused as labels.

Generated title/abstract sets:

- `high_signal_development_25.csv`: visible prompt-development set containing
  the canonical positive.
- `title_abstract_boundary_pilot_25.csv`: visible boundary-case stability
  pilot.
- `title_abstract_regression_116.csv`: disjoint expert-annotation candidate
  set.
- `title_abstract_holdout_v2_quarantined_25.csv`: disjoint but invalidated
  holdout retained only to document accidental partial disclosure.
- `title_abstract_stability_holdout_25.csv`: disjoint v3 holdout sampled after
  excluding every quarantined-v2 record. It remained sealed through prompt
  development and was first accessed for the frozen `v0.16.0` evaluation,
  which failed.
- `title_abstract_boundary_pilot_v0.2.0_25.csv` and
  `title_abstract_boundary_pilot_v0.3.0_25.csv`: visible development revisions
  that replace two malformed conference-abstract records. Their manifests
  record source, replacement, and output hashes.

All expert fields are blank. Sampling strata are retrieval diagnostics, not
eligibility labels. The manifest fixes the corpus hash, seed, set hashes, and
stratum counts.

The 60-paper full-text benchmark and 20-paper section-selector gold subset
remain pending until full texts have been retrieved and independently
annotated. They must not be synthesized from title/abstract predictions.

The regression set remains uninspected. Holdout v3 is no longer sealed after
its one frozen-suite evaluation and may only be used as development evidence
in a future, explicitly new calibration cycle. The quarantined v2 file must
never be used for final evaluation.
