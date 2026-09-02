# Causal extraction status

Last updated: 2026-09-02; v0.3.0 development stability result.

> **Current entry point:** `README.md`. There is no active causal-extraction
> instrument. Version `v0.3.0` is a frozen failed development baseline;
> opening that directory does not imply production approval.

## Production status

There is currently no approved production causal-extraction instrument.

The frozen `v0.3.0` free-enumeration experiment completed 60/60 valid calls
(12 reports, five repeats). Exact report agreement was 1/12 (8.3%) for both
the three-repeat and five-repeat views. Five-repeat exact agreement for the
analysis-anchor set was also 1/12. The instrument therefore failed its
prespecified 100% stability gate and must not be used on the remaining 89
reports.

The failure localizes the main instability: source sufficiency was stable in
12/12 reports, analysis count was stable in 7/12, and the conceptual reference
analysis set was stable in 8/12, while equivalent evidence-anchor selection,
validation classification, and analysis-unit boundaries varied. The next
prospective experiment must separate candidate discovery from candidate
classification and preserve `v0.3.0` unchanged as its baseline.

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

The immediate next experiment is the candidate-boundary ablation defined in
`design_decisions/2026-09-02-v0.3.0-free-enumeration-failure.md`. It reuses the
same frozen 12-report development set and changes one factor: candidate units
and canonical evidence anchors are fixed before repeated classification.

Processing the remaining 89 eligible reports remains blocked until:

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
