# Full-text Routing Amendment v1.5.4-rc1

## Problem

The frozen v1.5.3-rc1 route required all five runs to return the same first
failed criterion. This sent reports to manual review even when all five runs
independently agreed that a different decisive eligibility criterion failed.
The route therefore conflated uncertainty about the exclusion label with
uncertainty about the exclusion decision.

## Amended deterministic rule

A report is excluded when all five valid scope runs independently fail the
same criterion:

- `EC1`: `report_type = nonempirical`;
- `EC2`: `bio_health_scope = no`;
- `EC3`: `aging_process_relevance = no`;
- `EC4`: `multiomics_evidence = single_or_no_layer` or
  `current_report_layer_use = no`.

If more than one criterion is unanimously failed, the earliest criterion in
the prespecified EC1-EC4 order is reported. Disagreement in unrelated fields
is preserved in the audit and does not change the route. Missing runs,
execution failures, and records without a unanimous failed criterion remain
for adjudication.

This is Python-only postprocessing. It does not reinterpret article text,
change prompts, discard raw outputs, or rerun the model. The original
v1.5.3-rc1 ledger remains immutable and is reported as the pre-amendment
result.
