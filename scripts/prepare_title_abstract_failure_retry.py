#!/usr/bin/env python3
"""Freeze a retry batch for title/abstract role-execution failures."""

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
    parser.add_argument("--shards", type=int, default=12)
    parser.add_argument("--expected-records", type=int, default=72)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    source_rows = read_csv(args.input)
    source_by_id = {row["record_id"]: row for row in source_rows}
    if len(source_by_id) != len(source_rows):
        raise SystemExit("Duplicate record IDs in screening input")

    result_files = sorted(args.primary_runs.glob("shard_*/screening_results.jsonl"))
    if not result_files:
        raise SystemExit("No primary screening result files found")
    primary_rows = [row for path in result_files for row in read_jsonl(path)]
    failed = [
        row
        for row in primary_rows
        if row.get("final_decision") == "manual_review"
        and row.get("manual_review_reason") == "role_execution_failed"
    ]
    failed_ids = {str(row["record_id"]) for row in failed}
    if len(failed_ids) != len(failed):
        raise SystemExit("Duplicate failed record IDs in primary results")
    if len(failed_ids) != args.expected_records:
        raise SystemExit(f"Expected {args.expected_records} role failures, found {len(failed_ids)}")
    missing = sorted(failed_ids - source_by_id.keys())
    if missing:
        raise SystemExit(f"Failed IDs absent from source input: {missing[:5]}")

    selected = [row for row in source_rows if row["record_id"] in failed_ids]
    fields = list(source_rows[0])
    output = args.output_dir
    input_path = output / "input.csv"
    empty_path = output / "missing_abstract.csv"
    write_csv(input_path, selected, fields)
    write_csv(empty_path, [], fields)

    shard_count = min(args.shards, len(selected))
    shards: list[dict[str, Any]] = []
    for index in range(shard_count):
        shard_rows = selected[index::shard_count]
        shard_path = output / "shards" / f"shard_{index + 1:02d}.csv"
        write_csv(shard_path, shard_rows, fields)
        shards.append(
            {
                "path": relative(shard_path.resolve(), root),
                "sha256": sha256(shard_path),
                "records": len(shard_rows),
            }
        )

    failure_index_path = output / "failure_index.csv"
    failure_rows = [
        {
            "record_id": str(row["record_id"]),
            "title": str(row.get("title", "")),
            "primary_manual_review_reason": str(row["manual_review_reason"]),
            "primary_failure_role": str((row.get("manual_review_details") or {}).get("role", "")),
            "primary_failure_errors": json.dumps(
                (row.get("manual_review_details") or {}).get("errors", []),
                ensure_ascii=False,
                sort_keys=True,
            ),
        }
        for row in sorted(failed, key=lambda item: str(item["record_id"]))
    ]
    write_csv(failure_index_path, failure_rows, list(failure_rows[0]))

    manifest = {
        "status": "frozen_title_abstract_role_execution_failure_retry",
        "retry_policy": (
            "fresh five-run evaluation of each failed record; primary outputs remain immutable"
        ),
        "expected_primary_failure_reason": "role_execution_failed",
        "expected_records": args.expected_records,
        "screening_input": {
            "path": relative(input_path.resolve(), root),
            "sha256": sha256(input_path),
            "records": len(selected),
        },
        "missing_abstract_queue": {
            "path": relative(empty_path.resolve(), root),
            "sha256": sha256(empty_path),
            "records": 0,
        },
        "failure_index": {
            "path": relative(failure_index_path.resolve(), root),
            "sha256": sha256(failure_index_path),
            "records": len(failure_rows),
        },
        "primary_screening_input": {
            "path": relative(args.input.resolve(), root),
            "sha256": sha256(args.input),
            "records": len(source_rows),
        },
        "primary_result_files": [
            {"path": relative(path.resolve(), root), "sha256": sha256(path)}
            for path in result_files
        ],
        "primary_result_records": len(primary_rows),
        "shards": shards,
    }
    manifest_path = output / "input_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"records={len(selected)} shards={len(shards)} manifest={manifest_path}")


if __name__ == "__main__":
    main()
