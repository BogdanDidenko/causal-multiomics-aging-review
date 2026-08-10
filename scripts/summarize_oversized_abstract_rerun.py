#!/usr/bin/env python3
"""Audit and reconcile the 20,000-character oversized-abstract rerun."""

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


def read_jsonl_files(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("rerun_dir", type=Path)
    parser.add_argument("primary_runs", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    with (args.input_dir / "oversized_index.csv").open(encoding="utf-8", newline="") as handle:
        index = list(csv.DictReader(handle))
    expected_ids = {row["record_id"] for row in index}
    result_files = sorted(args.rerun_dir.glob("shard_*/screening_results.jsonl"))
    rerun = read_jsonl_files(result_files)
    rerun_by_id = {str(row["record_id"]): row for row in rerun}
    if len(rerun_by_id) != len(rerun) or set(rerun_by_id) != expected_ids:
        raise SystemExit("Rerun results do not exactly cover the frozen oversized index")

    primary_files = sorted(args.primary_runs.glob("shard_*/screening_results.jsonl"))
    primary = read_jsonl_files(primary_files)
    primary_by_id = {str(row["record_id"]): row for row in primary}
    invalid = [
        identifier
        for identifier in expected_ids
        if primary_by_id[identifier].get("decision_reason") != "oversized_abstract_metadata"
    ]
    if invalid:
        raise SystemExit("Replacement target contains non-oversized primary records")

    updated = dict(primary_by_id)
    updated.update(rerun_by_id)
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    ledger_path = output / "oversized_rerun_ledger.csv"
    fields = [
        "record_id",
        "doi",
        "title",
        "abstract_chars",
        "within_20000",
        "rerun_decision",
        "rerun_exclusion_code",
        "rerun_reason",
        "rerun_manual_review_reason",
        "scope_runs",
        "causal_runs",
    ]
    index_by_id = {row["record_id"]: row for row in index}
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for identifier in sorted(expected_ids):
            row = rerun_by_id[identifier]
            runs = row.get("role_runs") or {}
            metadata = index_by_id[identifier]
            writer.writerow(
                {
                    "record_id": identifier,
                    "doi": metadata["doi"],
                    "title": row.get("title", metadata["title"]),
                    "abstract_chars": metadata["abstract_chars"],
                    "within_20000": metadata["within_new_maximum"],
                    "rerun_decision": row.get("final_decision", ""),
                    "rerun_exclusion_code": row.get("final_exclusion_code", ""),
                    "rerun_reason": row.get("decision_reason", ""),
                    "rerun_manual_review_reason": row.get("manual_review_reason", ""),
                    "scope_runs": len(runs.get("scope_reviewer") or []),
                    "causal_runs": len(runs.get("causal_method_reviewer") or []),
                }
            )

    orchestrator_path = args.rerun_dir / "orchestrator_manifest.json"
    orchestrator = json.loads(orchestrator_path.read_text(encoding="utf-8"))
    retry_decisions = Counter(str(row.get("final_decision")) for row in rerun)
    report = {
        "status": "complete",
        "records": {
            "frozen_oversized": len(index),
            "within_20000": sum(row["within_new_maximum"] == "True" for row in index),
            "still_over_20000": sum(row["within_new_maximum"] != "True" for row in index),
            "rerun_results": len(rerun),
        },
        "rerun": {
            "decision_counts": dict(sorted(retry_decisions.items())),
            "reason_counts": dict(
                sorted(
                    Counter(
                        str(row.get("decision_reason") or row.get("manual_review_reason") or "none")
                        for row in rerun
                    ).items()
                )
            ),
            "remaining_oversized": sum(
                row.get("decision_reason") == "oversized_abstract_metadata" for row in rerun
            ),
            "role_execution_failures": sum(
                row.get("manual_review_reason") == "role_execution_failed" for row in rerun
            ),
        },
        "corpus_before_after": {
            "before": dict(
                sorted(Counter(str(row.get("final_decision")) for row in primary).items())
            ),
            "after": dict(
                sorted(Counter(str(row.get("final_decision")) for row in updated.values()).items())
            ),
        },
        "runtime": {
            key: orchestrator.get(key)
            for key in (
                "git_revision",
                "model",
                "reasoning_effort",
                "repeats",
                "suite_version",
                "suite_config_sha256",
                "workers",
                "started_at",
                "completed_at",
            )
        },
        "provenance": {
            "input_manifest": str(args.input_dir / "input_manifest.json"),
            "input_manifest_sha256": sha256(args.input_dir / "input_manifest.json"),
            "orchestrator_manifest": str(orchestrator_path),
            "orchestrator_manifest_sha256": sha256(orchestrator_path),
            "result_files": [{"path": str(path), "sha256": sha256(path)} for path in result_files],
            "ledger": str(ledger_path),
            "ledger_sha256": sha256(ledger_path),
        },
    }
    report_path = output / "oversized_rerun_summary.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"records={len(rerun)} decisions={dict(retry_decisions)} "
        f"still_oversized={report['rerun']['remaining_oversized']} "
        f"role_failures={report['rerun']['role_execution_failures']}"
    )


if __name__ == "__main__":
    main()
