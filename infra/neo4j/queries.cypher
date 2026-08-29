// Causal multi-omics aging review: reproducible retrieval examples.
// The v1 graph connects extracted entities at report level. These queries must
// not be interpreted as proof that every returned entity participates in the
// same causal analysis.

// 1. Corpus integrity.
MATCH (corpus:ReviewCorpus {corpus_id: 'eligible_graphs_101_v1_5_4'})
OPTIONAL MATCH (corpus)-[:CONTAINS_REPORT]->(report:CausalMultiomicsAgingPaper)
RETURN corpus.corpus_fingerprint AS fingerprint, count(report) AS reports;

MATCH (node:ReviewGraphNode {corpus_id: 'eligible_graphs_101_v1_5_4'})
RETURN node.node_label AS node_label, count(*) AS count
ORDER BY count DESC;

// 2. Report-level co-occurrence of an omics layer, aging construct, and causal analysis.
MATCH (report:CausalMultiomicsAgingPaper)-[:USES_OMICS_LAYER]->(omics:OmicsLayer)
MATCH (report)-[:INVESTIGATES_AGING_CONSTRUCT]->(aging:AgingConstruct)
MATCH (report)-[:REPORTS_CAUSAL_ANALYSIS]->(analysis:CausalAnalysis)
WHERE report.corpus_id = 'eligible_graphs_101_v1_5_4'
  AND omics.normalized_layer IN ['epigenomics', 'transcriptomics', 'proteomics']
RETURN DISTINCT report.doi AS doi,
       report.title AS title,
       omics.normalized_layer AS omics_layer,
       aging.reported_name AS aging_construct,
       analysis.design_family AS design_family,
       analysis.method_name AS method,
       analysis.provenance_json AS provenance
ORDER BY doi
LIMIT 100;

// 3. Full-text search over graph node properties and nested evidence text.
CALL db.index.fulltext.queryNodes(
  'review_graph_text',
  '"mendelian randomization" OR perturbation OR mediation'
)
YIELD node, score
WHERE node.corpus_id = 'eligible_graphs_101_v1_5_4'
MATCH (report:CausalMultiomicsAgingPaper)-[]->(node)
RETURN score,
       report.doi AS doi,
       report.title AS title,
       node.node_label AS matched_node_type,
       node.method_name AS method,
       node.target_claim AS target_claim,
       node.evidence_text AS candidate_evidence,
       node.provenance_json AS provenance
ORDER BY score DESC
LIMIT 50;

// 4. Locate all candidates from one report for deterministic evidence-atom resolution.
MATCH (report:CausalMultiomicsAgingPaper {doi: '10.1038/s41467-023-37729-w'})-[relationship]->(candidate)
RETURN type(relationship) AS relationship,
       candidate.node_key AS node_key,
       candidate.node_label AS node_label,
       candidate.search_text AS extracted_text,
       candidate.provenance_json AS provenance
ORDER BY relationship, node_key;

// 5. Inspect design-family distribution. This describes model-extracted candidates.
MATCH (:CausalMultiomicsAgingPaper)-[:REPORTS_CAUSAL_ANALYSIS]->(analysis:CausalAnalysis)
WHERE analysis.corpus_id = 'eligible_graphs_101_v1_5_4'
RETURN analysis.design_family AS design_family, count(*) AS candidates
ORDER BY candidates DESC;
