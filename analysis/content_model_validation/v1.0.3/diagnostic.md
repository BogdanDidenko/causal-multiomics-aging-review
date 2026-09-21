# CMACM v1.0.3 Prospective Validation Diagnostic

Status: rejected as a production extraction contract; retained as a
development-set result.

## Design

Fifteen canonical reports were selected before execution from the 357-report
post-version-collapse corpus. They were disjoint from all prior causal
extraction, codebook and transfer-check samples. Each full Docling Markdown was
submitted unchanged to three isolated GPT-5.6 Terra Medium sessions.

Two preceding transport-only preflights are preserved separately. Neither
v1.0.0 nor v1.0.1 yielded a scientific model response. A v1.0.2 preflight
generated one response, which exposed an incorrect linearization-membership
contract; that report was excluded from this v1.0.3 sample.

## Observed Stability

Across the three structural outputs per report:

| Outcome | Exact agreement |
|---|---:|
| Complete Foundation structure and all linearization member sizes | 1/15 |
| Workflow count | 8/15 |
| Causal-link count | 5/15 |
| Workflow design-family set | 10/15 |

Twenty-eight of 45 outputs passed exact quote grounding on the first run. A
deterministic whitespace/typography recovery accepted two more; 15 remained
unresolved because their proposed quotations were paraphrases rather than
recoverable formatting variants. There were no strict-schema, entity-reference,
or linearization-type failures after v1.0.3 transport preflight.

## Diagnosis

The WHO methodology was not falsified. The CMACM v1.0.3 domain individuation
rule was underspecified in two critical places.

1. `CausalWorkflow` was allowed to split when exposure or instrument changed.
   In drug-target MR this turned one shared estimation procedure into 11-12
   workflows, depending on whether a run enumerated a target.
2. `CausalLink` was allowed to split at each reported endpoint measurement.
   In the PDAP1 MR/cohort/cell report, two runs produced 30 links while a third
   produced four, despite agreeing on four workflows and design-family set.

These are domain-model errors, not evidence failures. The observed model
outputs establish that procedure, exposure family, normalized outcome domain,
contrast, measurement, and validation need more precise identity boundaries.

## Required Amendment Before New Holdout Test

- Workflow identity: `Study + causal procedure + analysis population/dataset
  context`. A new exposure, instrument, target, endpoint, arm, dose or estimator
  does not create a workflow when the procedure and context are shared.
- Link identity: `Workflow + exposure/intervention family + normalized outcome
  domain + direction + biological system`. Individual reported phenotypes,
  biomarkers and assays are result measurements or contrast axes unless they
  represent different normalized outcome domains.
- Contrast: comparator, arm, dose, timepoint, estimator, adjustment and
  measured endpoint specification.
- Validation: rescue, sensitivity, replication, negative control, challenge or
  orthogonal assay, never a workflow or a link.
- Source evidence: replace free model quotations with deterministic evidence
  atom identifiers for the next test; Python resolves the exact stored text.

The present 15 reports are now a development set for those amendments. A new,
fully disjoint sample must test the revised contract. No PRISMA, eligibility,
or synthesis count changes follow from this diagnostic.
