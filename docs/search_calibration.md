# Search Calibration

## Calibration Anchor

All automated sources were checked against DOI
`10.1038/s41467-023-37729-w`, *Multi-omic underpinnings of epigenetic aging
and human longevity*. The final query retrieves the record in PubMed, Scopus,
Europe PMC, OpenAlex, Springer Nature, and Semantic Scholar.

## Live Probe

Counts were probed on 2026-07-27 before the formal frozen extraction.

| Source | Probe count | Calibration role |
|---|---:|---|
| PubMed | 566 | Primary biomedical recall |
| Scopus | 219 | Title-anchored multidisciplinary precision |
| Europe PMC | 616 | Biomedical and preprint recall |
| Semantic Scholar | 1,549 | Broad supplementary title/abstract recall |
| Springer Nature Meta | 996 | Proximity-constrained publisher full-text index |
| OpenAlex | 606 | Title-anchored supplementary source |
| Google Scholar | About 180 | Title-anchored supplementary manual search |

Counts are not PRISMA denominators until every page is frozen in one execution.
Databases can reindex records without changing the query.

## Decisions

- A two-block `multi-omics AND aging` probe returned 1,539 PubMed, 1,663
  Europe PMC, 2,604 Scopus, 4,176 Semantic Scholar, 6,504 OpenAlex, and over
  40,000 Springer Nature records. It retained the canonical positive but was
  dominated by associational/context records.
- The final third block uses broad design anchors rather than requiring the
  exact phrases `causal inference` or `causal discovery`.
- No lower date limit is imposed. The complete PubMed two-block probe added
  only one pre-2010 record, so an arbitrary 2018 cutoff would not materially
  reduce workload but could remove early eligible work.
- `Age-related disease`, older participants, and chronological age alone are
  not search concepts or eligibility evidence. They require an explicit
  aging-process analysis.
- Springer Nature's free Meta API searches full text. Two proximity constraints
  reduce its raw pool while preserving the canonical positive; local
  title/abstract validation remains mandatory.
- Semantic Scholar's bulk backend returned HTTP 500 for several longer
  equivalent expressions. The frozen compact expression uses the same three
  concepts, retrieved 1,549 records, and retained the canonical positive.
- Google Scholar's broad expression reported about 17,600 opaque full-text
  matches. Adding `intitle:` anchors for multi-omics and aging reduced the
  auditable supplementary pool to about 180 and ranked the canonical positive
  first.
