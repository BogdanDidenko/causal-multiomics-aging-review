#!/usr/bin/env python3
"""Freeze graph-indexed Docling chunks as full-text screening records."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def graph_chunk_ids(graph: dict[str, Any]) -> set[int]:
    identifiers: set[int] = set()
    for node in graph.get("nodes", []):
        provenance = node.get("__provenance__", {})
        if provenance.get("match") != "verbatim":
            continue
        identifiers.update(int(value) for value in provenance.get("chunks", []))
    return identifiers


def abstract_metadata(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {str(row.get("doi", "")).strip().casefold(): row for row in rows}


def canonical_graph_runs(path: Path) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        if row.get("status") == "success":
            selected.setdefault(str(row["document_id"]), row)
    return selected


def build_records(
    graph_root: Path,
    metadata_path: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    metadata = abstract_metadata(metadata_path)
    corpus_path = graph_root / "corpus_manifest.csv"
    with corpus_path.open(encoding="utf-8", newline="") as handle:
        corpus = list(csv.DictReader(handle))
    runs = canonical_graph_runs(graph_root / "run_manifest.jsonl")
    records: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    for source in corpus:
        document_id = source["document_id"]
        if document_id not in runs:
            continue
        run = runs[document_id]
        graph_path = REPO / run["graph_path"]
        chunks_path = graph_path.parent.parent / "docling" / "chunks.json"
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
        priority = graph_chunk_ids(graph)
        doi = source["doi"].casefold()
        meta = metadata.get(doi, {})
        sections = []
        for chunk in chunks:
            chunk_id = int(chunk["chunk_id"])
            headings = [str(value) for value in chunk.get("headings", [])]
            sections.append(
                {
                    "section_id": f"chunk:{chunk_id:04d}",
                    "heading": " > ".join(headings),
                    "text": str(chunk["text"]),
                    "text_hash": str(chunk["text_hash"]),
                    "page_numbers": chunk.get("page_numbers", []),
                    "graph_priority": chunk_id in priority,
                }
            )
        record = {
            "record_id": source["record_id"],
            "document_id": document_id,
            "doi": doi,
            "source": meta.get("source", "full_text_corpus"),
            "year": meta.get("year", ""),
            "title": source["title"],
            "abstract": meta.get("abstract", "") or sections[0]["text"],
            "frozen_graph": {
                "path": run["graph_path"],
                "sha256": run["graph_sha256"],
                "model": run["model"],
                "reasoning_effort": run["reasoning_effort"],
            },
            "deterministic_chunks": {
                "path": str(chunks_path.relative_to(REPO)),
                "sha256": sha256_file(chunks_path),
                "count": len(sections),
            },
            "sections": sections,
        }
        records.append(record)
        audit.append(
            {
                "record_id": source["record_id"],
                "doi": doi,
                "document_id": document_id,
                "graph_sha256": run["graph_sha256"],
                "chunks_sha256": sha256_file(chunks_path),
                "chunks": len(sections),
                "graph_priority_chunks": len(priority),
            }
        )
    records.sort(key=lambda row: row["record_id"])
    audit.sort(key=lambda row: row["record_id"])
    return records, audit


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("graph_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--metadata",
        type=Path,
        default=REPO / "data/screening/v1.1.2_full_corpus/input.csv",
    )
    parser.add_argument("--shards", type=int, default=24)
    parser.add_argument("--expected", type=int, default=97)
    args = parser.parse_args()
    graph_root = args.graph_root.resolve()
    output = args.output_dir.resolve()
    if output.exists():
        raise SystemExit(f"Refusing to overwrite: {output}")
    output.mkdir(parents=True)
    records, audit = build_records(graph_root, args.metadata.resolve())
    if len(records) != args.expected:
        raise SystemExit(f"Expected {args.expected} records, found {len(records)}")
    if len({row["doi"] for row in records}) != len(records):
        raise SystemExit("Duplicate DOI in full-text screening input")
    input_path = output / "input.jsonl"
    write_jsonl(input_path, records)
    shard_items = []
    for index in range(args.shards):
        rows = records[index :: args.shards]
        if not rows:
            continue
        path = output / "shards" / f"shard_{index + 1:02d}.jsonl"
        path.parent.mkdir(exist_ok=True)
        write_jsonl(path, rows)
        shard_items.append(
            {
                "path": str(path.relative_to(REPO)),
                "sha256": sha256_file(path),
                "records": len(rows),
            }
        )
    audit_path = output / "input_audit.jsonl"
    write_jsonl(audit_path, audit)
    manifest = {
        "status": "frozen_full_text_screening_input",
        "records": len(records),
        "unique_doi": len({row["doi"] for row in records}),
        "graph_root": str(graph_root.relative_to(REPO)),
        "graph_run_manifest_sha256": sha256_file(graph_root / "run_manifest.jsonl"),
        "metadata_path": str(args.metadata.resolve().relative_to(REPO)),
        "metadata_sha256": sha256_file(args.metadata.resolve()),
        "input": {
            "path": str(input_path.relative_to(REPO)),
            "sha256": sha256_file(input_path),
        },
        "audit": {
            "path": str(audit_path.relative_to(REPO)),
            "sha256": sha256_file(audit_path),
        },
        "shards": shard_items,
    }
    (output / "input_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"records": len(records), "shards": len(shard_items)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
