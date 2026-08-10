#!/usr/bin/env python3
"""Reconcile primary, grounding-retry, and causal-recovery full-text outputs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.audit import sha256_file
from causal_multiomics_aging_review.v1 import (
    CAUSAL_DECISION_FIELDS,
    SCOPE_DECISION_FIELDS,
    agreement_audit,
    causal_status,
    derive_full_text_eligibility_route,
    scope_status,
)


def read_jsonl(paths: list[Path]) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def route_sequence(
    scope_runs: list[dict[str, Any]], causal_runs: list[dict[str, Any]]
) -> list[str]:
    sequence: list[str] = []
    for index, scope in enumerate(scope_runs):
        scope_route, scope_code = scope_status(scope)
        if scope_route == "exclude":
            sequence.append(f"exclude:{scope_code}")
        elif scope_route != "pass":
            sequence.append("manual_review:scope_unresolved")
        elif index >= len(causal_runs):
            sequence.append("manual_review:causal_not_run")
        else:
            causal_route, causal_code = causal_status(causal_runs[index])
            sequence.append(
                "assessed"
                if causal_route == "retain"
                else f"exclude:{causal_code}"
                if causal_route == "exclude"
                else "manual_review:causal_unresolved"
            )
    return sequence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("primary_run", type=Path)
    parser.add_argument("grounding_retry", type=Path)
    parser.add_argument("causal_recovery", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    primary_paths = sorted(
        (args.primary_run / "runs").glob("*/screening_results.jsonl")
    )
    primary = {row["record_id"]: row for row in read_jsonl(primary_paths)}
    retry_path = args.grounding_retry / "screening_results.jsonl"
    retries = {row["record_id"]: row for row in read_jsonl([retry_path])}
    recovery_path = args.causal_recovery / "causal_recovery_results.jsonl"
    recoveries = {row["record_id"]: row for row in read_jsonl([recovery_path])}

    if len(primary) != 97 or len(retries) != 2 or len(recoveries) != 14:
        raise SystemExit(
            f"Unexpected source counts: primary={len(primary)}, "
            f"retries={len(retries)}, recoveries={len(recoveries)}"
        )

    ledger: list[dict[str, Any]] = []
    for record_id, original in sorted(primary.items()):
        row = retries.get(record_id, original)
        roles = row.get("role_runs") or {}
        scope_runs = roles.get("scope_reviewer") or []
        causal_runs = roles.get("causal_method_reviewer") or []
        provenance = "grounding_retry" if record_id in retries else "primary"
        if record_id in recoveries:
            if record_id in retries:
                raise RuntimeError(f"Overlapping retry and recovery: {record_id}")
            causal_runs = recoveries[record_id]["causal_method_reviewer_runs"]
            provenance = "primary_scope_plus_causal_recovery"

        route = derive_full_text_eligibility_route(scope_runs, causal_runs, 5)
        scope_audit = agreement_audit(
            scope_runs, (*SCOPE_DECISION_FIELDS, "layer_candidates")
        )
        causal_audit = (
            agreement_audit(causal_runs, CAUSAL_DECISION_FIELDS)
            if causal_runs
            else {}
        )
        sequence = route_sequence(scope_runs, causal_runs)
        disagreement_fields = [
            f"scope_reviewer.{field}"
            for field, audit in scope_audit.items()
            if not audit["unanimous"]
        ] + [
            f"causal_method_reviewer.{field}"
            for field, audit in causal_audit.items()
            if not audit["unanimous"]
        ]
        ledger.append(
            {
                "record_id": record_id,
                "title": row.get("title", ""),
                "provenance": provenance,
                "final_decision": route["final_decision"],
                "final_exclusion_code": route["final_exclusion_code"],
                "decision_reason": route["decision_reason"],
                "five_request_route_exact": len(sequence) == 5
                and len(set(sequence)) == 1,
                "five_request_route_sequence": json.dumps(sequence),
                "all_tracked_fields_exact": not disagreement_fields,
                "disagreement_fields": ";".join(disagreement_fields),
            }
        )

    counts = Counter(row["final_decision"] for row in ledger)
    provenance_counts = Counter(row["provenance"] for row in ledger)
    summary = {
        "status": "reconciled_v1.5.1_rc1_full_text_eligibility",
        "records": len(ledger),
        "decision_counts": dict(sorted(counts.items())),
        "provenance_counts": dict(sorted(provenance_counts.items())),
        "five_request_route_exact_records": sum(
            row["five_request_route_exact"] for row in ledger
        ),
        "all_tracked_fields_exact_records": sum(
            row["all_tracked_fields_exact"] for row in ledger
        ),
        "source_files": {
            **{str(path): sha256_file(path) for path in primary_paths},
            str(retry_path): sha256_file(retry_path),
            str(recovery_path): sha256_file(recovery_path),
        },
        "interpretation": (
            "This ledger applies v1.5.1 route rules without changing stored model "
            "judgments. It substitutes two documented grounding retries and adds "
            "only the 14 causal roles skipped by the rejected routing implementation."
        ),
    }

    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "eligibility_ledger.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(ledger[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(ledger)
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    prisma = {
        "stage": "full_text_eligibility_screening",
        "reports_assessed_by_model_pipeline": len(ledger),
        "reports_with_unanimous_positive_route": counts["assessed"],
        "reports_with_unanimous_exclusion": counts["exclude"],
        "reports_pending_human_adjudication": counts["manual_review"],
        "status": "provisional_pending_expert_validation_and_evidence_extraction",
    }
    (args.output / "prisma_provisional.json").write_text(
        json.dumps(prisma, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
