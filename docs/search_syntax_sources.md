# Search Syntax Sources

The database-native queries were calibrated against current official
documentation and frozen on 2026-07-27.

| Source | Official syntax/API reference | Applied behavior |
|---|---|---|
| PubMed | [PubMed Help](https://pubmed.ncbi.nlm.nih.gov/help/) | `[tiab]`, `[Mesh]`, `[pt]`, Boolean nesting, wildcards, and `[pdat]`. |
| Europe PMC | [REST service](https://europepmc.org/RestfulWebService) and [web-service reference](https://europepmc.org/docs/EBI_Europe_PMC_Web_Service_Reference.pdf) | `TITLE:`, `ABSTRACT:`, Boolean nesting, wildcards, and `FIRST_PDATE`. |
| Scopus | [Scopus Search API](https://dev.elsevier.com/documentation/SCOPUSSearchAPI.wadl) | `TITLE`, `TITLE-ABS-KEY`, Boolean nesting, wildcards, and `PUBYEAR`. |
| Semantic Scholar | [Academic Graph API](https://api.semanticscholar.org/api-docs/graph) | Bulk search `+` (AND), `|` (OR), phrases, continuation tokens, and deterministic pagination. |
| Springer Nature | [Boolean and proximity queries](https://dev.springernature.com/docs/advanced-querying/complex-queries-boolean-ops/) | Boolean nesting, `NEAR/N`, and date constraints in the Meta v2 query. |
| OpenAlex | [Works filters](https://developers.openalex.org/api-reference/works) and [filter logic](https://developers.openalex.org/guides/filtering) | Comma-separated AND filters, pipe-separated OR values, date/type filters, and cursor pagination. |
| Google Scholar | [Google Scholar Search Help](https://scholar.google.com/intl/us/scholar/help.html) | Manual title-anchored supplementary search with an end-year filter. |

## Frozen-query notes

- Every source implements the same three concepts: multi-omics, an explicit
  aging process, and a broad causal-design anchor.
- Field syntax is not mechanically copied between sources. The exact executed
  strings are stored under `protocol/queries/`.
- Semantic Scholar's relevance endpoint does not support Boolean syntax; the
  collector therefore uses its documented bulk endpoint.
- OpenAlex currently marks field-specific `.search` filters as deprecated in
  favor of general search. They remained accepted on the execution date and
  were retained because the general search parameter cannot reproduce the
  title-only multi-omics precision constraint. Future updates must create a new
  protocol/search version rather than modifying this frozen run.
- Google Scholar exposes neither an official search API nor an exact stable
  result count. Its export is supplementary and records both the approximate
  reported count and every displayed result page.
