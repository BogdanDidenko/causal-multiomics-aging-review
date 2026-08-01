# Annotation Manual v1.0.0

## Workflow

1. Expert 1 and Expert 2 annotate independently from the source record.
2. Each criterion is labeled before the route or evidence level.
3. Missing title/abstract detail is `unclear`, not negative evidence.
4. Disagreements are discussed only after both annotation files are locked.
5. Adjudicated values and the reason for every change are retained.
6. Model outputs are revealed only after the human gold file is frozen.

## Title/abstract fields

- `report_type`: `empirical_primary`, `nonempirical`, or `unclear`.
- `bio_health_scope`: `yes`, `no`, or `unclear`.
- `aging_process_relevance`: direct aging-process analysis, not age as a
  demographic/covariate/background label.
- `multiomics_evidence`: `explicit_multiomics`, `two_or_more_layers`,
  `single_or_no_layer`, or `unclear`.
- `current_report_layer_use`: whether the named layers are analyzed in the
  current report.
- `causal_basis`: one value from the frozen seven-value v1 contract.
- `expected_route`: `seek_full_text` or `exclude`.
- `first_failed_criterion`: EC1-EC5, `none`, or `unclear`.

An intervention, instrument, perturbation, temporal identification design, or
other assessable effect design is `named_causal_effect_design`. A formal DAG,
SCM, directed SEM/mediation model, Bayesian network, or named causal-discovery
algorithm without effect identification is `formal_directed_hypothesis`.
Mechanistic or directional wording without such a method is
`causal_wording_only`.

## Full-text fields

Experts verify IC1-IC5, the omics layers and their roles, design family,
identification status, estimand, assumptions, diagnostics, and validation.
Levels are assigned from the frozen definitions:

- 0: context/ineligible or no multi-omics;
- 1: association/prediction only;
- 2: formal causal hypothesis without sufficient identification;
- 3: assessable causal contrast and assumptions;
- 4: Level 3 plus independent validation of the same causal link.

Level 2 is synthesized separately from Levels 3-4. Colocalization alone is not
identification. A perturbation of a mechanism does not automatically validate
a population genetic effect, and an RCT treatment effect does not by itself
identify molecular mediation.

## Reliability

Report criterion-level exact agreement, Cohen's kappa, confusion matrices, and
Wilson 95% intervals. Record every adjudication and every later human override
of a model output. At least 20% of records are re-annotated blind by each
expert after a prespecified washout period for intra-rater agreement.
