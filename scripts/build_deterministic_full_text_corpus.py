#!/usr/bin/env python3
"""Merge frozen full-text cohorts without model-generated selection metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = [
    REPO / "data/full_text_screening/v1.0.0_graph_chunks_97/input_manifest.json",
    REPO
    / "data/full_text_screening/v1.1.0_oversized_20k_seek65_graph_chunks/input_manifest.json",
    REPO
    / "data/full_text_screening/v1.2.1_agent_recovery17_graph_chunks/input_manifest.json",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
        ),
        encoding="utf-8",
    )


def repo_relative(path: Path) -> str:
    return str(path.resolve().relative_to(REPO))


def clean_record(
    record: dict[str, Any], source_manifest: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    sections = []
    removed_graph_flags = 0
    for section in record.get("sections", []):
        cleaned = {key: value for key, value in section.items() if key != "graph_priority"}
        removed_graph_flags += int("graph_priority" in section)
        sections.append(cleaned)

    allowed = {
        "record_id",
        "document_id",
        "doi",
        "source",
        "year",
        "title",
        "abstract",
    }
    cleaned_record = {key: record.get(key, "") for key in allowed}
    cleaned_record["sections"] = sections
    cleaned_record["input_provenance"] = {
        "source_manifest": repo_relative(source_manifest),
        "source_manifest_sha256": sha256(source_manifest),
        "source_chunk_artifact": record.get("deterministic_chunks", {}),
        "model_generated_selection_metadata_removed": True,
    }
    audit = {
        "record_id": cleaned_record["record_id"],
        "doi": cleaned_record["doi"],
        "source_manifest": repo_relative(source_manifest),
        "sections": len(sections),
        "removed_graph_priority_fields": removed_graph_flags,
        "removed_top_level_fields": sorted(set(record) - allowed - {"sections"}),
    }
    return cleaned_record, audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--source-manifest", action="append", type=Path)
    parser.add_argument("--shards", type=int, default=24)
    parser.add_argument("--expected", type=int, default=158)
    args = parser.parse_args()

    output = args.output_dir.resolve()
    if output.exists():
        raise SystemExit(f"Refusing to overwrite: {output}")
    source_manifests = [path.resolve() for path in (args.source_manifest or DEFAULT_SOURCES)]

    records: list[dict[str, Any]] = []
    audits: list[dict[str, Any]] = []
    source_entries = []
    for manifest_path in source_manifests:
        manifest = read_json(manifest_path)
        input_path = REPO / manifest["input"]["path"]
        if sha256(input_path) != manifest["input"]["sha256"]:
            raise SystemExit(f"Source input hash mismatch: {input_path}")
        source_rows = read_jsonl(input_path)
        if len(source_rows) != int(manifest["records"]):
            raise SystemExit(f"Source record count mismatch: {input_path}")
        source_entries.append(
            {
                "manifest": repo_relative(manifest_path),
                "manifest_sha256": sha256(manifest_path),
                "input": repo_relative(input_path),
                "input_sha256": sha256(input_path),
                "records": len(source_rows),
            }
        )
        for row in source_rows:
            cleaned, audit = clean_record(row, manifest_path)
            records.append(cleaned)
            audits.append(audit)

    if len(records) != args.expected:
        raise SystemExit(f"Expected {args.expected} records, found {len(records)}")
    record_ids = [str(row["record_id"]) for row in records]
    if len(set(record_ids)) != len(record_ids):
        raise SystemExit("Duplicate record_id in merged full-text corpus")
    dois = [str(row["doi"]).casefold() for row in records if str(row["doi"]).strip()]
    if len(set(dois)) != len(dois):
        raise SystemExit("Duplicate non-empty DOI in merged full-text corpus")

    records.sort(key=lambda row: str(row["record_id"]))
    audits.sort(key=lambda row: str(row["record_id"]))
    output.mkdir(parents=True)
    input_path = output / "input.jsonl"
    audit_path = output / "input_audit.jsonl"
    write_jsonl(input_path, records)
    write_jsonl(audit_path, audits)

    shards = []
    for index in range(args.shards):
        rows = records[index :: args.shards]
        if not rows:
            continue
        shard_path = output / "shards" / f"shard_{index + 1:02d}.jsonl"
        write_jsonl(shard_path, rows)
        shards.append(
            {
                "path": repo_relative(shard_path),
                "sha256": sha256(shard_path),
                "records": len(rows),
            }
        )

    manifest = {
        "status": "frozen_deterministic_full_text_screening_input",
        "method_version": "v1.5.3-rc1",
        "selection_contract": "no_model_generated_section_selection_or_ranking",
        "records": len(records),
        "records_with_doi": len(dois),
        "unique_doi": len(set(dois)),
        "records_without_doi": len(records) - len(dois),
        "source_cohorts": source_entries,
        "input": {
            "path": repo_relative(input_path),
            "sha256": sha256(input_path),
            "records": len(records),
        },
        "audit": {
            "path": repo_relative(audit_path),
            "sha256": sha256(audit_path),
        },
        "shards": shards,
    }
    manifest_path = output / "input_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "records": len(records),
                "unique_doi": len(set(dois)),
                "records_without_doi": len(records) - len(dois),
                "shards": len(shards),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
