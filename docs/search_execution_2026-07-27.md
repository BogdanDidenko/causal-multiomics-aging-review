# Search Execution: 2026-07-27

## Frozen identification counts

| Source | Reported | Retrieved | Local three-block QA | Canonical positive |
|---|---:|---:|---:|:---:|
| europepmc | 616 | 616 | 612 | yes |
| google_scholar | 180 | 180 | 131 | yes |
| openalex | 606 | 606 | 268 | yes |
| pubmed | 566 | 566 | 516 | yes |
| scopus | 219 | 219 | 15 | yes |
| semantic_scholar | 1,549 | 1,549 | 663 | yes |
| springernature | 996 | 996 | 92 | yes |

## PRISMA identification

- Automated database/API records: **4,552**.
- Manual supplementary Google Scholar records: **180**.
- Total source records: **4,732**.
- Duplicate instances removed: **1,880**.
- Unique records entering title/abstract screening: **2,852**.
- Unique records without an abstract: **193**; these route to metadata enrichment or manual review.
- Unique records with oversized abstract metadata: **35**; these also route to enrichment or manual review.

The local three-block count is a retrieval-quality diagnostic only. It does not remove records and is not a PRISMA inclusion count.

## Calibration control

DOI `10.1038/s41467-023-37729-w` was retrieved by all seven sources and merged into one canonical record.

## Source limitations

- Google Scholar has no official search API. Its `About 180` count is approximate; 180 displayed records across 18 pages were frozen through a manual browser session.
- The available Scopus API key permits `STANDARD`, not `COMPLETE`, view. Scopus abstracts are therefore absent and are backfilled only when another source supplies them.
- Springer Nature Meta searches full text, so its raw pool is broader than title/abstract databases. Proximity constraints and local QA fields are preserved for audit.
- Semantic Scholar intermittently returned HTTP 500 for long Boolean expressions. The frozen compact three-concept query retained the canonical positive.

Title/abstract screening, full-text retrieval, eligibility, and synthesis counts remain pending and must be appended without rewriting this identification snapshot.
