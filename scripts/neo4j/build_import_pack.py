#!/usr/bin/env python3
"""Build a deterministic Neo4j/Cypher import pack from canonical Docling graphs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "protocol/neo4j/retrieval_v0.1.0.json"
COMPOSE_PATH = REPO / "infra/neo4j/compose.yml"
QUERIES_PATH = REPO / "infra/neo4j/queries.cypher"
IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

NODE_FIELDS = (
    "title",
    "report_type",
    "biological_or_health_scope",
    "full_text_sufficient",
    "reported_name",
    "role",
    "normalized_layer",
    "assay_or_data_source",
    "cohort_or_system",
    "origin",
    "analytic_role",
    "method_name",
    "design_family",
    "design_role",
    "identification_status",
    "target_claim",
    "population_or_model",
    "exposure_or_intervention",
    "comparator",
    "outcome",
    "time_horizon",
    "estimand_or_contrast",
)

CSV_NODE_FIELDS = (
    "corpus_id",
    "node_key",
    "record_id",
    "doi",
    "document_title",
    "native_node_id",
    "node_label",
    "graph_node_type",
    *NODE_FIELDS,
    "evidence_text",
    "evidence_section_heading",
    "search_text",
    "properties_json",
    "provenance_json",
    "source_graph_path",
    "source_graph_sha256",
    "docling_markdown_path",
    "source_path",
)

CSV_EDGE_FIELDS = (
    "corpus_id",
    "edge_key",
    "record_id",
    "doi",
    "source_key",
    "target_key",
    "edge_label",
    "native_source_id",
    "native_target_id",
    "source_graph_sha256",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, fields: Iterable[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    field_list = list(fields)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_list, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in field_list})


def source_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        text = " ".join(value.split())
        if text:
            yield text
    elif isinstance(value, list):
        for item in value:
            yield from source_strings(item)
    elif isinstance(value, dict):
        for key in sorted(value):
            yield from source_strings(value[key])


def deduplicated_text(values: Iterable[str]) -> str:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = " ".join(value.split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            output.append(normalized)
    return "\n".join(output)


def validate_identifier(value: str, *, kind: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Invalid Neo4j {kind}: {value!r}")
    return value


def cypher_string(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def node_key(record_id: str, native_node_id: str) -> str:
    return f"{record_id}|{native_node_id}"


def edge_key(record_id: str, source: str, target: str, label: str) -> str:
    payload = canonical_json([record_id, source, target, label]).encode("utf-8")
    return "edge_" + sha256_bytes(payload)[:24]


def node_row(
    *,
    corpus_id: str,
    manifest_row: dict[str, str],
    graph_sha256: str,
    node: dict[str, Any],
) -> dict[str, Any]:
    evidence = node.get("evidence") if isinstance(node.get("evidence"), dict) else {}
    searchable = {
        key: value
        for key, value in node.items()
        if key not in {"id", "label", "type", "__class__", "__provenance__"}
    }
    strings = [manifest_row["doi"], manifest_row["title"], str(node.get("label", ""))]
    strings.extend(source_strings(searchable))
    row: dict[str, Any] = {
        "corpus_id": corpus_id,
        "node_key": node_key(manifest_row["record_id"], str(node["id"])),
        "record_id": manifest_row["record_id"],
        "doi": manifest_row["doi"],
        "document_title": manifest_row["title"],
        "native_node_id": node["id"],
        "node_label": node["label"],
        "graph_node_type": node.get("type", ""),
        "evidence_text": evidence.get("quote", ""),
        "evidence_section_heading": evidence.get("section_heading", ""),
        "search_text": deduplicated_text(strings),
        "properties_json": canonical_json(
            {key: value for key, value in node.items() if key != "__provenance__"}
        ),
        "provenance_json": canonical_json(node.get("__provenance__", {})),
        "source_graph_path": manifest_row["graph_path"],
        "source_graph_sha256": graph_sha256,
        "docling_markdown_path": manifest_row["docling_markdown_path"],
        "source_path": manifest_row["source_path"],
    }
    for field in NODE_FIELDS:
        value = node.get(field, "")
        row[field] = value if isinstance(value, (str, int, float, bool)) else ""
    return row


def property_assignments() -> str:
    fields = [
        field
        for field in CSV_NODE_FIELDS
        if field not in {"node_key", "node_label"}
    ]
    return ",\n    ".join(f"node.{field} = row.{field}" for field in fields)


def build_load_cypher(
    *,
    corpus_id: str,
    corpus_fingerprint: str,
    node_labels: list[str],
    edge_labels: list[str],
    reports: int,
    graph_nodes: int,
    graph_edges: int,
) -> str:
    corpus = cypher_string(corpus_id)
    lines = [
        "// Generated deterministic import for the causal multi-omics aging review.",
        "// Re-running this file is idempotent for the frozen corpus.",
        "",
        "CREATE CONSTRAINT review_graph_node_key IF NOT EXISTS",
        "FOR (node:ReviewGraphNode) REQUIRE node.node_key IS UNIQUE;",
        "",
        "CREATE CONSTRAINT review_corpus_id IF NOT EXISTS",
        "FOR (corpus:ReviewCorpus) REQUIRE corpus.corpus_id IS UNIQUE;",
        "",
        "CREATE RANGE INDEX review_graph_doi IF NOT EXISTS",
        "FOR (node:ReviewGraphNode) ON (node.doi);",
        "",
        "CREATE RANGE INDEX review_graph_design_family IF NOT EXISTS",
        "FOR (node:CausalAnalysis) ON (node.design_family);",
        "",
        "CREATE RANGE INDEX review_graph_omics_layer IF NOT EXISTS",
        "FOR (node:OmicsLayer) ON (node.normalized_layer);",
        "",
        "CREATE FULLTEXT INDEX review_graph_text IF NOT EXISTS",
        "FOR (node:ReviewGraphNode) ON EACH [node.search_text];",
        "",
    ]
    assignments = property_assignments()
    for label in node_labels:
        validate_identifier(label, kind="node label")
        lines.extend(
            [
                f"// Import node label {label}.",
                "LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row",
                f"WITH row WHERE row.node_label = {cypher_string(label)}",
                f"MERGE (node:ReviewGraphNode:`{label}` {{node_key: row.node_key}})",
                f"SET node.node_label = row.node_label,\n    {assignments};",
                "",
            ]
        )
    for label in edge_labels:
        validate_identifier(label, kind="relationship type")
        lines.extend(
            [
                f"// Import relationship type {label}.",
                "LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row",
                f"WITH row WHERE row.edge_label = {cypher_string(label)}",
                "MATCH (source:ReviewGraphNode {node_key: row.source_key})",
                "MATCH (target:ReviewGraphNode {node_key: row.target_key})",
                f"MERGE (source)-[relationship:`{label}` {{edge_key: row.edge_key}}]->(target)",
                "SET relationship.corpus_id = row.corpus_id,",
                "    relationship.record_id = row.record_id,",
                "    relationship.doi = row.doi,",
                "    relationship.native_source_id = row.native_source_id,",
                "    relationship.native_target_id = row.native_target_id,",
                "    relationship.source_graph_sha256 = row.source_graph_sha256;",
                "",
            ]
        )
    lines.extend(
        [
            f"MERGE (corpus:ReviewCorpus {{corpus_id: {corpus}}})",
            f"SET corpus.corpus_fingerprint = {cypher_string(corpus_fingerprint)},",
            f"    corpus.expected_reports = {reports},",
            f"    corpus.expected_graph_nodes = {graph_nodes},",
            f"    corpus.expected_graph_edges = {graph_edges},",
            "    corpus.graph_absence_can_exclude = false,",
            "    corpus.relationship_scope = 'report_level_cooccurrence';",
            "",
            f"MATCH (corpus:ReviewCorpus {{corpus_id: {corpus}}})",
            f"MATCH (report:ReviewGraphNode:CausalMultiomicsAgingPaper {{corpus_id: {corpus}}})",
            "MERGE (corpus)-[:CONTAINS_REPORT]->(report);",
            "",
            "CALL db.awaitIndexes(300);",
            "",
        ]
    )
    return "\n".join(lines)


def build_reset_cypher(corpus_id: str) -> str:
    corpus = cypher_string(corpus_id)
    return "\n".join(
        [
            "// Delete only this review corpus and its imported occurrence nodes.",
            f"MATCH (corpus:ReviewCorpus {{corpus_id: {corpus}}}) DETACH DELETE corpus;",
            f"MATCH (node:ReviewGraphNode {{corpus_id: {corpus}}}) DETACH DELETE node;",
            "",
        ]
    )


def build(config_path: Path) -> dict[str, Any]:
    config = read_json(config_path)
    source_manifest = REPO / config["source_manifest"]
    with source_manifest.open(encoding="utf-8", newline="") as handle:
        manifest_rows = list(csv.DictReader(handle))
    if len(manifest_rows) != config["expected"]["reports"]:
        raise ValueError(
            f"Expected {config['expected']['reports']} reports, got {len(manifest_rows)}"
        )
    if len({row["record_id"] for row in manifest_rows}) != len(manifest_rows):
        raise ValueError("Source manifest has duplicate record_id values")
    if len({row["doi"].lower() for row in manifest_rows}) != len(manifest_rows):
        raise ValueError("Source manifest has duplicate DOI values")

    allowed_node_labels = set(config["allowed_node_labels"])
    allowed_edge_labels = set(config["allowed_edge_labels"])
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    graph_inventory: list[dict[str, Any]] = []
    node_label_counts: Counter[str] = Counter()
    edge_label_counts: Counter[str] = Counter()
    native_id_counts: Counter[str] = Counter()
    all_node_keys: set[str] = set()

    for manifest_row in sorted(manifest_rows, key=lambda row: row["record_id"]):
        graph_path = REPO / manifest_row["graph_path"]
        graph_sha256 = sha256_file(graph_path)
        graph = read_json(graph_path)
        graph_nodes = graph.get("nodes")
        graph_edges = graph.get("edges")
        if not isinstance(graph_nodes, list) or not isinstance(graph_edges, list):
            raise ValueError(f"Malformed graph export: {graph_path}")
        native_ids = [str(node["id"]) for node in graph_nodes]
        if len(native_ids) != len(set(native_ids)):
            raise ValueError(f"Duplicate native node ID within {manifest_row['doi']}")
        labels = {str(node.get("label", "")) for node in graph_nodes}
        unknown_labels = labels - allowed_node_labels
        if unknown_labels:
            raise ValueError(f"Unknown node labels in {manifest_row['doi']}: {unknown_labels}")
        edge_labels = {str(edge.get("label", "")) for edge in graph_edges}
        unknown_edge_labels = edge_labels - allowed_edge_labels
        if unknown_edge_labels:
            raise ValueError(
                f"Unknown relationship labels in {manifest_row['doi']}: {unknown_edge_labels}"
            )
        if sum(node.get("label") == "CausalMultiomicsAgingPaper" for node in graph_nodes) != 1:
            raise ValueError(f"Expected one paper root in {manifest_row['doi']}")

        document_keys = {
            native_id: node_key(manifest_row["record_id"], native_id)
            for native_id in native_ids
        }
        for node in graph_nodes:
            row = node_row(
                corpus_id=config["corpus_id"],
                manifest_row=manifest_row,
                graph_sha256=graph_sha256,
                node=node,
            )
            if row["node_key"] in all_node_keys:
                raise ValueError(f"Duplicate namespaced node key: {row['node_key']}")
            all_node_keys.add(row["node_key"])
            nodes.append(row)
            node_label_counts[str(node["label"])] += 1
            native_id_counts[str(node["id"])] += 1
        for edge in graph_edges:
            source = str(edge["source"])
            target = str(edge["target"])
            if source not in document_keys or target not in document_keys:
                raise ValueError(f"Unresolved edge endpoint in {manifest_row['doi']}: {edge}")
            label = str(edge["label"])
            edges.append(
                {
                    "corpus_id": config["corpus_id"],
                    "edge_key": edge_key(manifest_row["record_id"], source, target, label),
                    "record_id": manifest_row["record_id"],
                    "doi": manifest_row["doi"],
                    "source_key": document_keys[source],
                    "target_key": document_keys[target],
                    "edge_label": label,
                    "native_source_id": source,
                    "native_target_id": target,
                    "source_graph_sha256": graph_sha256,
                }
            )
            edge_label_counts[label] += 1
        graph_inventory.append(
            {
                "record_id": manifest_row["record_id"],
                "doi": manifest_row["doi"],
                "graph_path": manifest_row["graph_path"],
                "graph_sha256": graph_sha256,
                "nodes": len(graph_nodes),
                "edges": len(graph_edges),
            }
        )

    expected = config["expected"]
    if len(nodes) != expected["graph_nodes"] or len(edges) != expected["graph_edges"]:
        raise ValueError(
            f"Graph size drift: nodes={len(nodes)}, edges={len(edges)}, expected={expected}"
        )
    if len({row["edge_key"] for row in edges}) != len(edges):
        raise ValueError("Generated duplicate edge keys")

    fingerprint_payload = [
        {
            "record_id": row["record_id"],
            "doi": row["doi"],
            "graph_sha256": row["graph_sha256"],
        }
        for row in graph_inventory
    ]
    corpus_fingerprint = sha256_bytes(canonical_json(fingerprint_payload).encode("utf-8"))
    import_root = REPO / config["outputs"]["import_root"]
    nodes_path = import_root / "nodes.csv"
    edges_path = import_root / "edges.csv"
    load_path = import_root / "load.cypher"
    reset_path = import_root / "reset.cypher"
    write_csv(nodes_path, CSV_NODE_FIELDS, nodes)
    write_csv(edges_path, CSV_EDGE_FIELDS, edges)
    load_path.write_text(
        build_load_cypher(
            corpus_id=config["corpus_id"],
            corpus_fingerprint=corpus_fingerprint,
            node_labels=sorted(node_label_counts),
            edge_labels=sorted(edge_label_counts),
            reports=len(manifest_rows),
            graph_nodes=len(nodes),
            graph_edges=len(edges),
        ),
        encoding="utf-8",
    )
    reset_path.write_text(build_reset_cypher(config["corpus_id"]), encoding="utf-8")

    repeated_native_ids = [count for count in native_id_counts.values() if count > 1]
    result = {
        "schema_version": config["schema_version"],
        "status": "import_pack_built",
        "corpus_id": config["corpus_id"],
        "corpus_fingerprint": corpus_fingerprint,
        "source_manifest": config["source_manifest"],
        "source_manifest_sha256": sha256_file(source_manifest),
        "config": str(config_path.relative_to(REPO)),
        "config_sha256": sha256_file(config_path),
        "exporter": str(Path(__file__).resolve().relative_to(REPO)),
        "exporter_sha256": sha256_file(Path(__file__).resolve()),
        "reports": len(manifest_rows),
        "graph_nodes": len(nodes),
        "graph_edges": len(edges),
        "node_label_counts": dict(sorted(node_label_counts.items())),
        "edge_label_counts": dict(sorted(edge_label_counts.items())),
        "native_node_id_collision_groups_across_reports": len(repeated_native_ids),
        "maximum_native_node_id_multiplicity": max(repeated_native_ids, default=1),
        "namespaced_node_key_collisions": 0,
        "neo4j": config["neo4j"],
        "files": {
            "nodes_csv": {
                "path": str(nodes_path.relative_to(REPO)),
                "sha256": sha256_file(nodes_path),
                "rows": len(nodes),
            },
            "edges_csv": {
                "path": str(edges_path.relative_to(REPO)),
                "sha256": sha256_file(edges_path),
                "rows": len(edges),
            },
            "load_cypher": {
                "path": str(load_path.relative_to(REPO)),
                "sha256": sha256_file(load_path),
            },
            "reset_cypher": {
                "path": str(reset_path.relative_to(REPO)),
                "sha256": sha256_file(reset_path),
            },
            "docker_compose": {
                "path": str(COMPOSE_PATH.relative_to(REPO)),
                "sha256": sha256_file(COMPOSE_PATH),
            },
            "example_queries": {
                "path": str(QUERIES_PATH.relative_to(REPO)),
                "sha256": sha256_file(QUERIES_PATH),
            },
        },
        "source_graph_inventory": graph_inventory,
        "methodological_boundary": config["methodological_boundary"],
    }
    compact_manifest = REPO / config["outputs"]["compact_manifest"]
    write_json(compact_manifest, result)
    report = "\n".join(
        [
            "# Neo4j retrieval import v0.1.0",
            "",
            f"Corpus fingerprint: `{corpus_fingerprint}`",
            "",
            f"- Reports: {len(manifest_rows)}",
            f"- Imported Docling Graph nodes: {len(nodes)}",
            f"- Imported Docling Graph relationships: {len(edges)}",
            "- Cross-report native-ID collision groups preserved separately: "
            f"{len(repeated_native_ids)}",
            "- Namespaced node-key collisions: 0",
            f"- Neo4j image: `{config['neo4j']['image']}`",
            "",
            "The import represents document-scoped graph occurrences. It does not merge",
            "similarly named entities across reports. The current v1 edges support",
            "report-level co-occurrence retrieval; they do not establish that an omics",
            "layer and aging construct participate in the same causal analysis.",
            "",
            "Graph absence cannot exclude a report. Decisive citations must resolve to",
            "the frozen deterministic evidence-atom index.",
            "",
        ]
    )
    report_path = REPO / config["outputs"]["compact_report"]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    result = build(args.config.resolve())
    display = {
        key: result[key] for key in ("status", "reports", "graph_nodes", "graph_edges")
    }
    print(json.dumps(display, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
