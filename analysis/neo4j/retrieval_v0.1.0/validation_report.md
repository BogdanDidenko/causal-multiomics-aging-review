# Neo4j retrieval validation v0.1.0

Status: **pass**

- Container: `causal-aging-neo4j`
- Image: `neo4j:2026.07.1-community@sha256:dbc377fb9cd8fe8dabc19d3041b197d5ca0ef8bae514cea175b8df265e5b7a76`
- Corpus fingerprint: `8b58d00219f9499811d15d5bb471e001d4fdcf89fbac35e543f65c3b14befc3b`
- Full-text `aging` smoke-test hits: 450

| Check | Expected | Observed | Passed |
|---|---:|---:|:---:|
| `artifact_sha256:data/neo4j/retrieval_v0.1.0/import/nodes.csv` | `"9571c1002f161d54b3ccf9018f2e6de988e47669aa73cccb65f65ea0677f9414"` | `"9571c1002f161d54b3ccf9018f2e6de988e47669aa73cccb65f65ea0677f9414"` | yes |
| `artifact_sha256:data/neo4j/retrieval_v0.1.0/import/edges.csv` | `"3cf747b8d015f0e830029ad35c9ded6dccb7b5ab8ca6201266dba5bf9211e3bc"` | `"3cf747b8d015f0e830029ad35c9ded6dccb7b5ab8ca6201266dba5bf9211e3bc"` | yes |
| `artifact_sha256:data/neo4j/retrieval_v0.1.0/import/load.cypher` | `"b39a54949b5b5df4ac4e2dc4bc086c2ba1abd794ff596c14b1d7b4f877f02d9e"` | `"b39a54949b5b5df4ac4e2dc4bc086c2ba1abd794ff596c14b1d7b4f877f02d9e"` | yes |
| `artifact_sha256:data/neo4j/retrieval_v0.1.0/import/reset.cypher` | `"39812f611bfd034e13440352e011c8e0ab641d30d34de42a6614b3bfa161f507"` | `"39812f611bfd034e13440352e011c8e0ab641d30d34de42a6614b3bfa161f507"` | yes |
| `artifact_sha256:infra/neo4j/compose.yml` | `"87364b02f484abefe9a83ca1500903d9553c843d20eed6b97137ad75c649279a"` | `"87364b02f484abefe9a83ca1500903d9553c843d20eed6b97137ad75c649279a"` | yes |
| `artifact_sha256:infra/neo4j/queries.cypher` | `"eea222e19caf7b8631cdc224f73d31da302d54ce29ee731da0f1358c66730485"` | `"eea222e19caf7b8631cdc224f73d31da302d54ce29ee731da0f1358c66730485"` | yes |
| `neo4j_version` | `"2026.07.1"` | `"2026.07.1"` | yes |
| `neo4j_edition` | `"community"` | `"community"` | yes |
| `review_graph_nodes` | `1536` | `1536` | yes |
| `review_graph_edges` | `1435` | `1435` | yes |
| `reports` | `101` | `101` | yes |
| `corpus_report_links` | `101` | `101` | yes |
| `missing_provenance` | `0` | `0` | yes |
| `duplicate_namespaced_node_keys` | `0` | `0` | yes |
| `cross_document_graph_edges` | `0` | `0` | yes |
| `online_indexes` | `["review_corpus_id", "review_graph_design_family", "review_graph_doi", "review_graph_node_key", "review_graph_omics_layer", "review_graph_text"]` | `["review_corpus_id", "review_graph_design_family", "review_graph_doi", "review_graph_node_key", "review_graph_omics_layer", "review_graph_text"]` | yes |
| `index_states` | `["ONLINE", "ONLINE", "ONLINE", "ONLINE", "ONLINE", "ONLINE"]` | `["ONLINE", "ONLINE", "ONLINE", "ONLINE", "ONLINE", "ONLINE"]` | yes |
| `fulltext_retrieval_smoke_test` | `">0"` | `450` | yes |
| `node_label_counts` | `{"AgingConstruct": 686, "CausalAnalysis": 312, "CausalMultiomicsAgingPaper": 101, "OmicsLayer": 437}` | `{"AgingConstruct": 686, "CausalAnalysis": 312, "CausalMultiomicsAgingPaper": 101, "OmicsLayer": 437}` | yes |
| `edge_label_counts` | `{"INVESTIGATES_AGING_CONSTRUCT": 686, "REPORTS_CAUSAL_ANALYSIS": 312, "USES_OMICS_LAYER": 437}` | `{"INVESTIGATES_AGING_CONSTRUCT": 686, "REPORTS_CAUSAL_ANALYSIS": 312, "USES_OMICS_LAYER": 437}` | yes |
| `container_image` | `"neo4j:2026.07.1-community@sha256:dbc377fb9cd8fe8dabc19d3041b197d5ca0ef8bae514cea175b8df265e5b7a76"` | `"neo4j:2026.07.1-community@sha256:dbc377fb9cd8fe8dabc19d3041b197d5ca0ef8bae514cea175b8df265e5b7a76"` | yes |

This validates database integrity and retrieval mechanics. It does not
measure scientific recall, precision, or causal-claim validity.
