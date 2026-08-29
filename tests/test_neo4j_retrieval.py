from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "protocol/neo4j/retrieval_v0.1.0.json"


def load_builder():
    path = REPO / "scripts/neo4j/build_import_pack.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_neo4j_runtime_is_current_pinned_and_isolated() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    compose = (REPO / "infra/neo4j/compose.yml").read_text(encoding="utf-8")
    image = config["neo4j"]["image"]

    assert config["neo4j"]["version"] == "2026.07.1"
    assert "@sha256:" in image
    assert image in compose
    assert config["neo4j"]["container_name"] in compose
    assert "127.0.0.1:7475:7474" in compose
    assert "127.0.0.1:7688:7687" in compose
    assert "nla_docling_neo4j_data" not in compose
    assert config["neo4j"]["data_volume"] in compose


def test_node_identity_is_document_scoped() -> None:
    builder = load_builder()
    first = builder.node_key("doi:10.1/example-a", "CausalAnalysis_deadbeef")
    second = builder.node_key("doi:10.1/example-b", "CausalAnalysis_deadbeef")

    assert first != second
    assert first.endswith("|CausalAnalysis_deadbeef")


def test_generated_cypher_uses_typed_labels_edges_and_fulltext() -> None:
    builder = load_builder()
    script = builder.build_load_cypher(
        corpus_id="fixture",
        corpus_fingerprint="abc123",
        node_labels=["CausalAnalysis", "CausalMultiomicsAgingPaper"],
        edge_labels=["REPORTS_CAUSAL_ANALYSIS"],
        reports=1,
        graph_nodes=2,
        graph_edges=1,
    )

    assert "ReviewGraphNode:`CausalAnalysis`" in script
    assert "[relationship:`REPORTS_CAUSAL_ANALYSIS`" in script
    assert "CREATE FULLTEXT INDEX review_graph_text IF NOT EXISTS" in script
    assert "graph_absence_can_exclude = false" in script


def test_compact_import_manifest_has_complete_canonical_inventory() -> None:
    manifest_path = REPO / "analysis/neo4j/retrieval_v0.1.0/import_manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["reports"] == 101
    assert manifest["graph_nodes"] == 1536
    assert manifest["graph_edges"] == 1435
    assert len(manifest["source_graph_inventory"]) == 101
    assert manifest["namespaced_node_key_collisions"] == 0

    source_manifest = REPO / manifest["source_manifest"]
    with source_manifest.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["doi"] for row in rows} == {
        row["doi"] for row in manifest["source_graph_inventory"]
    }
