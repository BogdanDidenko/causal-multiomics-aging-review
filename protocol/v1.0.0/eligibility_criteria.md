# Eligibility Criteria v1.0.0

## Inclusion criteria

| Code | Criterion |
| --- | --- |
| IC1 | Primary empirical biological or health research. |
| IC2 | Aging is analyzed as an outcome, trajectory, mechanism, exposure, mediator, or intervention target. |
| IC3 | At least two distinct molecular omics layers are measured or analytically connected in the current report. |
| IC4 | The current report applies a named causal-effect design, a formal directed/causal-discovery method, or an explicit causal analysis whose method requires full-text verification. |
| IC5 | Sufficient report information is available for full-text causal assessment. |

## Causal evidence levels

| Level | Label | Definition |
| ---: | --- | --- |
| 0 | `context_only` | Ineligible/context report or no verified multi-omics analysis. |
| 1 | `associational` | Association, prediction, enrichment, or causal wording without a formal causal basis. |
| 2 | `causal_hypothesis` | Formal directed/causal-discovery analysis without sufficient effect identification. |
| 3 | `causal_evidence` | Assessable causal contrast with a defined design and assumptions. |
| 4 | `causal_evidence_validated` | Level 3 plus independent validation of the same causal link. |

Levels 2-4 enter synthesis. Level 2 is reported separately from Levels 3-4.

## Exclusion codes

| Code | Meaning |
| --- | --- |
| EC1 | Not primary empirical research. |
| EC2 | Not biological or health research. |
| EC3 | Aging is only demographic, covariate, disease-label, or background context. |
| EC4 | Fewer than two analytically used molecular omics layers. |
| EC5 | Association, prediction, enrichment, causal wording, or an undirected network without a formal causal basis. |
| EC6 | Duplicate report or superseded preprint. |
| EC7 | Full text unavailable or insufficient after documented retrieval attempts. |

## Formal causal bases

Eligible families include genetic instruments; randomized and
quasi-experimental interventions; direct perturbations; identified temporal
designs; formal mediation; DAG/SCM/SEM analyses; Bayesian networks with an
explicit causal interpretation; and named causal-discovery algorithms such as
PC, FCI, GES, LiNGAM, and NOTEARS.

Colocalization alone, feature importance, pathway direction, WGCNA,
co-expression, cell-cell communication, pseudotime, and generic regulatory
network edges do not qualify. Granger, SEM, mediation, and learned directed
graphs remain Level 2 unless their identification assumptions support Level 3.
