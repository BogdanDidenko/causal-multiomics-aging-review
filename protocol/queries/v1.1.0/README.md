# Search Query Pack v1.1.0

This version changes source scope without altering the frozen `v1.0.0` pilot.

- Springer Nature is excluded from identification because its available Meta
  API searches a broad full-text index. It may still be used for identifier-
  based full-text retrieval.
- OpenAlex is split into one explicit multi-omics branch and five pairwise
  molecular-layer branches. Results are deduplicated by OpenAlex Work ID before
  cross-database deduplication.
- Every OpenAlex branch requires an abstract, an aging-process term, and a
  formal causal-design anchor in title or abstract.
- Bare `causal`, `intervention`, `mediation`, and `perturbation` are not used.
  More specific phrases and named designs preserve the prespecified design
  families while reducing generic biomedical matches.

The PubMed, Scopus, Europe PMC, Semantic Scholar, and manual Google Scholar
queries are unchanged from `v1.0.0` pending their separate quality review.

`v1.1.0` remains a calibration query pack. Branch counts and candidate recall
must be reviewed before a complete retrieval is frozen.
