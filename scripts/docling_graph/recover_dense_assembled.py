#!/usr/bin/env python3
"""Recover a validated graph from a completed dense extraction assembly.

Docling Graph persists ``dense_assembled_root.json`` before final Pydantic
validation.  A malformed fill response can therefore leave a small number of
incomplete list items while the rest of an expensive dense extraction remains
valid.  This recovery drops only list items identified by Pydantic validation
errors, records every dropped path, and rebuilds the deterministic graph.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.docling_graph.run_corpus import (  # noqa: E402
    append_attempt,
    load_template,
    read_attempts,
    sha256_file,
)


def _get_at_path(value: Any, path: tuple[Any, ...]) -> Any:
    for part in path:
        value = value[part]
    return value


def _invalid_list_item_paths(data: Any, errors: list[dict[str, Any]]) -> set[tuple[Any, ...]]:
    paths: set[tuple[Any, ...]] = set()
    for error in errors:
        loc = tuple(error.get("loc", ()))
        for index, part in enumerate(loc):
            if not isinstance(part, int):
                continue
            parent_path = loc[:index]
            try:
                parent = _get_at_path(data, parent_path)
            except (KeyError, IndexError, TypeError):
                continue
            if isinstance(parent, list) and 0 <= part < len(parent):
                paths.add(loc[: index + 1])
                break
    return paths


def validate_by_dropping_invalid_list_items(
    data: dict[str, Any], template: type[BaseModel]
) -> tuple[BaseModel, list[dict[str, Any]]]:
    """Validate while dropping only list items named by validation errors."""
    working = json.loads(json.dumps(data))
    dropped: list[dict[str, Any]] = []
    while True:
        try:
            return template.model_validate(working), dropped
        except ValidationError as exc:
            errors = exc.errors()
            paths = _invalid_list_item_paths(working, errors)
            if not paths:
                raise
            for path in sorted(paths, key=lambda value: (len(value), value), reverse=True):
                parent = _get_at_path(working, path[:-1])
                item = parent[path[-1]]
                related = [
                    {
                        "loc": list(error.get("loc", ())),
                        "type": error.get("type"),
                        "msg": error.get("msg"),
                    }
                    for error in errors
                    if tuple(error.get("loc", ()))[: len(path)] == path
                ]
                dropped.append(
                    {
                        "path": list(path),
                        "item_sha256": hashlib.sha256(
                            json.dumps(item, sort_keys=True, default=str).encode("utf-8")
                        ).hexdigest(),
                        "validation_errors": related,
                    }
                )
                del parent[path[-1]]


def _load_jsonl_by_key(path: Path, key: str) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[str(row[key])] = row
    return rows


def recover(config_path: Path, document_id: str) -> dict[str, Any]:
    from docling_graph.core.converters.graph_converter import GraphConverter
    from docling_graph.core.converters.node_id_registry import NodeIDRegistry
    from docling_graph.core.exporters import CSVExporter, JSONExporter
    from docling_graph.core.provenance.binder import bind_provenance
    from docling_graph.core.provenance.models import (
        DocumentOrigin,
        ProvenanceLedger,
        content_hash,
        template_schema_hash,
    )

    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_root = REPO / config["runtime"]["output_root"]
    corpus_path = output_root / "corpus_manifest.csv"
    with corpus_path.open(encoding="utf-8", newline="") as handle:
        corpus = {row["document_id"]: row for row in csv.DictReader(handle)}
    if document_id not in corpus:
        raise KeyError(f"Unknown document_id: {document_id}")
    source_row = corpus[document_id]
    conversions = _load_jsonl_by_key(output_root / "conversion_manifest.jsonl", "document_id")
    conversion = conversions[document_id]
    source = REPO / conversion["docling_json_path"]
    document_output = output_root / "artifacts" / document_id
    assemblies = sorted(document_output.rglob("debug/dense_assembled_root.json"))
    if not assemblies:
        raise FileNotFoundError(f"No dense assembly for {document_id}")
    assembly_path = assemblies[-1]
    debug_dir = assembly_path.parent
    provenance_path = debug_dir / "dense_provenance.json"
    if not provenance_path.is_file():
        raise FileNotFoundError(provenance_path)

    template = load_template(config["docling_graph"]["template"])
    assembled = json.loads(assembly_path.read_text(encoding="utf-8"))
    model, dropped = validate_by_dropping_invalid_list_items(assembled, template)
    ledger = ProvenanceLedger.model_validate_json(provenance_path.read_text(encoding="utf-8"))
    ledger.document = DocumentOrigin(
        document_id=content_hash(source.read_bytes()),
        source=str(source),
        input_type="docling_document",
        template_name=template.__name__,
        template_schema_hash=template_schema_hash(template),
    )

    registry = NodeIDRegistry()
    bind_stats: dict[str, int] = {}

    def binder(graph: Any, models: Any) -> None:
        bind_stats.update(
            bind_provenance(
                graph=graph,
                models=models,
                ledger=ledger,
                registry=registry,
                template=template,
                include_spans=True,
            )
        )

    graph, _ = GraphConverter(
        add_reverse_edges=False,
        validate_graph=True,
        registry=registry,
    ).pydantic_list_to_graph([model], provenance_binder=binder)
    ledger.bind_stats = bind_stats

    artifact_root = assembly_path.parent.parent
    graph_dir = artifact_root / "docling_graph"
    docling_dir = artifact_root / "docling"
    graph_dir.mkdir(parents=True, exist_ok=True)
    docling_dir.mkdir(parents=True, exist_ok=True)
    graph_path = graph_dir / "graph.json"
    final_provenance_path = graph_dir / "provenance.json"
    JSONExporter().export(graph, graph_path)
    CSVExporter().export(graph, graph_dir)
    final_provenance_path.write_text(ledger.model_dump_json(indent=2), encoding="utf-8")
    (docling_dir / "chunks.json").write_text(
        json.dumps(
            [record.model_dump(mode="json") for _, record in sorted(ledger.chunks.items())],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    recovery_audit_path = debug_dir / "dense_validation_recovery.json"
    recovery_audit_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "strategy": "drop_only_pydantic_invalid_list_items",
                "assembled_sha256": sha256_file(assembly_path),
                "dropped_item_count": len(dropped),
                "dropped_items": dropped,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    previous_attempts = read_attempts(output_root / "run_manifest.jsonl")
    retry_index = 1 + max(
        [int(row.get("retry_index", 0)) for row in previous_attempts if row["document_id"] == document_id],
        default=-1,
    )
    attempt = {
        "document_id": document_id,
        "doi": source_row["doi"],
        "source_path": source_row["source_path"],
        "source_sha256": source_row["source_sha256"],
        "graph_input_path": conversion["docling_json_path"],
        "graph_input_sha256": conversion["docling_json_sha256"],
        "model": config["model"]["codex_cli_model"],
        "reasoning_effort": config["model"]["reasoning_effort"],
        "config_sha256": sha256_file(config_path),
        "template_sha256": sha256_file(REPO / "scripts/docling_graph/templates/causal_multiomics_aging.py"),
        "extraction_contract": "dense",
        "retry_index": retry_index,
        "started_at_unix": time.time(),
        "status": "success",
        "elapsed_seconds": 0.0,
        "graph_nodes": graph.number_of_nodes(),
        "graph_edges": graph.number_of_edges(),
        "extracted_models": 1,
        "graph_path": str(graph_path.relative_to(REPO)),
        "graph_sha256": sha256_file(graph_path),
        "provenance_path": str(final_provenance_path.relative_to(REPO)),
        "provenance_sha256": sha256_file(final_provenance_path),
        "dense_validation_recovery": {
            "assembled_path": str(assembly_path.relative_to(REPO)),
            "audit_path": str(recovery_audit_path.relative_to(REPO)),
            "audit_sha256": sha256_file(recovery_audit_path),
            "dropped_item_count": len(dropped),
        },
    }
    append_attempt(output_root / "run_manifest.jsonl", attempt)
    return attempt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("document_id")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    attempt = recover(args.config.resolve(), args.document_id)
    print(json.dumps(attempt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
