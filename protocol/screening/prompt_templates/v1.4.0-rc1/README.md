# Canonical Evidence-Mode Prompt Templates

These two templates preserve the calibrated `v1.4.0-rc1` criterion contracts:

- `scope_reviewer.txt`
- `causal_method_reviewer.txt`

Only evidence-mode wording is parameterized. Criterion definitions, allowed
values, precedence rules, layer inventory rules, causal-basis rules,
design-family ordering, and output fields are not template variables.

Evidence profiles:

- `../../evidence_profiles/v1.4.0-rc1/title_abstract.json` contains the frozen
  values used in the completed abstract screen. Its rendered prompts must be
  byte-identical to `prompts/title_abstract/v1.4.0-rc1/`.
- `../../evidence_profiles/v1.4.0-rc1/full_text_sections.json` supplies
  full-text evidence wording and a `{{SELECTED_SECTIONS}}` runtime placeholder.

For full text, deterministic Docling chunks are the evidence-bearing text.
Their stable `section_id` values provide citation traceability. The frozen
Docling graph may prioritize or index chunks, but graph relations do not count
as scientific evidence and cannot satisfy a criterion by themselves.
