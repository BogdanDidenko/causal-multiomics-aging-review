# Claim-level causal extraction codebook pilot v0.1.0

## Purpose

This is a transparent instrument-development pilot for the claim-level causal
extraction codebook. It does not alter the frozen eligibility ledger, PRISMA
flow, production prompts, or Levels 0-4 assigned in the completed screening
stage.

The pilot asks whether the draft codebook can represent materially different
causal designs without collapsing author language, design provenance,
identification assessability, result direction, and validation into one field.

## Sample

Fifteen full-text-eligible reports were purposively selected from the 101-report
corpus. Selection maximized variation in:

- human, mouse, fly, worm, chicken, tissue, and cell systems;
- randomized and non-randomized interventions;
- biological transfer, pharmacologic and genetic perturbation;
- Mendelian randomization and molecular-QTL analyses;
- mediation, SEM, directed statistical models, and computational
  prioritization;
- positive, null, conflicting, and time-specific findings;
- clear and disputed same-link validation.

This is not a prevalence sample and must not be used to estimate the frequency
of evidence levels in the review corpus.

## Procedure

1. The primary analyst drafted `protocol/causal_extraction/v0.1.0/codebook.md`
   and its JSON Schema before coding the sample.
2. The primary analyst annotated normalized claims from deterministic Docling
   Markdown and attached shortest exact evidence quotations.
3. A deterministic validator checked schema validity, DOI coverage, claim IDs,
   evidence substring grounding, anchor references, and Level mapping.
4. Claude Opus 5 was asked to inspect the frozen draft and source texts in
   read-only mode, independently challenge the coding, and recommend changes.
5. The primary analyst audited each recommendation against the source text.

The Claude review is advisory, not an independent expert gold standard. Any
subsequent revision is versioned rather than silently overwriting this pilot.

## Files

- `reports_15.csv`: purposive report sample and design rationale.
- `claims.jsonl`: primary analyst claim-level coding.
- `self_audit.md`: ambiguities and decisions identified during coding.
- `opus_review.md`: complete external model review plus runtime provenance.
- `cross_audit.md`: item-by-item adjudication of model feedback.

## Interpretation

Passing this pilot means the contract is usable on the selected heterogeneous
cases. It does not establish inter-rater reliability, validity against expert
gold labels, or production readiness.
