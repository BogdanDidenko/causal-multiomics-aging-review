from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.finalize_full_text_eligibility import finalize


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_finalize_overlays_human_decisions_and_separates_not_retrieved(
    tmp_path: Path,
) -> None:
    routing_path = tmp_path / "routing.csv"
    write_csv(
        routing_path,
        [
            {
                "record_id": "doi:10.1/a",
                "doi": "10.1/a",
                "title": "Eligible",
                "original_decision": "assessed",
                "original_exclusion_code": "none",
                "amended_decision": "assessed",
                "amended_exclusion_code": "none",
                "amended_reason": "five_of_five_positive",
                "route_changed": "False",
            },
            {
                "record_id": "doi:10.1/b",
                "doi": "10.1/b",
                "title": "Human exclusion",
                "original_decision": "manual_review",
                "original_exclusion_code": "none",
                "amended_decision": "manual_review",
                "amended_exclusion_code": "none",
                "amended_reason": "",
                "route_changed": "False",
            },
            {
                "record_id": "doi:10.1/c",
                "doi": "10.1/c",
                "title": "Rule exclusion",
                "original_decision": "manual_review",
                "original_exclusion_code": "none",
                "amended_decision": "exclude",
                "amended_exclusion_code": "EC4",
                "amended_reason": "unanimous_decisive_criterion_failure",
                "route_changed": "True",
            },
        ],
    )
    human_path = tmp_path / "human.csv"
    write_csv(
        human_path,
        [
            {
                "record_id": "doi:10.1/b",
                "doi": "10.1/b",
                "title": "Human exclusion",
                "human_reviewer_id": "reviewer",
                "human_decision": "exclude",
                "first_failed_criterion": "EC1",
                "human_rationale": "Not a primary report.",
                "supporting_section_ids": "chunk:0001",
                "adjudication_status": "confirmed",
            }
        ],
    )
    retrieval_path = tmp_path / "retrieval.jsonl"
    retrieval_path.write_text(
        json.dumps(
            {
                "record_id": "doi:10.1/d",
                "doi": "10.1/d",
                "title": "Unavailable",
                "status": "unresolved",
                "decision_note": "No legal full target content found.",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    summary = finalize(routing_path, human_path, retrieval_path, tmp_path / "out")

    assert summary["records"] == {
        "reports_sought": 4,
        "reports_assessed": 3,
        "reports_not_retrieved": 1,
        "reports_meeting_eligibility": 1,
        "reports_excluded": 2,
        "reports_pending": 0,
    }
    assert summary["decision_source_counts"] == {
        "ai_five_run_route": 1,
        "deterministic_python_amendment": 1,
        "human_adjudication": 1,
    }
    flow = json.loads((tmp_path / "out/prisma_full_text_flow.json").read_text())
    assert flow["integrity"] == {
        "eligibility_balance": True,
        "no_pending_eligibility_decisions": True,
        "retrieval_balance": True,
        "unique_doi_in_eligibility_ledger": True,
        "unique_doi_in_report_disposition": True,
    }
    with (tmp_path / "out/report_disposition_162.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        dispositions = list(csv.DictReader(handle))
    unavailable = next(row for row in dispositions if row["record_id"] == "doi:10.1/d")
    assert unavailable["prisma_disposition"] == "report_not_retrieved"
    assert unavailable["protocol_disposition_code"] == "EC7"
    assert unavailable["final_exclusion_code"] == "none"
