# Full-text shared-template stability evaluation v1.5.0-rc1

## Purpose

This evaluation reapplied the frozen `v1.4.0-rc1` title/abstract criterion
contracts to full-text evidence by rendering the same canonical templates with
the `full_text_sections` evidence profile. It evaluates repeated-request
stability, not expert-gold accuracy.

## Frozen inputs and runtime

- Records: 97 unique-DOI reports.
- Input manifest: `data/full_text_screening/v1.0.0_graph_chunks_97/input_manifest.json`.
- Evidence: deterministic Docling chunks with stable `section_id` values.
- Frozen graph: used only to prioritize/index chunks (`graph_priority_score=200`).
- Evidence package: maximum 60,000 characters, maximum 12,000 per section.
- Model: GPT 5.6 Terra Medium through Codex CLI.
- Reasoning effort: medium.
- Requests: five independent requests per evaluated role.
- Automatic routing: exact agreement on every configured decision field;
  disagreement or unresolved evidence routes to manual review.

The earlier full-text evaluation used separate compound full-text prompts and
produced only 3/97 strict unanimous assessments. That result is retained as an
instrument-development comparison and is not directly pooled with this run.

## Primary run

The primary run completed all 24 shards and all 97 records without a failed
shard.

- Strict positive assessment: 69.
- Strict manual review: 28.
- Strict automatic exclusion: 0.
- Five-request route exactness: 94/97 (96.9%).
- Exact agreement across all evaluated fields: 69/97 (71.1%; Wilson 95% CI
  61.4%-79.2%).
- Model attempt log rows: 916, including retries.
- Failed attempts before retry/manual routing: 36.

Two manual-review records were caused by deterministic quote-grounding failure
around Docling inline markdown and line breaks, rather than criterion
disagreement. The prompt text, model, evidence package, schemas, and routing
contracts were unchanged for their technical retry. A deterministic normalizer
was added to map a near-verbatim quote through Docling `*...*`, soft-hyphen,
and line-wrap artifacts back to an exact contiguous source span.

## After technical grounding retry

Both affected records completed with exact 5/5 agreement on every scope and
causal field:

- `10.1007/s11306-023-02022-w`
- `10.1016/j.celrep.2024.115099`

Reconciled stability counts are:

- Strict positive assessment: 71/97.
- Strict manual review: 26/97.
- Strict automatic exclusion: 0/97.
- Five-request eligibility-route exactness: 96/97 (99.0%; Wilson 95% CI
  94.4%-99.8%).
- Exact agreement across all tracked fields: 71/97 (73.2%; Wilson 95% CI
  63.6%-81.0%).

These reconciled counts keep the original run and retry logs separate. They do
not erase the primary execution history.

## Field-level stability

After the technical retry:

| Role / field | Exact records | Rate |
|---|---:|---:|
| Scope: report type | 97/97 | 100% |
| Scope: biological/health scope | 97/97 | 100% |
| Scope: aging-process relevance | 97/97 | 100% |
| Scope: current-report layer use | 97/97 | 100% |
| Scope: multi-omics evidence class | 95/97 | 97.9% |
| Scope: exact layer inventory | 84/97 | 86.6% |
| Causal: current-report application | 82/82 | 100% |
| Causal: causal basis | 82/82 | 100% |
| Causal: information sufficiency | 82/82 | 100% |
| Causal: routing design family | 71/82 | 86.6% |

The 26 strict-manual records comprise 15 scope-detail disagreements and 11
design-family disagreements. Twenty-five of these 26 records nevertheless had
the same eligibility route in all five requests. The design-family conflicts
were consistently between `randomized_intervention` and
`direct_perturbation` in randomized animal perturbation experiments. They did
not alter `causal_basis` or the positive eligibility route.

One record had genuine route instability:

- `10.1002/ccs3.70045`: three requests classified current evidence as one
  transcriptomics layer, while two treated the phrase "supported by
  multi-omics evidence" as an explicit current-report multi-omics claim. The
  full text also states that only transcriptomics and PPI analysis were used,
  so this record requires human adjudication and is a useful future boundary
  case. It must not be used to tune a prompt and then be reported as an
  independent test case.

## Interpretation

The shared-template approach localized the decision task substantially better
than the rejected compound full-text prompts. Eligibility routing is highly
stable, while exact taxonomy extraction remains less stable. The result does
not establish scientific validity: expert criterion-level adjudication is
still required before final PRISMA inclusion/exclusion counts or causal
evidence levels are assigned.

## Audit artifacts

- Primary run: `data/full_text_screening/v1.0.0_graph_chunks_97/evaluation_v1.5.0-rc1_shared_templates/`
- Stability summary: `stability_summary.json` under the primary run.
- Per-record ledger: `stability_ledger.csv` under the primary run.
- Primary PRISMA draft: `prisma_full_text_screening.json` under the primary run.
- Technical retry: `data/full_text_screening/v1.0.0_graph_chunks_97/evaluation_v1.5.0-rc1_grounding_retry/`
