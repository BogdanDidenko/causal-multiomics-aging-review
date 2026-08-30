# Neo4j retrieval comparison v0.1.0

Status: **exploratory; no expert retrieval gold standard**

- Frozen eligible corpus: 101 reports
- Shared historical subset: 30 reports
- Corpus fingerprint: `8b58d00219f9499811d15d5bb471e001d4fdcf89fbac35e543f65c3b14befc3b`
- Comparison unit: unique DOI
- References/Bibliography were excluded from the Docling lexical baseline.

## Full 101-report corpus

Method-specific units are graph nodes, regex occurrences, or profile objects and
must not be compared as though they were the same scientific unit.

| Information need | Neo4j structured | Frozen profile | Neo4j graph text | Docling lexical | Active-method union |
|---|---:|---:|---:|---:|---:|
| `assigned_intervention` | 51 | 51 | 37 | 86 | 90 |
| `directed_or_temporal_model` | 8 | 8 | 0 | 3 | 9 |
| `formal_mediation` | 5 | 5 | 17 | 60 | 62 |
| `genetic_instrument` | 14 | 14 | 14 | 16 | 17 |
| `targeted_perturbation` | 66 | 66 | 57 | 81 | 88 |

## Key overlaps

| Information need | Structured vs graph-text Jaccard | Structured vs Docling Jaccard | Graph-text vs Docling Jaccard |
|---|---:|---:|---:|
| `assigned_intervention` | 0.491525 | 0.539326 | 0.413793 |
| `directed_or_temporal_model` | 0.000000 | 0.222222 | 0.000000 |
| `formal_mediation` | 0.222222 | 0.083333 | 0.241935 |
| `genetic_instrument` | 0.866667 | 0.764706 | 0.875000 |
| `targeted_perturbation` | 0.757143 | 0.670455 | 0.682927 |

## Shared 30-report historical subset

| Information need | Neo4j structured | Neo4j graph text | Docling lexical | Rejected legacy LLM candidates |
|---|---:|---:|---:|---:|
| `assigned_intervention` | 14 | 11 | 25 | 23 |
| `directed_or_temporal_model` | 4 | 0 | 3 | 1 |
| `formal_mediation` | 5 | 7 | 18 | 20 |
| `genetic_instrument` | 5 | 6 | 6 | 6 |
| `targeted_perturbation` | 14 | 13 | 23 | 18 |

## Historical candidate burden

Across the same 30 reports, the rejected open+dense LLM discovery produced 2829 frozen candidates. The current graph contains 94 CausalAnalysis nodes for those reports (30.096 legacy candidates per graph node).
These are different candidate definitions, so this quantifies workload rather than recall.

## Frozen-profile equivalence

Neo4j structured Cypher and direct filtering of the same frozen graph profiles returned identical DOI sets for all five information needs.

## Interpretation boundary

Neo4j adds deterministic relationship composition, indexed exploration, and stable
provenance lookup. It does not add new scientific evidence beyond the model-generated
Docling graphs. Graph-text and Docling lexical retrieval are candidate generators;
their unique hits require human-gold assessment before precision or recall can be stated.
No missing hit can support exclusion.
