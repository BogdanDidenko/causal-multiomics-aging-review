#!/usr/bin/env python3
"""Build the audited PRISMA follow-up record for the 20k abstract cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact(path: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(REPO)), "sha256": sha256(path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cohort-root",
        type=Path,
        default=REPO / "data/full_text/v1.1.2_oversized_20k_seek66",
    )
    parser.add_argument(
        "--graph-root",
        type=Path,
        default=(
            REPO
            / "data/full_text_graph/v1.1.0_oversized_20k_seek65_luna_light"
        ),
    )
    parser.add_argument("evaluation_root", type=Path)
    args = parser.parse_args()

    cohort_root = args.cohort_root.resolve()
    graph_root = args.graph_root.resolve()
    evaluation_root = args.evaluation_root.resolve()
    cohort_path = cohort_root / "cohort_manifest.json"
    retrieval_path = cohort_root / "summary.json"
    graph_path = graph_root / "run_summary.json"
    input_path = evaluation_root.parent / "input_manifest.json"
    orchestrator_path = evaluation_root / "orchestrator_manifest.json"
    stability_path = evaluation_root / "stability_summary.json"

    cohort = read_json(cohort_path)
    retrieval = read_json(retrieval_path)
    graph = read_json(graph_path)
    screening_input = read_json(input_path)
    orchestrator = read_json(orchestrator_path)
    stability = read_json(stability_path)

    reports = int(cohort["records"])
    retrieved = sum(
        int(count)
        for status, count in retrieval["status_counts"].items()
        if status.startswith("downloaded_")
    )
    not_retrieved = reports - retrieved
    decisions = stability["strict_decision_counts"]
    assessed = int(decisions.get("assessed", 0))
    excluded = int(decisions.get("exclude", 0))
    manual = int(decisions.get("manual_review", 0))

    checks = {
        "cohort_input_minus_collapsed_duplicate_equals_unique_reports": (
            int(cohort["input_records"]) - int(cohort["duplicate_records_collapsed"])
            == reports
        ),
        "retrieved_plus_not_retrieved_equals_reports_sought": (
            retrieved + not_retrieved == reports
        ),
        "graph_count_equals_retrieved_reports": (
            int(graph["documents_succeeded"]) == retrieved
        ),
        "screening_input_equals_graph_count": (
            int(screening_input["records"]) == retrieved
        ),
        "screening_output_equals_input": (
            int(orchestrator["result_records"]) == retrieved
            and int(stability["records"]) == retrieved
        ),
        "screening_routes_partition_assessed_reports": (
            assessed + excluded + manual == retrieved
        ),
    }
    if not all(checks.values()):
        raise SystemExit(f"PRISMA consistency checks failed: {checks}")

    result = {
        "schema_version": "1.0.0",
        "status": "followup_full_text_screening_complete_pending_expert_adjudication",
        "cohort": "oversized_abstract_20k_seek_full_text_followup",
        "flow": {
            "title_abstract_records_routed_to_followup": int(cohort["input_records"]),
            "duplicate_reports_collapsed_before_retrieval": int(
                cohort["duplicate_records_collapsed"]
            ),
            "reports_sought_for_retrieval": reports,
            "reports_not_retrieved": not_retrieved,
            "reports_retrieved_and_assessed": retrieved,
            "reports_with_unanimous_model_exclusion": excluded,
            "reports_with_unanimous_positive_model_assessment": assessed,
            "reports_pending_expert_adjudication": manual,
            "studies_included_in_synthesis": None,
        },
        "stability": {
            "five_run_route_exact_records": stability["five_request_route_exact_records"],
            "five_run_route_exact_rate": stability["five_request_route_exact_rate"],
            "all_evaluated_fields_exact_records": stability[
                "all_evaluated_fields_exact_records"
            ],
            "all_evaluated_fields_exact_rate": stability[
                "all_evaluated_fields_exact_rate"
            ],
            "model_attempts": stability["model_attempts"],
            "successful_final_role_runs": stability["successful_attempts"],
            "failed_attempts_recovered_by_retry": stability[
                "failed_attempts_before_retry_or_manual_review"
            ],
        },
        "model": {
            "name": orchestrator["model"],
            "reasoning_effort": orchestrator["reasoning_effort"],
            "repeats_per_role": orchestrator["repeats_per_role"],
            "suite_config": orchestrator["suite_config"],
            "suite_approval_status": orchestrator["suite_approval_status"],
        },
        "interpretation": (
            "Unanimous model routes are screening outputs, not expert-gold final "
            "eligibility decisions. Reports not retrieved are retrieval losses and "
            "must not be counted as scientific full-text exclusions."
        ),
        "consistency_checks": checks,
        "artifacts": {
            "cohort_manifest": artifact(cohort_path),
            "retrieval_summary": artifact(retrieval_path),
            "graph_run_summary": artifact(graph_path),
            "screening_input_manifest": artifact(input_path),
            "orchestrator_manifest": artifact(orchestrator_path),
            "stability_summary": artifact(stability_path),
        },
    }
    output = evaluation_root / "prisma_followup.json"
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
