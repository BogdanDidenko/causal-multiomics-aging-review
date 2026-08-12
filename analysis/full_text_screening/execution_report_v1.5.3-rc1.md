# Deterministic Full-Text Screening v1.5.3-rc1

Date completed: 2026-08-12

## Status

This is the only current candidate full-text screening run. It is complete but
remains pending human adjudication and expert-gold validation. Its model outputs
are not final PRISMA eligibility decisions.

All graph-prioritized full-text inputs and outputs are registered as
`legacy_not_for_prisma` in
`data/full_text_screening/legacy_registry.json`.

## Frozen Method

- Corpus: 158 unique reports, including 157 unique DOI values and one DOI-less
  report.
- Full-text conversion: deterministic Docling chunks with stable section IDs.
- Packaging: `deterministic_heading_keyword_v2_no_model_ranking`.
- Model-generated graph priority fields in reviewer input: zero.
- Canonical roles: `scope_reviewer` and `causal_method_reviewer`.
- Model: GPT 5.6 Terra Medium through Codex CLI.
- Repeats: five independent requests per executed role.
- Routing: Python consistency rules; any route disagreement or unresolved
  evidence goes to manual review.

The input, suite, runtime code, raw requests, parsed outputs, retries, evidence
repairs, and result records are preserved with hashes.

## Execution Integrity

- Shards completed: 24/24.
- Result records: 158/158.
- Failed shards: 0.
- Logical call slots: 1,292.
- Slots requiring the one permitted retry: 65.
- Successfully recovered after retry: 62.
- Unresolved after retry: 3; all routed to manual review.
- Raw model attempts: 1,357.
- Successful attempts: 1,289.
- Failed attempts retained in the audit: 68.
- Accepted packages with graph-prioritized chunks: 0.

Most retry failures were caused by evidence quotes that were not exact source
substrings. Deterministic same-chunk quote repair was applied where possible;
unresolved grounding was not silently accepted.

## Model-Pipeline Outcomes

| Route | Reports |
|---|---:|
| Unanimous positive assessment | 100 |
| Unanimous AI exclusion | 33 |
| Manual review | 25 |
| Total | 158 |

The 33 unanimous AI exclusions comprise EC1 22, EC3 9, EC4 1, and EC5 1.
They remain AI-pipeline outcomes until the prespecified human and expert-gold
requirements are satisfied.

Manual-review reasons:

- 21 scope-route disagreement or unresolved scope;
- 1 causal-route disagreement or unresolved causal assessment;
- 3 role executions unresolved after the one-retry policy.

## Stability

- Exact five-request route: 133/158 (84.2%).
- Exact scope agreement across all tracked fields: 109/158 (69.0%).
- Causal reviewer executed for 102 reports.
- Exact causal agreement across all tracked fields: 94/102 (92.2%).
- Exact agreement across all evaluated fields: 101/158 (63.9%).

Route stability is the primary operational measure. Field-level stability is
reported separately and must not be interpreted as scientific validity.

## Authoritative Artifacts

- `data/full_text_screening/current_candidate.json`
- `data/full_text_screening/v1.5.3_deterministic_full_text_158/input_manifest.json`
- `data/full_text_screening/v1.5.3_deterministic_full_text_158/evaluation_v1.5.3-rc1/orchestrator_manifest.json`
- `data/full_text_screening/v1.5.3_deterministic_full_text_158/evaluation_v1.5.3-rc1/stability_summary.json`
- `data/full_text_screening/v1.5.3_deterministic_full_text_158/evaluation_v1.5.3-rc1/stability_ledger.csv`
- `data/full_text_screening/v1.5.3_deterministic_full_text_158/evaluation_v1.5.3-rc1/prisma_full_text_screening.json`
