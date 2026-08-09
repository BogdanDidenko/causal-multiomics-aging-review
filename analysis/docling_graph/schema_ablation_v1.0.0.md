# Docling Graph schema ablation v1.0.0

Date: 2026-08-09

## Objective

Test whether a fully entity-normalized causal evidence schema is operationally
appropriate for whole-report extraction with GPT 5.6 Luna Light.

## Fixed input

- DOI: `10.1001/jamapsychiatry.2024.1429`
- source format: XML
- converted full text: 68,512 characters
- Docling chunks: 32
- model: `gpt-5.6-luna`
- reasoning effort: `low`
- Docling Graph: 1.9.1
- initial contract: dense
- skeleton batch budget: 3,072 tokens

## Observed result

The first skeleton pass required six model calls and took 4 minutes 17
seconds. It produced approximately 40 candidate nodes because assumptions,
diagnostics, sensitivity analyses, and validations were each represented as
independent graph entities. Nineteen zero-yield chunks containing 61% of source
tokens then triggered four additional coverage batches. The run was stopped
before fill extraction because this granularity would not scale to 98 reports.

## Prespecified correction

The evidence meaning is retained, but assumptions, diagnostics, sensitivity
analyses, and validations are nested components of a causal-analysis entity.
The extraction contract becomes `auto`: use direct whole-document extraction
when the serialized report fits the declared context and dense extraction only
for longer reports. Dense fallback uses 6,144-token skeleton batches and an
eight-entity fill cap.

An immediate auto-contract probe exposed a second independent issue: LiteLLM
reported a 128,000-token output budget for the unregistered Luna model, equal
to its inferred context window. That made direct extraction mathematically
impossible even for a 15,433-token report. The active config therefore pins a
128,000-token context and an 8,000-token extraction output cap, and uses direct
whole-document extraction. A deterministic dense fallback is allowed only for
an explicit context-overflow error. Gleaning and sparse-output fallback are
disabled because an empty evidence list can be a valid extraction and a second
uncontrolled pass would add cost and another source of variation. These values
are runtime budgeting controls; Codex CLI remains the authenticated model
surface.

This is a schema/runtime ablation, not prompt tuning against an eligibility
label. No screening decision or gold label from the paper was used.
