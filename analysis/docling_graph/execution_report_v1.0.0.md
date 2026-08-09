# Docling Graph execution report v1.0.0

Date: 2026-08-09  
Model: GPT 5.6 Luna Light (`gpt-5.6-luna`, reasoning effort `low`)  
Docling Graph: 1.9.1

## Corpus flow

| Processing node | Reports |
|---|---:|
| Retrieval candidates presented to deterministic conversion | 98 |
| Canonical Docling conversions | 97 |
| Insufficient full text after conversion QA | 1 |
| Luna Light graphs built | 97 |
| Graph extraction failures | 0 |

The insufficient record is `10.1186/s13578-026-01594-z`. Its archived HTML
contains metadata and an access shell but no article body. It was not submitted
to the model. The active PRISMA subflow is therefore 113 reports sought, 97
sufficient for assessment, and 16 not retrieved or insufficient.

## Runtime

- Python 3.14.0
- Codex CLI 0.145.0
- Docling 2.118.1
- Docling Core 2.91.0
- Docling Graph 1.9.1
- LiteLLM 1.95.0
- PDF OCR disabled; accurate table parsing enabled
- direct whole-document extraction with deterministic dense fallback only on
  an explicit context-overflow error
- up to six non-overlapping execution shards; sharding changed scheduling only
- one retry allowed; no graph required a terminal failure route

The schema/runtime ablation that preceded the complete run is recorded in
[`schema_ablation_v1.0.0.md`](schema_ablation_v1.0.0.md).

## Graph quality

The 97 graphs contain 1,475 nodes. All 1,475 nodes are grounded by Docling
provenance; unresolved nodes are zero. Every graph and provenance hash in the
run ledger matches its local artifact.

The model supplied 2,286 candidate evidence quotes. Of these, 1,370 (59.9%)
are exact substrings of canonical Markdown and 1,799 (78.7%) match after
Unicode, whitespace, HTML-entity, and Markdown-emphasis normalization. The
remaining differences show why model quote strings are not accepted as final
citations. Decisive screening evidence must be resolved to deterministic
Docling chunks or source section IDs.

Twelve reports were independently extracted a second time. All 12/12 had an
identical complete `graph.json` SHA-256. Exact agreement was also 12/12 for
omics layers, omics layer types, causal methods, causal family/status pairs,
and aging constructs (mean Jaccard 1.0 for every dimension). This is a graph
preprocessing stability audit, not a substitute for repeated downstream
eligibility decisions.

The control article `10.1038/s41467-023-37729-w` produced 22 nodes: one paper,
11 aging constructs, five omics layers, and five causal analyses. The graph
separated identified Mendelian-randomization analyses from a hypothesis-only
TWAS/FOCUS analysis.

## Interpretation

This run completed evidence indexing, not full-text eligibility screening. A
missing graph entity cannot cause exclusion, and model-derived root metadata
is not used for routing. Stability testing applies to the downstream
criterion-level reviewers operating on the frozen source chunks and graph
candidates. Repeating graph extraction is not required for a decision because
the graph itself makes no decision.

Machine-readable outputs are in
[`data/full_text_graph/v1.0.0_luna_light`](../../data/full_text_graph/v1.0.0_luna_light/):
`run_summary.json`, `graph_quality_summary.json`, `graph_quality.csv`, and
`prisma_full_text_processing.json`. Repeat results are in
`graph_repeat_stability_summary.json` and `graph_repeat_stability.csv`.
