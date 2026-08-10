#!/usr/bin/env python3
"""Summarize repeated-call stability for shared-template full-text screening."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.v1 import causal_status, scope_status


def read_jsonl(paths: list[Path]) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    if total == 0:
        return [0.0, 0.0]
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(
        proportion * (1 - proportion) / total + z * z / (4 * total * total)
    ) / denominator
    return [max(0.0, center - margin), min(1.0, center + margin)]


def request_route_sequence(row: dict[str, Any]) -> list[str]:
    runs = row.get("role_runs", {})
    scopes = runs.get("scope_reviewer", [])
    causals = runs.get("causal_method_reviewer", [])
    sequence: list[str] = []
    for index, scope in enumerate(scopes):
        scope_route, scope_code = scope_status(scope)
        if scope_route == "exclude":
            sequence.append(f"exclude:{scope_code}")
        elif scope_route != "pass":
            sequence.append("manual_review:scope_unresolved")
        elif index >= len(causals):
            sequence.append("manual_review:causal_not_run")
        else:
            causal_route, causal_code = causal_status(causals[index])
            if causal_route == "retain":
                sequence.append("assessed")
            elif causal_route == "exclude":
                sequence.append(f"exclude:{causal_code}")
            else:
                sequence.append("manual_review:causal_unresolved")
    return sequence


def summarize(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    results = read_jsonl(sorted((root / "runs").glob("*/screening_results.jsonl")))
    attempts = read_jsonl(sorted((root / "runs").glob("*/raw_provider_responses.jsonl")))
    field_counts: dict[str, Counter[str]] = defaultdict(Counter)
    ledger: list[dict[str, Any]] = []
    exact_routes = 0
    exact_all_fields = 0
    exact_scope_fields = 0
    exact_causal_fields = 0

    for row in results:
        disagreements: list[str] = []
        role_exact: dict[str, bool] = {}
        for role, fields in row.get("role_agreement", {}).items():
            role_exact[role] = bool(fields) and all(
                audit["unanimous"] for audit in fields.values()
            )
            for field, audit in fields.items():
                key = f"{role}.{field}"
                field_counts[key]["evaluated"] += 1
                if audit["unanimous"]:
                    field_counts[key]["unanimous"] += 1
                else:
                    disagreements.append(key)
        scope_exact = role_exact.get("scope_reviewer", False)
        causal_evaluated = bool(
            row.get("role_runs", {}).get("causal_method_reviewer", [])
        )
        causal_exact = role_exact.get("causal_method_reviewer", False)
        all_fields_exact = scope_exact and (causal_exact if causal_evaluated else True)
        sequence = request_route_sequence(row)
        route_exact = len(sequence) == 5 and len(set(sequence)) == 1
        exact_routes += route_exact
        exact_scope_fields += scope_exact
        exact_causal_fields += causal_exact
        exact_all_fields += all_fields_exact
        ledger.append(
            {
                "record_id": row["record_id"],
                "title": row.get("title", ""),
                "final_decision": row["final_decision"],
                "final_exclusion_code": row.get("final_exclusion_code", "none"),
                "decision_reason": row.get("decision_reason", ""),
                "scope_all_fields_exact": scope_exact,
                "causal_evaluated": causal_evaluated,
                "causal_all_fields_exact": causal_exact,
                "all_evaluated_fields_exact": all_fields_exact,
                "five_request_route_sequence": json.dumps(sequence),
                "five_request_route_exact": route_exact,
                "disagreement_fields": ";".join(sorted(disagreements)),
            }
        )

    total = len(results)
    successful = sum(row.get("status") == "ok" for row in attempts)
    repairs = [
        repair
        for row in attempts
        for repair in row.get("post_validation", {}).get(
            "evidence_quote_repairs", []
        )
    ]
    summary = {
        "status": "complete_full_text_shared_template_stability_evaluation",
        "records": total,
        "strict_decision_counts": dict(
            Counter(row["final_decision"] for row in results)
        ),
        "strict_exclusion_code_counts": dict(
            Counter(
                row.get("final_exclusion_code", "none")
                for row in results
                if row["final_decision"] == "exclude"
            )
        ),
        "five_request_route_exact_records": exact_routes,
        "five_request_route_exact_rate": exact_routes / total if total else 0,
        "five_request_route_exact_wilson_95_ci": wilson(exact_routes, total),
        "scope_all_fields_exact_records": exact_scope_fields,
        "scope_all_fields_exact_rate": exact_scope_fields / total if total else 0,
        "causal_all_fields_exact_records": exact_causal_fields,
        "causal_evaluated_records": sum(row["causal_evaluated"] for row in ledger),
        "all_evaluated_fields_exact_records": exact_all_fields,
        "all_evaluated_fields_exact_rate": exact_all_fields / total if total else 0,
        "all_evaluated_fields_exact_wilson_95_ci": wilson(exact_all_fields, total),
        "model_attempts": len(attempts),
        "successful_attempts": successful,
        "failed_attempts_before_retry_or_manual_review": len(attempts) - successful,
        "schema_and_grounding_success_rate": successful / len(attempts) if attempts else 0,
        "deterministic_quote_repairs": len(repairs),
        "criterion_agreement": {
            key: {
                "evaluated_records": counts["evaluated"],
                "unanimous_records": counts["unanimous"],
                "unanimous_rate": counts["unanimous"] / counts["evaluated"],
                "wilson_95_ci": wilson(counts["unanimous"], counts["evaluated"]),
            }
            for key, counts in sorted(field_counts.items())
        },
        "interpretation": (
            "Each role used five independent Codex CLI requests over the same frozen "
            "deterministic evidence package. Python normalized unordered layer arrays "
            "and applied only consistency and routing rules. Any decision-field "
            "disagreement routes the record to manual review."
        ),
    }
    return summary, sorted(ledger, key=lambda row: row["record_id"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_root", type=Path)
    args = parser.parse_args()
    root = args.run_root.resolve()
    summary, ledger = summarize(root)
    (root / "stability_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if ledger:
        with (root / "stability_ledger.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(ledger[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(ledger)
    prisma = {
        "stage": "full_text_eligibility_screening",
        "run_status": summary["status"],
        "reports_assessed_by_model_pipeline": summary["records"],
        "reports_with_strict_unanimous_positive_assessment": summary[
            "strict_decision_counts"
        ].get("assessed", 0),
        "reports_with_strict_unanimous_exclusion": summary[
            "strict_decision_counts"
        ].get("exclude", 0),
        "reports_pending_human_adjudication": summary["strict_decision_counts"].get(
            "manual_review", 0
        ),
        "note": (
            "These are model-pipeline eligibility counts. Final PRISMA inclusion and "
            "exclusion counts require human adjudication and expert-gold validation."
        ),
    }
    (root / "prisma_full_text_screening.json").write_text(
        json.dumps(prisma, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
