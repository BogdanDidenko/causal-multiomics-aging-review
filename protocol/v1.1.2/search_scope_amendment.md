# Search Scope Amendment v1.1.2

This amendment supersedes only the identification-source and OpenAlex-query
parts of the v1.0.0 PRISMA pipeline.

1. Active identification sources are PubMed, Scopus, Europe PMC, Semantic
   Scholar, OpenAlex, and manual Google Scholar.
2. Springer Nature is excluded from identification because the available Meta
   API searches a broad full-text index. It may be used for identifier-based
   full-text retrieval after screening.
3. OpenAlex uses one explicit multi-omics branch and five pairwise
   molecular-layer branches. Each branch requires an exact aging construct, a
   formal causal-design anchor, an abstract, article/preprint type, publication
   on or before 2026-08-02, and non-retracted status.
4. OpenAlex branch occurrences are deduplicated by Work ID before
   cross-database deduplication. Both gross branch counts and unique Work counts
   are reported.
5. The superseded OpenAlex count of 32,273 and Springer Nature count of 11,896
   are calibration diagnostics and are excluded from the final PRISMA
   denominator.
6. Search query freeze and full-corpus screening require completion of the
   criterion-level semantic quality audit for the frozen random branch sample.
