#!/usr/bin/env python3
"""Freeze records previously routed as oversized abstract metadata."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"Expected JSON objects in {path}")
                rows.append(value)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("primary_runs", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--new-maximum", type=int, default=20000)
    parser.add_argument("--expected-records", type=int, default=397)
    parser.add_argument("--shards", type=int, default=48)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    source = read_csv(args.input)
    source_by_id = {row["record_id"]: row for row in source}
    if len(source_by_id) != len(source):
        raise SystemExit("Duplicate record IDs in screening input")
    result_files = sorted(args.primary_runs.glob("shard_*/screening_results.jsonl"))
    primary = [row for path in result_files for row in read_jsonl(path)]
    oversized = [
        row
        for row in primary
        if row.get("final_decision") == "seek_full_text"
        and row.get("decision_reason") == "oversized_abstract_metadata"
    ]
    identifiers = {str(row["record_id"]) for row in oversized}
    if len(identifiers) != len(oversized):
        raise SystemExit("Duplicate oversized record IDs")
    if len(identifiers) != args.expected_records:
        raise SystemExit(
            f"Expected {args.expected_records} oversized records, found {len(identifiers)}"
        )
    if not identifiers <= source_by_id.keys():
        raise SystemExit("Oversized result IDs are absent from source input")

    selected = [row for row in source if row["record_id"] in identifiers]
    fields = list(source[0])
    output = args.output_dir
    input_path = output / "input.csv"
    missing_path = output / "missing_abstract.csv"
    write_csv(input_path, selected, fields)
    write_csv(missing_path, [], fields)

    index_rows = [
        {
            "record_id": row["record_id"],
            "doi": row.get("doi", ""),
            "title": row.get("title", ""),
            "abstract_chars": str(len(row.get("abstract", ""))),
            "within_new_maximum": str(len(row.get("abstract", "")) <= args.new_maximum),
        }
        for row in selected
    ]
    index_path = output / "oversized_index.csv"
    write_csv(index_path, index_rows, list(index_rows[0]))

    shard_count = min(args.shards, len(selected))
    shards: list[dict[str, Any]] = []
    for index in range(shard_count):
        rows = selected[index::shard_count]
        path = output / "shards" / f"shard_{index + 1:02d}.csv"
        write_csv(path, rows, fields)
        shards.append(
            {
                "path": relative(path.resolve(), root),
                "sha256": sha256(path),
                "records": len(rows),
            }
        )

    within = sum(len(row.get("abstract", "")) <= args.new_maximum for row in selected)
    manifest = {
        "status": "frozen_oversized_abstract_rerun",
        "policy": "full abstract is retained; no truncation or semantic packaging",
        "prior_maximum_chars": 5000,
        "new_maximum_chars": args.new_maximum,
        "expected_records": args.expected_records,
        "records_within_new_maximum": within,
        "records_still_over_new_maximum": len(selected) - within,
        "screening_input": {
            "path": relative(input_path.resolve(), root),
            "sha256": sha256(input_path),
            "records": len(selected),
        },
        "missing_abstract_queue": {
            "path": relative(missing_path.resolve(), root),
            "sha256": sha256(missing_path),
            "records": 0,
        },
        "oversized_index": {
            "path": relative(index_path.resolve(), root),
            "sha256": sha256(index_path),
            "records": len(index_rows),
        },
        "primary_screening_input": {
            "path": relative(args.input.resolve(), root),
            "sha256": sha256(args.input),
            "records": len(source),
        },
        "primary_result_files": [
            {"path": relative(path.resolve(), root), "sha256": sha256(path)}
            for path in result_files
        ],
        "primary_result_records": len(primary),
        "shards": shards,
    }
    manifest_path = output / "input_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"records={len(selected)} within={within} "
        f"still_oversized={len(selected) - within} shards={len(shards)}"
    )


if __name__ == "__main__":
    main()
