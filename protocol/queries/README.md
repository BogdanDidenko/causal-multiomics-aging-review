# Database Query Pack

Each file contains the one frozen query used for that source. Syntax differs
because field names, Boolean operators, phrase handling, wildcards,
proximity, and pagination are database-specific.

Official syntax references and source-specific limitations are recorded in
[`docs/search_syntax_sources.md`](../../docs/search_syntax_sources.md).

The semantic contract is constant:

`MULTI-OMICS AND AGING PROCESS AND BROAD CAUSAL-DESIGN ANCHOR`

The causal block intentionally goes beyond `causal inference` and `causal
discovery`. It includes genetic instruments, mediation, interventions,
perturbations, quasi-experiments, temporal designs, and directed models.

Source-specific choices:

- PubMed and Europe PMC search title/abstract plus established indexing.
- Scopus and OpenAlex require multi-omics in the title for precision.
- Semantic Scholar uses its Boolean bulk endpoint and local validation.
- Springer Nature uses `NEAR` because the accessible Meta API searches full
  text and does not provide free title-only search.
- Google Scholar uses a shortened manual expression because it has no official
  API and limited Boolean support.
