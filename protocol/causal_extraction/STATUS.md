# Causal extraction status

Last updated: 2026-08-31; lifecycle clarification after E0 run 1.

> **Current entry point:** `README.md`. There is no active causal-extraction
> codebook. Version `v0.2.0` is explicitly marked `legacy_rejected` in
> `v0.2.0/lifecycle.json`; opening that directory does not imply approval.

## Production status

There is currently no approved production causal-extraction instrument.

Prompt suite `v0.1.1-rc1` and codebook `v0.2.0` are frozen rejected lineage.
They may be cited for instrument-development and methodological postmortem
only. Their candidate records, candidate counts as causal-claim counts, and
derived Levels must not enter the scientific synthesis.

## E0 result

E0 run 1 completed from pre-model revision `328abcf`:

- 132/132 planned calls reached a valid terminal response;
- all evidence atoms were core exactly once in all six reports;
- the evidence-ID arm was valid on 66/66 first attempts and resolved 642/642
  returned IDs;
- the quote arm was valid on 62/66 first attempts and required four retries for
  character-inexact quotations.

The maximum result is `technical_pass_pending_human_semantic_audit`.
`evidence_atom_id` is retained as the grounding interface for the next
development instrument. This does not approve the open causal-analysis
inventory or establish scientific accuracy.

The post-hoc stability audit found that all exact repeat pairs were empty
windows; nonempty full agreement was 0/18 per arm. This is an exploratory
development signal on six contaminated reports, without a preregistered
threshold or human gold. It cannot be represented as a general accuracy or
stability estimate.

## Current gate

The next prospective experiment is E1, defined in
`design_decisions/2026-08-29-e0-result-and-e1-gate.md`. E1 must freeze a new,
disjoint development sample, two-human boundary gold, one-factor unit ablation,
schemas, runtime, and acceptance metrics before model calls.

Processing all 101 eligible reports remains blocked until:

1. E0 semantic-support and analysis-boundary gold are adjudicated;
2. E1 and subsequent development ablations are completed against expert gold;
3. the hierarchical causal-analysis data model is frozen;
4. one configuration passes a single prespecified external or temporal
   sealed-set evaluation acquired after instrument freeze.

## Corrected record

The corrected checkpoint interpretation is in
`../../analysis/causal_extraction/checkpoints/v0.1.1-rc1/two_sample_stability.md`.
The independent Opus 5 audit is in
`../../analysis/causal_extraction/consultations/2026-08-29-opus5-v0.1.1-audit/report.md`.
The E0 compact result is in
`../../analysis/causal_extraction/e0_grounding/v0.1.0_run1/report.md`; its
post-hoc disagreement audit and independent Opus 4.8 critique are stored beside
it and under `../../analysis/causal_extraction/consultations/`.
