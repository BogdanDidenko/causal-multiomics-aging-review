# Neo4j retrieval runtime

This isolated local runtime imports the 101 canonical eligible Docling Graphs
into Neo4j for Cypher and full-text retrieval. It does not reuse the existing
`nla-docling-neo4j` container, its ports, or its data volume.

## Frozen runtime

- Neo4j Community `2026.07.1`, pinned by image digest;
- Browser: `http://127.0.0.1:7475/browser/`;
- Bolt: `neo4j://127.0.0.1:7688`;
- authentication disabled because both ports bind only to localhost;
- corpus-specific persistent data and log volumes.

## Build and load

```bash
.venv/bin/python scripts/neo4j/build_import_pack.py
docker compose -f infra/neo4j/compose.yml up -d
docker compose -f infra/neo4j/compose.yml exec -T neo4j \
  cypher-shell --format plain -f /import/load.cypher
.venv/bin/python scripts/neo4j/validate_runtime.py
```

The generated `nodes.csv` contains graph-extracted article evidence and remains
ignored under `data/neo4j/`. The compact import manifest, source graph hashes,
counts, and validation report are versioned under
`analysis/neo4j/retrieval_v0.1.0/`.

Run the reproducible exploratory queries:

```bash
docker compose -f infra/neo4j/compose.yml exec -T neo4j \
  cypher-shell --format plain < infra/neo4j/queries.cypher
```

To remove only this imported corpus while preserving the database schema:

```bash
docker compose -f infra/neo4j/compose.yml exec -T neo4j \
  cypher-shell --format plain -f /import/reset.cypher
```

## Interpretation boundary

The v1 Docling Graph has report-to-entity relationships. A Cypher match joining
an omics layer, aging construct, and causal analysis through the same report is
report-level co-occurrence. It does not establish that those nodes belong to one
causal design instance.

Graph hits generate candidates for deterministic evidence-atom resolution.
Graph misses cannot justify exclusion. Scientific retrieval performance remains
unmeasured until a text-only versus graph versus hybrid ablation is evaluated
against human-annotated causal claims.
