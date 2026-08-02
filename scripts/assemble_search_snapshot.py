#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import search_databases as search


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_component(value: str) -> tuple[str, Path]:
    source, separator, path = value.partition("=")
    if not separator or not source or not path:
        raise argparse.ArgumentTypeError("component must be SOURCE=SEARCH_DIR")
    return source, Path(path)


def query_files(manifest: dict[str, Any]) -> dict[str, str]:
    if files := manifest.get("query_files"):
        return {str(key): str(value) for key, value in files.items()}
    return {"combined": str(manifest["query_file"])}


def query_hashes(manifest: dict[str, Any]) -> dict[str, str]:
    hashes = manifest["query_sha256"]
    if isinstance(hashes, dict):
        return {str(key): str(value) for key, value in hashes.items()}
    return {"combined": str(hashes)}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assemble independently executed source searches into one snapshot"
    )
    parser.add_argument("--component", action="append", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--protocol-version", required=True)
    args = parser.parse_args()

    components = dict(parse_component(value) for value in args.component)
    if len(components) != len(args.component):
        raise SystemExit("Duplicate source component")
    if args.output.exists():
        raise SystemExit(f"Refusing to overwrite existing snapshot: {args.output}")

    source_records: list[dict[str, str]] = []
    component_audit: dict[str, Any] = {}
    for source, directory in sorted(components.items()):
        manifest_path = directory / "manifests" / f"{source}.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("source") != source:
            raise SystemExit(f"{source}: source manifest mismatch")
        normalized_path = directory / manifest["normalized_file"]
        if search.sha256_file(normalized_path) != manifest["normalized_sha256"]:
            raise SystemExit(f"{source}: normalized SHA-256 mismatch")
        rows = read_csv(normalized_path)
        if len(rows) != int(manifest["retrieved_count"]):
            raise SystemExit(f"{source}: normalized record count mismatch")
        if {row.get("source") for row in rows} != {source}:
            raise SystemExit(f"{source}: normalized source column mismatch")

        files = query_files(manifest)
        hashes = query_hashes(manifest)
        for branch, query_path_text in files.items():
            query_path = search.ROOT / query_path_text
            observed_text = search.sha256_text(
                query_path.read_text(encoding="utf-8").strip()
            )
            observed_file = search.sha256_file(query_path)
            if hashes[branch] not in {observed_text, observed_file}:
                raise SystemExit(f"{source}.{branch}: query SHA-256 mismatch")

        source_records.extend(rows)
        component_audit[source] = {
            "search_directory": str(directory),
            "source_manifest": str(manifest_path),
            "source_manifest_sha256": search.sha256_file(manifest_path),
            "reported_count": manifest["reported_count"],
            "retrieved_count": len(rows),
            "local_three_block_count": int(
                manifest.get("local_three_block_count", 0)
            ),
            "query_files": files,
            "query_sha256": hashes,
            "normalized_file": str(normalized_path),
            "normalized_sha256": manifest["normalized_sha256"],
            "started_at": manifest.get("started_at"),
            "completed_at": manifest.get("completed_at"),
            "source_details": manifest.get("source_details", {}),
        }

    source_records.sort(
        key=lambda row: (
            row.get("source", ""),
            row.get("publication_date", ""),
            row.get("source_record_id", ""),
        )
    )
    combined_path = args.output / "normalized" / "all_sources.csv"
    search.write_records(combined_path, source_records)
    manifest = {
        "manifest_version": "1.0.0",
        "protocol_version": args.protocol_version,
        "snapshot_type": "composite_complete_retrieval",
        "created_at": datetime.now(UTC).isoformat(),
        "git_revision": search.git_revision(),
        "sources": sorted(components),
        "source_components": component_audit,
        "complete_retrieval": True,
        "total_source_records": len(source_records),
        "total_local_three_block_records": sum(
            str(row.get("local_three_block_match", "")).lower() == "true"
            for row in source_records
        ),
        "combined_file": str(combined_path.relative_to(args.output)),
        "combined_sha256": search.sha256_file(combined_path),
        "interpretation": (
            "Source records are counts before cross-database deduplication. "
            "OpenAlex has already been deduplicated across query branches."
        ),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "search_run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"sources={len(components)} records={len(source_records)} "
        f"local_three_block={manifest['total_local_three_block_records']}"
    )


if __name__ == "__main__":
    main()
