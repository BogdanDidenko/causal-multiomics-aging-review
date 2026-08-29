#!/usr/bin/env python3
"""Validate the isolated Neo4j retrieval database against its frozen import manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "protocol/neo4j/retrieval_v0.1.0.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def run_cypher(container: str, query: str) -> list[dict[str, str]]:
    output = run_command(
        ["docker", "exec", container, "cypher-shell", "--format", "plain", query]
    )
    if not output:
        return []
    rows = list(csv.reader(output.splitlines(), skipinitialspace=True))
    if not rows:
        return []
    header = rows[0]
    return [dict(zip(header, row, strict=True)) for row in rows[1:]]


def integer_result(container: str, query: str, field: str) -> int:
    rows = run_cypher(container, query)
    if len(rows) != 1 or field not in rows[0]:
        raise RuntimeError(f"Expected one Cypher result with {field!r}, got {rows!r}")
    return int(rows[0][field])


def check(name: str, expected: Any, observed: Any) -> dict[str, Any]:
    return {
        "name": name,
        "expected": expected,
        "observed": observed,
        "passed": expected == observed,
    }


def validate(config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    manifest_path = REPO / config["outputs"]["compact_manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    container = config["neo4j"]["container_name"]
    checks: list[dict[str, Any]] = []

    for file_record in manifest["files"].values():
        path = REPO / file_record["path"]
        checks.append(
            check(
                f"artifact_sha256:{file_record['path']}",
                file_record["sha256"],
                sha256_file(path),
            )
        )

    version_rows = run_cypher(
        container,
        "CALL dbms.components() YIELD name, versions, edition "
        "WHERE name = 'Neo4j Kernel' "
        "RETURN versions[0] AS version, edition;",
    )
    if len(version_rows) != 1:
        raise RuntimeError(f"Unexpected Neo4j component response: {version_rows!r}")
    checks.append(check("neo4j_version", config["neo4j"]["version"], version_rows[0]["version"]))
    checks.append(check("neo4j_edition", config["neo4j"]["edition"], version_rows[0]["edition"]))

    corpus = json.dumps(config["corpus_id"])
    checks.extend(
        [
            check(
                "review_graph_nodes",
                manifest["graph_nodes"],
                integer_result(
                    container,
                    f"MATCH (node:ReviewGraphNode {{corpus_id: {corpus}}}) "
                    "RETURN count(node) AS count;",
                    "count",
                ),
            ),
            check(
                "review_graph_edges",
                manifest["graph_edges"],
                integer_result(
                    container,
                    f"MATCH (source:ReviewGraphNode {{corpus_id: {corpus}}})-[relationship]->"
                    f"(target:ReviewGraphNode {{corpus_id: {corpus}}}) "
                    "RETURN count(relationship) AS count;",
                    "count",
                ),
            ),
            check(
                "reports",
                manifest["reports"],
                integer_result(
                    container,
                    f"MATCH (report:ReviewGraphNode:CausalMultiomicsAgingPaper "
                    f"{{corpus_id: {corpus}}}) RETURN count(report) AS count;",
                    "count",
                ),
            ),
            check(
                "corpus_report_links",
                manifest["reports"],
                integer_result(
                    container,
                    f"MATCH (:ReviewCorpus {{corpus_id: {corpus}}})-[:CONTAINS_REPORT]->"
                    "(report:CausalMultiomicsAgingPaper) RETURN count(report) AS count;",
                    "count",
                ),
            ),
            check(
                "missing_provenance",
                0,
                integer_result(
                    container,
                    f"MATCH (node:ReviewGraphNode {{corpus_id: {corpus}}}) "
                    "WHERE node.provenance_json IS NULL OR node.provenance_json = '' "
                    "RETURN count(node) AS count;",
                    "count",
                ),
            ),
            check(
                "duplicate_namespaced_node_keys",
                0,
                integer_result(
                    container,
                    f"MATCH (node:ReviewGraphNode {{corpus_id: {corpus}}}) "
                    "WITH node.node_key AS key, count(*) AS occurrences "
                    "WHERE occurrences <> 1 RETURN count(*) AS count;",
                    "count",
                ),
            ),
            check(
                "cross_document_graph_edges",
                0,
                integer_result(
                    container,
                    f"MATCH (source:ReviewGraphNode {{corpus_id: {corpus}}})-[relationship]->"
                    f"(target:ReviewGraphNode {{corpus_id: {corpus}}}) "
                    "WHERE source.record_id <> target.record_id "
                    "RETURN count(relationship) AS count;",
                    "count",
                ),
            ),
        ]
    )

    expected_indexes = [
        "review_corpus_id",
        "review_graph_design_family",
        "review_graph_doi",
        "review_graph_node_key",
        "review_graph_omics_layer",
        "review_graph_text",
    ]
    indexes = run_cypher(
        container,
        "SHOW INDEXES YIELD name, state "
        f"WHERE name IN {json.dumps(expected_indexes)} RETURN name, state ORDER BY name;",
    )
    checks.append(check("online_indexes", expected_indexes, [row["name"] for row in indexes]))
    checks.append(
        check(
            "index_states",
            ["ONLINE"] * len(expected_indexes),
            [row["state"] for row in indexes],
        )
    )
    fulltext_hits = integer_result(
        container,
        "CALL db.index.fulltext.queryNodes('review_graph_text', 'aging') "
        "YIELD node, score "
        f"WHERE node.corpus_id = {corpus} RETURN count(node) AS count;",
        "count",
    )
    checks.append(
        {
            "name": "fulltext_retrieval_smoke_test",
            "expected": ">0",
            "observed": fulltext_hits,
            "passed": fulltext_hits > 0,
        }
    )

    label_rows = run_cypher(
        container,
        f"MATCH (node:ReviewGraphNode {{corpus_id: {corpus}}}) "
        "RETURN node.node_label AS label, count(*) AS count ORDER BY label;",
    )
    observed_labels = {row["label"]: int(row["count"]) for row in label_rows}
    checks.append(check("node_label_counts", manifest["node_label_counts"], observed_labels))
    relationship_rows = run_cypher(
        container,
        f"MATCH (source:ReviewGraphNode {{corpus_id: {corpus}}})-[relationship]->"
        f"(target:ReviewGraphNode {{corpus_id: {corpus}}}) "
        "RETURN type(relationship) AS label, count(*) AS count ORDER BY label;",
    )
    observed_relationships = {row["label"]: int(row["count"]) for row in relationship_rows}
    checks.append(
        check("edge_label_counts", manifest["edge_label_counts"], observed_relationships)
    )

    image = run_command(
        ["docker", "inspect", container, "--format", "{{.Config.Image}}"]
    )
    image_id = run_command(["docker", "inspect", container, "--format", "{{.Image}}"])
    checks.append(check("container_image", config["neo4j"]["image"], image))
    passed = all(item["passed"] for item in checks)
    result = {
        "schema_version": config["schema_version"],
        "status": "pass" if passed else "fail",
        "corpus_id": config["corpus_id"],
        "corpus_fingerprint": manifest["corpus_fingerprint"],
        "container": container,
        "container_image": image,
        "container_image_id": image_id,
        "fulltext_smoke_test_hits": fulltext_hits,
        "checks": checks,
    }
    output = REPO / config["outputs"]["validation_json"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_lines = [
        "# Neo4j retrieval validation v0.1.0",
        "",
        f"Status: **{result['status']}**",
        "",
        f"- Container: `{container}`",
        f"- Image: `{image}`",
        f"- Corpus fingerprint: `{manifest['corpus_fingerprint']}`",
        f"- Full-text `aging` smoke-test hits: {fulltext_hits}",
        "",
        "| Check | Expected | Observed | Passed |",
        "|---|---:|---:|:---:|",
    ]
    for item in checks:
        expected = json.dumps(item["expected"], ensure_ascii=False, sort_keys=True)
        observed = json.dumps(item["observed"], ensure_ascii=False, sort_keys=True)
        report_lines.append(
            f"| `{item['name']}` | `{expected}` | `{observed}` | "
            f"{'yes' if item['passed'] else 'no'} |"
        )
    report_lines.extend(
        [
            "",
            "This validates database integrity and retrieval mechanics. It does not",
            "measure scientific recall, precision, or causal-claim validity.",
            "",
        ]
    )
    report_path = REPO / config["outputs"]["validation_report"]
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    result = validate(args.config.resolve())
    print(json.dumps({"status": result["status"], "checks": len(result["checks"])}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
