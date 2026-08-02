# Search Execution: 2026-08-02, Protocol v1.1.2

## Frozen identification counts

| Source | Reported | Retrieved for PRISMA | Local three-block QA | Canonical positive |
|---|---:|---:|---:|:---:|
| PubMed | 2,133 | 2,133 | 1,823 | yes |
| Europe PMC | 1,651 | 1,651 | 1,608 | yes |
| Scopus | 3,889 | 3,889 | 19 | yes |
| Semantic Scholar | 3,494 | 3,494 | 1,221 | yes |
| OpenAlex | 1,600 branch hits | 1,181 unique Works | 1,067 | yes |
| Google Scholar | about 180 | 180 | 131 | yes |

Springer Nature is excluded from this identification run. Its Meta API full-text
search could not express the calibrated scope with acceptable precision. The old
Springer pilot remains available as superseded audit history but does not enter the
final PRISMA denominator.

The local three-block count is a retrieval-quality diagnostic only. It does not
remove records and is not an inclusion or exclusion count.

## PRISMA identification

- Records from five automated databases/APIs: **12,348**.
- Supplementary manual Google Scholar records: **180**.
- Total source records before cross-database deduplication: **12,528**.
- Duplicate instances removed: **4,670**.
- Unique records entering the screening workflow: **7,858**.
- Records with an abstract: **5,022**.
- Records without an abstract: **2,836**; these route to metadata enrichment,
  full-text retrieval, or manual review and are not excluded.
- Abstract records over the 5,000-character title/abstract boundary: **397**;
  these route directly to `seek_full_text` to prevent full-text leakage.

## DOI and identity audit

- Canonical records with a DOI: **7,580**.
- Unique normalized DOI values: **7,580**.
- Duplicate normalized DOI values: **0**.
- Canonical records without a DOI: **278**.
- Abstract records with a DOI: **4,913**, all unique.
- Abstract records without a DOI: **109**; stable SHA-based record IDs are used.
- Duplicate normalized title-year clusters after DOI-first deduplication: **0**.

The control paper `10.1038/s41467-023-37729-w` was retrieved by all six retained
sources and merged into one canonical record.

## Execution details

- Automated database search completion date: **2026-08-02**.
- Google Scholar supplementary capture: **2026-07-26 UTC**, 18 manually frozen
  pages. The date difference is retained explicitly in the audit manifest.
- PubMed completed with HTTP/1.1 and `retmax=20`. Earlier `retmax=200` and
  `retmax=50` runs encountered partial HTTP 200 XML transfers and are retained as
  failed transport attempts, not counted as separate searches.
- Scopus used the licensed `STANDARD` response view. The available entitlement did
  not return abstracts, which accounts for much of the missing-abstract queue.
- OpenAlex used six scoped query branches. The branch counts totalled 1,600; 419
  repeated branch hits were removed before its 1,181 unique Works entered PRISMA.

## Frozen artifacts

- Search manifest: `data/searches/final/2026-08-02-v1.1.2-composite/search_run_manifest.json`
- Machine-readable PRISMA log: `data/searches/final/2026-08-02-v1.1.2-composite/prisma_identification.json`
- Combined source records: `data/searches/final/2026-08-02-v1.1.2-composite/normalized/all_sources.csv`
- Canonical corpus: `data/normalized/v1.1.2/canonical_all_sources.csv`
- Deduplication log: `data/normalized/v1.1.2/deduplication_log.csv`
- Screening input manifest: `data/screening/v1.1.2_full_corpus/input_manifest.json`

The 2026-07-27 search snapshot is a superseded pilot and must not be combined with
these counts.
