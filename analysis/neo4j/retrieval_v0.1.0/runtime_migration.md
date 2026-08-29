# Neo4j runtime migration record

Date: 2026-08-30

## Existing runtime

The initial local Docker inspection found an active container named
`nla-docling-neo4j`:

- Neo4j Community `5.26.30` from the floating `neo4j:5.26-community` tag;
- Browser/Bolt bound to localhost ports `7474` and `7687`;
- persistent volume `nla_docling_neo4j_data`;
- content belonging to the separate NLA Docling Graph project.

That container, volume, and graph were left unchanged by this review task. A
later validation observed that another local process had recreated the NLA
container from the floating `neo4j:latest` tag; it then reported Neo4j Community
`2026.07.1`. This external state change did not affect the review container or
its volumes. Reuse would still mix unrelated corpora and make corpus-level
counts ambiguous, while a floating tag would weaken runtime reproducibility.

## Review-specific runtime

The causal multi-omics aging review now uses:

- container `causal-aging-neo4j`;
- Neo4j Community `2026.07.1`;
- exact image
  `neo4j:2026.07.1-community@sha256:dbc377fb9cd8fe8dabc19d3041b197d5ca0ef8bae514cea175b8df265e5b7a76`;
- localhost Browser/Bolt ports `7475` and `7688`;
- versioned volumes `causal_aging_neo4j_data_v0_1_0` and
  `causal_aging_neo4j_logs_v0_1_0`;
- no optional Neo4j plugins.

The exact 2026.07.1 tag was selected from the official
[Neo4j Docker image](https://hub.docker.com/_/neo4j) and
[Neo4j Docker operations documentation](https://neo4j.com/docs/operations-manual/current/docker/introduction/).
The image digest was recorded after pulling the official multi-architecture
manifest on the local ARM64 Docker runtime.

## Load and validation

The deterministic import pack contains the 101 canonical eligible report
graphs selected by
`analysis/article_design/corpus_grounding_v1.0.0/eligible_graph_manifest_101.csv`.
Native Docling Graph IDs are namespaced by report because 57 native IDs recur
across reports, with a maximum multiplicity of 39.

The Cypher load was executed twice. Both executions produced the same database
state, confirming idempotent import for the frozen pack. The compact validation
contains 21 passing checks, including exact counts and hashes, online indexes,
full-text retrieval, provenance presence, unique namespaced IDs, and absence of
cross-document graph edges.

The runtime validation establishes infrastructure integrity. Retrieval recall,
precision, and scientific validity require a separate human-annotated ablation.
