#!/usr/bin/env python3
"""Audit a title/abstract failure retry and derive a provenance-safe replacement ledger."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value


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


def route_key(row: dict[str, Any]) -> str:
    decision = str(row.get("final_decision", "unknown"))
    reason = str(row.get("decision_reason") or row.get("manual_review_reason") or "none")
    return f"{decision}:{reason}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("retry_input_dir", type=Path)
    parser.add_argument("retry_runs", type=Path)
    parser.add_argument("primary_runs", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    manifest_path = args.retry_input_dir / "input_manifest.json"
    manifest = read_json(manifest_path)
    retry_files = sorted(args.retry_runs.glob("shard_*/screening_results.jsonl"))
    primary_files = sorted(args.primary_runs.glob("shard_*/screening_results.jsonl"))
    retry = [row for path in retry_files for row in read_jsonl(path)]
    primary = [row for path in primary_files for row in read_jsonl(path)]
    retry_by_id = {str(row["record_id"]): row for row in retry}
    primary_by_id = {str(row["record_id"]): row for row in primary}
    expected_ids = {
        row["record_id"]
        for row in csv.DictReader(
            (args.retry_input_dir / "failure_index.csv").open(encoding="utf-8", newline="")
        )
    }
    if len(retry_by_id) != len(retry):
        raise SystemExit("Duplicate record IDs in retry results")
    if set(retry_by_id) != expected_ids:
        raise SystemExit("Retry results do not exactly cover the frozen failure index")
    if not expected_ids <= primary_by_id.keys():
        raise SystemExit("Retry IDs are absent from primary results")
    invalid_primary = [
        identifier
        for identifier in expected_ids
        if primary_by_id[identifier].get("manual_review_reason") != "role_execution_failed"
    ]
    if invalid_primary:
        raise SystemExit("Replacement target includes non-execution failures")

    updated = dict(primary_by_id)
    updated.update(retry_by_id)
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / "retry_replacement_ledger.csv"
    fields = [
        "record_id",
        "title",
        "primary_decision",
        "primary_reason",
        "retry_decision",
        "retry_exclusion_code",
        "retry_reason",
        "retry_manual_review_reason",
        "retry_scope_runs",
        "retry_causal_runs",
    ]
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for identifier in sorted(expected_ids):
            old = primary_by_id[identifier]
            new = retry_by_id[identifier]
            role_runs = new.get("role_runs") or {}
            writer.writerow(
                {
                    "record_id": identifier,
                    "title": new.get("title", old.get("title", "")),
                    "primary_decision": old.get("final_decision", ""),
                    "primary_reason": old.get("manual_review_reason", ""),
                    "retry_decision": new.get("final_decision", ""),
                    "retry_exclusion_code": new.get("final_exclusion_code", ""),
                    "retry_reason": new.get("decision_reason", ""),
                    "retry_manual_review_reason": new.get("manual_review_reason", ""),
                    "retry_scope_runs": len(role_runs.get("scope_reviewer") or []),
                    "retry_causal_runs": len(role_runs.get("causal_method_reviewer") or []),
                }
            )

    primary_decisions = Counter(str(row.get("final_decision")) for row in primary)
    retry_decisions = Counter(str(row.get("final_decision")) for row in retry)
    updated_decisions = Counter(str(row.get("final_decision")) for row in updated.values())
    report = {
        "status": "complete",
        "interpretation": (
            "Derived replacement only: immutable primary outputs are preserved and retry "
            "results supersede exactly the frozen role_execution_failed IDs."
        ),
        "records": {
            "primary": len(primary),
            "frozen_retry": len(expected_ids),
            "retry_results": len(retry),
            "updated_derived_ledger": len(updated),
        },
        "retry": {
            "decision_counts": dict(sorted(retry_decisions.items())),
            "route_counts": dict(sorted(Counter(route_key(row) for row in retry).items())),
            "exclusion_code_counts": dict(
                sorted(
                    Counter(str(row.get("final_exclusion_code") or "none") for row in retry).items()
                )
            ),
            "remaining_role_execution_failures": sum(
                row.get("manual_review_reason") == "role_execution_failed" for row in retry
            ),
        },
        "before_after": {
            "primary_decision_counts": dict(sorted(primary_decisions.items())),
            "updated_decision_counts": dict(sorted(updated_decisions.items())),
            "primary_role_execution_failures": len(expected_ids),
            "updated_role_execution_failures": sum(
                row.get("manual_review_reason") == "role_execution_failed"
                for row in updated.values()
            ),
        },
        "provenance": {
            "retry_input_manifest": str(manifest_path),
            "retry_input_manifest_sha256": sha256(manifest_path),
            "retry_orchestrator_manifest": str(args.retry_runs / "orchestrator_manifest.json"),
            "retry_orchestrator_manifest_sha256": sha256(
                args.retry_runs / "orchestrator_manifest.json"
            ),
            "retry_result_files": [
                {"path": str(path), "sha256": sha256(path)} for path in retry_files
            ],
            "primary_result_files_match_frozen_manifest": all(
                sha256(Path(item["path"])) == item["sha256"]
                for item in manifest["primary_result_files"]
            ),
            "replacement_ledger": str(ledger_path),
            "replacement_ledger_sha256": sha256(ledger_path),
        },
    }
    report_path = output / "retry_summary.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"records={len(retry)} decisions={dict(retry_decisions)} "
        f"remaining_failures={report['retry']['remaining_role_execution_failures']}"
    )


if __name__ == "__main__":
    main()
