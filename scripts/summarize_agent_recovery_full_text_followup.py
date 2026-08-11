#!/usr/bin/env python3
"""Build the final retrieval-plus-model-screening PRISMA follow-up snapshot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
FIRST_EVALUATION = REPO / (
    "data/full_text_screening/v1.1.0_oversized_20k_seek65_graph_chunks/"
    "evaluation_v1.5.2-rc1"
)
RECOVERY_EVALUATION = REPO / (
    "data/full_text_screening/v1.2.1_agent_recovery17_graph_chunks/"
    "evaluation_v1.5.2-rc1"
)
RECOVERY_ROOT = REPO / "data/full_text/v1.1.2_oversized_20k_seek66/agent_recovery"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def artifact(path: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(REPO)), "sha256": sha256_file(path)}


def build() -> dict[str, Any]:
    retrieval = load(RECOVERY_ROOT / "prisma_recovery_addendum.json")
    first = load(FIRST_EVALUATION / "stability_summary.json")
    recovery = load(RECOVERY_EVALUATION / "stability_summary.json")
    with (REPO / "protocol/full_text/oversized_20k_agent_recovery_selection.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        selection = list(csv.DictReader(handle))
    unavailable = [row for row in selection if row["report_form"] == "unavailable"]

    sought = int(retrieval["flow"]["reports_sought_for_retrieval"])
    retrieved = int(retrieval["flow"]["reports_retrieved_after_agent_recovery"])
    not_retrieved = int(retrieval["flow"]["reports_not_retrieved_after_agent_recovery"])
    first_records = int(first["records"])
    recovery_records = int(recovery["records"])
    strict_exclusions = int(first["strict_decision_counts"]["exclude"]) + int(
        recovery["strict_decision_counts"]["exclude"]
    )
    strict_assessed = int(first["strict_decision_counts"]["assessed"]) + int(
        recovery["strict_decision_counts"]["assessed"]
    )
    pending = int(first["strict_decision_counts"]["manual_review"]) + int(
        recovery["strict_decision_counts"]["manual_review"]
    )

    assert sought == retrieved + not_retrieved
    assert not_retrieved == len(unavailable) == 4
    assert retrieved == first_records + recovery_records == 61
    assert retrieved == strict_exclusions + strict_assessed + pending

    return {
        "schema_version": "1.0.0",
        "status": "retrieval_and_model_screening_complete_pending_expert_adjudication",
        "cohort": "oversized_abstract_20k_seek_full_text_followup",
        "flow": {
            "title_abstract_records_routed_to_followup": 66,
            "duplicate_reports_collapsed_before_retrieval": 1,
            "reports_sought_for_retrieval": sought,
            "reports_retrieved": retrieved,
            "reports_not_retrieved": not_retrieved,
            "reports_assessed_by_model_pipeline": retrieved,
            "reports_with_unanimous_model_exclusion": strict_exclusions,
            "reports_with_unanimous_positive_model_assessment": strict_assessed,
            "reports_pending_expert_adjudication": pending,
            "studies_included_in_synthesis": None,
        },
        "not_retrieved_reports": [
            {
                "doi": row["target_doi"],
                "reason": row["decision_note"],
                "prisma_classification": "report_not_retrieved",
            }
            for row in unavailable
        ],
        "screening_batches": {
            "initial_retrieved_44": first["strict_decision_counts"],
            "agent_recovered_17": recovery["strict_decision_counts"],
        },
        "recovery_batch_stability": {
            "records": recovery_records,
            "five_request_route_exact_records": recovery["five_request_route_exact_records"],
            "five_request_route_exact_rate": recovery["five_request_route_exact_rate"],
            "all_evaluated_fields_exact_records": recovery[
                "all_evaluated_fields_exact_records"
            ],
            "all_evaluated_fields_exact_rate": recovery["all_evaluated_fields_exact_rate"],
            "schema_and_grounding_success_rate": recovery[
                "schema_and_grounding_success_rate"
            ],
            "technical_role_execution_failures": 1,
            "technical_failure_record_id": "doi:10.1002/alz.12278",
        },
        "interpretation": (
            "The four unavailable reports are retrieval losses, not scientific exclusions. "
            "Unanimous model routes are provisional screening outputs; final PRISMA eligibility "
            "and synthesis counts require expert adjudication."
        ),
        "artifacts": {
            "retrieval_addendum": artifact(
                RECOVERY_ROOT / "prisma_recovery_addendum.json"
            ),
            "recovery_selection": artifact(
                REPO / "protocol/full_text/oversized_20k_agent_recovery_selection.csv"
            ),
            "initial_stability_summary": artifact(
                FIRST_EVALUATION / "stability_summary.json"
            ),
            "recovery_stability_summary": artifact(
                RECOVERY_EVALUATION / "stability_summary.json"
            ),
            "recovery_screening_input": artifact(
                REPO
                / "data/full_text_screening/v1.2.1_agent_recovery17_graph_chunks/"
                "input_manifest.json"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=RECOVERY_EVALUATION / "prisma_followup_complete.json",
    )
    args = parser.parse_args()
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["flow"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
