# Corpus-grounded article-structure exploration v1.0.0

## Purpose

This pack supports bottom-up exploration of the 101 reports that met frozen
full-text eligibility. It was created because comparator-review analysis alone
produced an article outline that was methodologically coherent but insufficiently
grounded in the actual composition of the corpus.

The pack does not perform causal evidence extraction and does not change
eligibility or PRISMA counts.

## Inputs

- Final eligibility ledger:
  `analysis/full_text_screening/final_eligibility_v1.5.4/final_eligibility_ledger_158.csv`.
- Docling Graph roots:
  - `data/full_text_graph/v1.0.0_luna_light`;
  - `data/full_text_graph/v1.1.0_oversized_20k_seek65_luna_light`;
  - `data/full_text_graph/v1.2.0_agent_recovery17_luna_light`.

All 101 eligible DOI records have at least one successful graph. Eleven have
multiple successful graph candidates from repeated or recovery processing. The
builder deterministically selects the earliest successful production graph for
each DOI.

Corpus fingerprint:
`0443b521ba173aea29c71ba6040a3b7c70f80315f28fadeb1a68c06407244749`.

## Outputs

- `eligible_graph_manifest_101.csv`: one row per eligible report with canonical
  graph, deterministic Docling Markdown, and source paths.
- `eligible_graph_profiles_101.jsonl`: compact graph-derived profiles retaining
  evidence anchors, aging constructs, omics layers, and causal-analysis
  candidates.
- `corpus_graph_summary.json`: aggregate node counts and graph-label
  distributions.

The pack is rebuilt by:

```bash
python3 scripts/build_article_structure_corpus_pack.py
```

## Methodological boundary

Docling Graph used Luna Light to create an evidence index. Its nodes and labels
are model-generated candidates, not gold data. In particular:

- `identification_status=identified` is not a final causal judgment;
- a missing graph node is not evidence that a concept is absent;
- graph counts cannot be reported as review findings without claim-level
  verification;
- graph-derived section ranking was not used for final eligibility;
- the pack is not allowed to alter PRISMA dispositions or Levels 0-4.

For article design, graph profiles may be used to quantify apparent corpus
patterns and select representative reports. Every substantive interpretation
must then be checked against the linked deterministic full-text Markdown.

## Independent corpus analyses

Four subagents independently analyzed all 101 graph profiles and each checked a
stratified subset of 35-40 deterministic full texts. Their reports are retained
under `agent_reports/` as auditable inputs to article-structure synthesis:

- `study_archetypes.md`: report-level empirical workflows;
- `causal_design_audit.md`: causal claims and inferential boundaries;
- `aging_narrative.md`: aging constructs, scales, and biological storyline;
- `multiomics_integration.md`: how molecular layers enter the analysis.
- `structure_synthesis.md`: synthesis of the four audits and comparator-review
  analyses into a five-question Results architecture.

`agent_manifest.json` records the assignment and corpus fingerprint. These are
exploratory analyses, not independent eligibility decisions or validated
claim-level extraction.

## Initial orientation signal

The graph index contains 312 causal-analysis candidates. Its raw labels are
dominated by direct perturbation (181) and non-randomized intervention (59),
with 33 genetic-instrument and 24 randomized-intervention candidates. This is a
reason to reassess the earlier top-down article architecture, not a final result:
the graph may overcall mechanistic experiments as identified causal effects.
