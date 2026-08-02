# OpenAlex Scope Calibration

## Decision

Springer Nature is excluded from the identification search. Its available Meta
API searches a broad full-text index and returned 11,896 raw matches; only
32/500 pilot records contained all three review concept blocks in title or
abstract. Springer Nature may be used later only for identifier-based full-text
retrieval.

OpenAlex `v1.1.2` is provisionally selected for complete retrieval. It replaces
the invalid 32,273-result pilot with six scoped branches and within-source Work
ID deduplication.

## Ablations

| Version | Controlled change | Gross branch hits | Evaluation sample | Local three-block conformity |
| --- | --- | ---: | ---: | ---: |
| `v1.0.0` | Broad single-layer OR block | 32,273 | 500 | 51/500 (10.2%) |
| `v1.1.0` | Explicit/pairwise branches and formal causal anchors | 3,029 | 234 unique high-signal records | 97/234 (41.5%) |
| `v1.1.1` | Exact aging search instead of stemmed aging search | 1,457 | 244 unique random records | 213/244 (87.3%) |
| `v1.1.2` | Add `metabolite` to pairwise metabolomics vocabulary | 1,600 | 244 unique random records | 217/244 (88.9%) |

The `v1.1.1` and `v1.1.2` random samples use OpenAlex seed `20260802`.
Because changing the query changes the sampling frame, these are reproducible
descriptive samples, not a paired statistical comparison.

Local three-block conformity is a lexical audit, not relevance, eligibility,
precision, or accuracy. It checks whether the reconstructed title/abstract
contains recognized multi-omics, aging, and formal causal-anchor vocabulary.

## Recall Check

The development pool contains 96 assistant-selected INCLUDE/SEEK records with
DOIs, all indexed by OpenAlex; 78 have an OpenAlex abstract. These records are
not expert gold.

| Query | Matched among 78 records with abstracts |
| --- | ---: |
| `v1.1.1` | 74/78 (94.9%) |
| `v1.1.2` | 75/78 (96.2%) |

The added record is a two-stage network Mendelian-randomization study using
GWAS and circulating-metabolite mediators. The `metabolite` addition increased
gross branch occurrences by 143 (9.8%).

## Complete OpenAlex Retrieval

The complete `v1.1.2` retrieval produced:

- 1,600 branch occurrences;
- 419 duplicate branch occurrences removed;
- 1,181 unique OpenAlex Works;
- 1,067/1,181 (90.3%; Wilson 95% CI 88.5%-91.9%) with local lexical
  three-block conformity;
- successful retrieval of DOI `10.1038/s41467-023-37729-w`.

All query files, API responses, normalized records, Git revisions, and SHA-256
hashes are preserved. The 1,181 Works are records identified from OpenAlex, not
included studies.

## Remaining Gate

The query is not yet frozen for final screening. The random branch-quality
sample still requires criterion-level semantic annotation. Until that is
recorded, the complete multi-database corpus and production title/abstract run
remain blocked.
