# Neo4j retrieval disagreement diagnostics v0.1.0

## Status

This is a post-hoc analyst diagnostic of method-disagreement cases found after
the frozen retrieval comparison. It is not a random accuracy sample, an expert
gold standard, or a basis for precision and recall estimates. Its purpose is to
identify failure mechanisms before production causal-analysis extraction.

## Diagnostic cases

| DOI | Information need | Retrieval pattern | Analyst diagnostic | Failure mode or gain |
|---|---|---|---|---|
| `10.1002/imo2.70128` | genetic instrument | Neo4j graph text and Docling lexical; absent from structured family | The current report explicitly lists SMR among its analyses in `chunk:0003`. The graph contains a mediation node but no genetic-instrument node. | Structured graph omission; graph-text retrieval recovers a real candidate. |
| `10.1093/geroni/igac059.2661` | genetic instrument | Neo4j structured only | The extracted node calls a GWAS a `genetic_instrument` and marks it `association_only`; GWAS association alone is not MR/IV identification. The source package also contains unrelated conference abstracts under the same report. | Wrong design-family label plus source-package contamination. |
| `10.3389/fimmu.2026.1718849` | genetic instrument | Docling lexical only | `chunk:0044` mentions limitations of conventional MR while describing another method; the report does not attribute MR to its current analysis. | Contextual lexical false positive. |
| `10.3390/microorganisms13061379` | genetic instrument | Docling lexical only | The match is a cited MR paper embedded in `chunk:0018`, whose heading is `Conclusions` despite containing reference-list material. | Reference leakage caused by imperfect deterministic section boundaries. |
| `10.1093/bib/bbag271` | directed/temporal model | Docling lexical only for this family | `chunk:0009` reports mediation analysis using SEM. The graph captured it under `formal_mediation`, so the evidence exists but the prespecified family mapping differs. | Controlled-vocabulary mapping sensitivity. |
| `10.1186/s40364-023-00458-9` | directed/temporal model | Neo4j structured only | The graph labels Spearman correlation as `other_formal_causal_design` and also marks it `association_only`. | Wrong causal-design label. |
| `10.26599/fshw.2026.9251125` | directed/temporal model | Neo4j structured only | Network pharmacology and molecular docking were labelled `dag_scm`; these methods do not establish a DAG/SCM design. | Wrong causal-design label. |
| `10.1016/j.ymthe.2025.12.035` | formal mediation | Neo4j structured | The labelled analysis is INHBA knockdown plus KAT8 rescue. This supports a mechanistic perturbation claim, but it is not a formal statistical mediation design. | Mechanism/mediation category conflation. |
| `10.2147/jir.s545622` | targeted perturbation | Neo4j structured only across the three active methods | Retinoic-acid treatment is a genuine intervention candidate even though the narrow frozen perturbation lexicon did not retrieve it. | Useful semantic retrieval beyond exact keywords. |
| `10.1002/advs.202514269` | targeted perturbation | Neo4j structured only across the three active methods | The graph retrieves experimental 5-HTP treatment and biological-transfer context. The intervention is relevant, but `direct_perturbation` is broader than the comparison label's genetic/pharmacologic wording. | Useful semantic retrieval plus vocabulary-boundary mismatch. |

The motivating report `10.1038/s41467-023-37729-w` was retrieved by all four
full-corpus methods for the genetic-instrument information need.

## What the disagreement means

Neo4j structured retrieval is much more selective than raw Docling lexical
search, but selectivity comes from model-generated labels that can be wrong or
incomplete. Neo4j graph-text search can recover analyses omitted from typed
nodes, as shown by the SMR case. Docling lexical search remains useful as a
high-sensitivity fallback, but ordinary discussion text and malformed
reference boundaries create obvious false candidates.

The current graph therefore supports candidate prioritization and corpus
navigation. It cannot serve as the final scientific classifier. Production
retrieval should use the union of typed Cypher and graph-text candidates, add a
restricted deterministic Docling fallback for prespecified high-value methods,
and resolve every retained candidate to frozen evidence atoms before codebook
classification. Graph absence must never trigger exclusion.

## Schema implications

The next graph version should represent a `CausalAnalysis` as the hub and link
its exposure, outcome, contrast, omics inputs, variation source, assumptions,
and evidence atoms directly. It should also distinguish at least:

- assigned intervention;
- targeted genetic or pharmacologic perturbation;
- biological transfer;
- formal mediation;
- temporal ordering without identification;
- formal temporal or quasi-experimental identification;
- associational models.

Until those edges and controlled labels are human-validated, report-level
co-occurrence paths remain retrieval hints rather than causal evidence.
