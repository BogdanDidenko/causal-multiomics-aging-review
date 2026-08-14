#!/usr/bin/env python3
"""Apply the v1.5.4 criterion short-circuit to frozen full-text outputs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.v1 import derive_full_text_eligibility_route


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    results: dict[str, dict[str, Any]] = {}
    for path in sorted(args.run_root.glob("runs/*/screening_results.jsonl")):
        for row in read_jsonl(path):
            results[str(row["record_id"])] = row

    ledger = []
    for identifier in sorted(results):
        original = results[identifier]
        role_runs = original.get("role_runs") or {}
        scope_runs = role_runs.get("scope_reviewer") or []
        causal_runs = role_runs.get("causal_method_reviewer") or []
        if len(scope_runs) == 5:
            amended = derive_full_text_eligibility_route(
                scope_runs,
                causal_runs,
                repeat_count=5,
                scope_exclusion_policy="unanimous_decisive_criterion",
            )
        else:
            amended = {
                "final_decision": original["final_decision"],
                "final_exclusion_code": original.get("final_exclusion_code", "none"),
                "decision_reason": original.get("decision_reason", ""),
                "manual_review_reason": original.get("manual_review_reason", ""),
            }
        ledger.append(
            {
                "record_id": identifier,
                "doi": identifier.removeprefix("doi:") if identifier.startswith("doi:") else "",
                "title": original.get("title", ""),
                "original_decision": original["final_decision"],
                "original_exclusion_code": original.get("final_exclusion_code", "none"),
                "amended_decision": amended["final_decision"],
                "amended_exclusion_code": amended["final_exclusion_code"],
                "amended_reason": amended["decision_reason"],
                "route_changed": original["final_decision"] != amended["final_decision"],
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = args.output_dir / "routing_ledger.csv"
    with ledger_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ledger[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(ledger)

    original_counts = Counter(row["original_decision"] for row in ledger)
    amended_counts = Counter(row["amended_decision"] for row in ledger)
    changed = [row for row in ledger if row["route_changed"]]
    summary = {
        "policy_version": "1.5.4-rc1",
        "model_rerun": False,
        "records": len(ledger),
        "original_decision_counts": dict(sorted(original_counts.items())),
        "amended_decision_counts": dict(sorted(amended_counts.items())),
        "changed_routes": len(changed),
        "changed_route_exclusion_codes": dict(
            sorted(Counter(row["amended_exclusion_code"] for row in changed).items())
        ),
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manual_path = args.output_dir / "remaining_manual_review_6.csv"
    manual = [row for row in ledger if row["amended_decision"] == "manual_review"]
    with manual_path.open("w", encoding="utf-8", newline="") as handle:
        fields = ("record_id", "doi", "title", "original_decision", "amended_reason")
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in manual)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
