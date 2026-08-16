#!/usr/bin/env python3
"""Finalize the frozen full-text eligibility ledger and PRISMA flow."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.audit import sha256_file

ELIGIBILITY_FIELDS = (
    "record_id",
    "doi",
    "title",
    "full_text_retrieval_status",
    "original_model_decision",
    "original_model_exclusion_code",
    "amended_decision",
    "amended_exclusion_code",
    "amended_reason",
    "route_changed_by_python_amendment",
    "human_adjudication_applied",
    "human_reviewer_id",
    "human_decision",
    "human_exclusion_code",
    "human_rationale",
    "supporting_section_ids",
    "final_decision",
    "final_exclusion_code",
    "final_decision_source",
    "final_decision_reason",
    "prisma_disposition",
    "protocol_disposition_code",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=ELIGIBILITY_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def doi_audit(rows: list[dict[str, str]]) -> dict[str, int]:
    dois = [row["doi"].strip().lower() for row in rows if row["doi"].strip()]
    counts = Counter(dois)
    return {
        "records": len(rows),
        "records_with_doi": len(dois),
        "unique_normalized_doi": len(counts),
        "duplicate_normalized_doi": sum(count - 1 for count in counts.values()),
        "records_without_doi": len(rows) - len(dois),
    }


def build_eligibility_ledger(
    routing_rows: list[dict[str, str]],
    human_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    routing_ids = [row["record_id"] for row in routing_rows]
    if len(routing_ids) != len(set(routing_ids)):
        raise ValueError("Routing ledger contains duplicate record_id values")

    human_by_id = {row["record_id"]: row for row in human_rows}
    if len(human_by_id) != len(human_rows):
        raise ValueError("Human adjudication ledger contains duplicate record_id values")

    pending_ids = {
        row["record_id"]
        for row in routing_rows
        if row["amended_decision"] == "manual_review"
    }
    if set(human_by_id) != pending_ids:
        raise ValueError(
            "Confirmed human decisions must exactly cover amended manual-review records: "
            f"expected={sorted(pending_ids)}, supplied={sorted(human_by_id)}"
        )

    final_rows: list[dict[str, str]] = []
    for source in sorted(routing_rows, key=lambda row: row["record_id"]):
        human = human_by_id.get(source["record_id"])
        if human:
            if human["adjudication_status"] != "confirmed":
                raise ValueError(f"Unconfirmed adjudication for {source['record_id']}")
            if human["doi"] != source["doi"] or human["title"] != source["title"]:
                raise ValueError(f"Adjudication metadata mismatch for {source['record_id']}")
            final_decision = human["human_decision"]
            final_code = human["first_failed_criterion"] or "none"
            decision_source = "human_adjudication"
            decision_reason = human["human_rationale"]
        else:
            final_decision = source["amended_decision"]
            final_code = source["amended_exclusion_code"] or "none"
            changed = source["route_changed"].strip().lower() == "true"
            decision_source = (
                "deterministic_python_amendment"
                if changed
                else "ai_five_run_route"
            )
            decision_reason = source["amended_reason"]

        if final_decision not in {"assessed", "exclude"}:
            raise ValueError(
                f"Final adjudication remains unresolved for {source['record_id']}: "
                f"{final_decision}"
            )
        if final_decision == "exclude" and final_code not in {
            "EC1",
            "EC2",
            "EC3",
            "EC4",
            "EC5",
        }:
            raise ValueError(f"Invalid exclusion code for {source['record_id']}: {final_code}")
        if final_decision == "assessed" and final_code != "none":
            raise ValueError(f"Eligible report has an exclusion code: {source['record_id']}")

        final_rows.append(
            {
                "record_id": source["record_id"],
                "doi": source["doi"],
                "title": source["title"],
                "full_text_retrieval_status": "retrieved",
                "original_model_decision": source["original_decision"],
                "original_model_exclusion_code": source["original_exclusion_code"],
                "amended_decision": source["amended_decision"],
                "amended_exclusion_code": source["amended_exclusion_code"],
                "amended_reason": source["amended_reason"],
                "route_changed_by_python_amendment": source["route_changed"].lower(),
                "human_adjudication_applied": str(bool(human)).lower(),
                "human_reviewer_id": human["human_reviewer_id"] if human else "",
                "human_decision": human["human_decision"] if human else "",
                "human_exclusion_code": human["first_failed_criterion"] if human else "",
                "human_rationale": human["human_rationale"] if human else "",
                "supporting_section_ids": human["supporting_section_ids"] if human else "",
                "final_decision": final_decision,
                "final_exclusion_code": final_code,
                "final_decision_source": decision_source,
                "final_decision_reason": decision_reason,
                "prisma_disposition": (
                    "meets_full_text_eligibility"
                    if final_decision == "assessed"
                    else "excluded_after_full_text_assessment"
                ),
                "protocol_disposition_code": final_code,
            }
        )
    return final_rows


def build_report_disposition(
    eligibility_rows: list[dict[str, str]],
    retrieval_rows: list[dict[str, Any]],
) -> list[dict[str, str]]:
    unresolved = [row for row in retrieval_rows if row.get("status") == "unresolved"]
    unresolved_ids = [str(row["record_id"]) for row in unresolved]
    if len(unresolved_ids) != len(set(unresolved_ids)):
        raise ValueError("Unresolved retrieval manifest contains duplicate record_id values")
    overlap = set(unresolved_ids) & {row["record_id"] for row in eligibility_rows}
    if overlap:
        raise ValueError(f"Unretrieved reports also occur in eligibility ledger: {sorted(overlap)}")

    rows = [dict(row) for row in eligibility_rows]
    for source in sorted(unresolved, key=lambda row: str(row["record_id"])):
        rows.append(
            {
                "record_id": str(source["record_id"]),
                "doi": str(source.get("doi") or ""),
                "title": str(source.get("title") or ""),
                "full_text_retrieval_status": "not_retrieved",
                "original_model_decision": "",
                "original_model_exclusion_code": "",
                "amended_decision": "",
                "amended_exclusion_code": "",
                "amended_reason": "",
                "route_changed_by_python_amendment": "false",
                "human_adjudication_applied": "false",
                "human_reviewer_id": "",
                "human_decision": "",
                "human_exclusion_code": "",
                "human_rationale": "",
                "supporting_section_ids": "",
                "final_decision": "not_assessed",
                "final_exclusion_code": "none",
                "final_decision_source": "retrieval_audit",
                "final_decision_reason": str(source.get("decision_note") or ""),
                "prisma_disposition": "report_not_retrieved",
                "protocol_disposition_code": "EC7",
            }
        )
    return sorted(rows, key=lambda row: row["record_id"])


def finalize(
    routing_path: Path,
    human_path: Path,
    retrieval_manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    eligibility_rows = build_eligibility_ledger(
        read_csv(routing_path),
        read_csv(human_path),
    )
    disposition_rows = build_report_disposition(
        eligibility_rows,
        read_jsonl(retrieval_manifest_path),
    )

    eligibility_doi = doi_audit(eligibility_rows)
    disposition_doi = doi_audit(disposition_rows)
    if eligibility_doi["duplicate_normalized_doi"] != 0:
        raise ValueError("Eligibility ledger contains duplicate DOI values")
    if disposition_doi["duplicate_normalized_doi"] != 0:
        raise ValueError("Report disposition ledger contains duplicate DOI values")

    decision_counts = Counter(row["final_decision"] for row in eligibility_rows)
    exclusion_counts = Counter(
        row["final_exclusion_code"]
        for row in eligibility_rows
        if row["final_decision"] == "exclude"
    )
    source_counts = Counter(row["final_decision_source"] for row in eligibility_rows)
    retrieval_counts = Counter(row["prisma_disposition"] for row in disposition_rows)

    reports_sought = len(disposition_rows)
    reports_not_retrieved = retrieval_counts["report_not_retrieved"]
    reports_assessed = len(eligibility_rows)
    reports_excluded = decision_counts["exclude"]
    reports_eligible = decision_counts["assessed"]
    arithmetic_checks = {
        "retrieval_balance": reports_sought == reports_not_retrieved + reports_assessed,
        "eligibility_balance": reports_assessed == reports_excluded + reports_eligible,
        "no_pending_eligibility_decisions": all(
            row["final_decision"] in {"assessed", "exclude"} for row in eligibility_rows
        ),
        "unique_doi_in_eligibility_ledger": eligibility_doi["duplicate_normalized_doi"] == 0,
        "unique_doi_in_report_disposition": disposition_doi["duplicate_normalized_doi"] == 0,
    }
    if not all(arithmetic_checks.values()):
        raise ValueError(f"Final flow integrity check failed: {arithmetic_checks}")

    output_dir.mkdir(parents=True, exist_ok=True)
    eligibility_path = output_dir / "final_eligibility_ledger_158.csv"
    disposition_path = output_dir / "report_disposition_162.csv"
    write_csv(eligibility_path, eligibility_rows)
    write_csv(disposition_path, disposition_rows)

    flow = {
        "schema_version": "1.0.0",
        "stage": "full_text_retrieval_and_eligibility",
        "scope": "frozen_162_report_full_text_candidate_cohort",
        "status": "final_for_frozen_full_text_candidate_cohort",
        "flow": {
            "reports_sought_for_retrieval": reports_sought,
            "reports_not_retrieved": reports_not_retrieved,
            "reports_assessed_for_eligibility": reports_assessed,
            "reports_excluded_after_full_text_assessment": reports_excluded,
            "reports_meeting_full_text_eligibility": reports_eligible,
            "reports_advanced_to_causal_evidence_extraction": reports_eligible,
            "reports_pending_eligibility_adjudication": 0,
        },
        "full_text_exclusion_reasons": dict(sorted(exclusion_counts.items())),
        "decision_provenance": dict(sorted(source_counts.items())),
        "doi_audit": {
            "eligibility_ledger": eligibility_doi,
            "report_disposition": disposition_doi,
        },
        "integrity": arithmetic_checks,
        "interpretation": {
            "eligible_reports_are_not_yet_final_synthesis_inclusions": True,
            "next_stage": "causal_evidence_extraction_and_python_level_assignment",
            "overall_review_prisma_status": "provisional_upstream_title_abstract_work_incomplete",
        },
        "notes": [
            (
                "EC7 is retained as an internal protocol disposition for the four reports "
                "not retrieved; these reports are not counted among exclusions after "
                "full-text assessment."
            ),
            (
                "The 101 eligible reports advance to causal evidence extraction and are "
                "not yet final Level 2-4 synthesis inclusions."
            ),
            (
                "This flow is final only for the frozen 162-report full-text candidate "
                "cohort; the overall review PRISMA flow remains provisional because "
                "upstream title/abstract processing is not fully resolved."
            ),
        ],
    }
    flow_path = output_dir / "prisma_full_text_flow.json"
    flow_path.write_text(
        json.dumps(flow, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    reason_lines = "\n".join(
        f"| {code} | {count} |" for code, count in sorted(exclusion_counts.items())
    )
    flow_markdown_path = output_dir / "prisma_full_text_flow.md"
    flow_markdown_path.write_text(
        "# Frozen full-text PRISMA flow\n\n"
        "Status: final for the frozen 162-report full-text candidate cohort.\n\n"
        "```mermaid\n"
        "flowchart TD\n"
        f'  A["Reports sought for retrieval (n={reports_sought})"] --> '
        f'B["Reports not retrieved (n={reports_not_retrieved})"]\n'
        f'  A --> C["Reports assessed for eligibility (n={reports_assessed})"]\n'
        f'  C --> D["Reports excluded (n={reports_excluded})"]\n'
        f'  C --> E["Reports meeting full-text eligibility (n={reports_eligible})"]\n'
        f'  E --> F["Advance to causal evidence extraction (n={reports_eligible})"]\n'
        "```\n\n"
        "## Exclusion reasons\n\n"
        "| First failed criterion | Reports |\n"
        "|---|---:|\n"
        f"{reason_lines}\n\n"
        "The four reports not retrieved carry internal protocol disposition EC7, but are "
        "not counted among reports excluded after full-text assessment. The 101 reports "
        "meeting eligibility are candidates for causal evidence extraction, not yet final "
        "Level 2-4 synthesis inclusions.\n\n"
        "The overall review PRISMA flow remains provisional because upstream "
        "title/abstract processing is not fully resolved.\n",
        encoding="utf-8",
    )

    summary = {
        "status": flow["status"],
        "records": {
            "reports_sought": reports_sought,
            "reports_assessed": reports_assessed,
            "reports_not_retrieved": reports_not_retrieved,
            "reports_meeting_eligibility": reports_eligible,
            "reports_excluded": reports_excluded,
            "reports_pending": 0,
        },
        "decision_counts": dict(sorted(decision_counts.items())),
        "exclusion_code_counts": dict(sorted(exclusion_counts.items())),
        "decision_source_counts": dict(sorted(source_counts.items())),
        "source_artifacts": {
            "routing_ledger": str(routing_path),
            "routing_ledger_sha256": sha256_file(routing_path),
            "human_adjudications": str(human_path),
            "human_adjudications_sha256": sha256_file(human_path),
            "retrieval_manifest": str(retrieval_manifest_path),
            "retrieval_manifest_sha256": sha256_file(retrieval_manifest_path),
        },
        "output_artifacts": {
            "eligibility_ledger": str(eligibility_path),
            "eligibility_ledger_sha256": sha256_file(eligibility_path),
            "report_disposition": str(disposition_path),
            "report_disposition_sha256": sha256_file(disposition_path),
            "prisma_full_text_flow": str(flow_path),
            "prisma_full_text_flow_sha256": sha256_file(flow_path),
            "prisma_full_text_flow_markdown": str(flow_markdown_path),
            "prisma_full_text_flow_markdown_sha256": sha256_file(flow_markdown_path),
        },
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        "# Final full-text eligibility v1.5.4\n\n"
        "This snapshot closes eligibility decisions for the frozen 162-report full-text "
        "candidate cohort. Of 162 reports sought, 4 were not retrieved, 158 were assessed, "
        "57 were excluded, and 101 met full-text eligibility. No eligibility adjudications "
        "remain pending.\n\n"
        "`final_eligibility_ledger_158.csv` overlays six confirmed human adjudications on "
        "the frozen AI and deterministic routing layers. `report_disposition_162.csv` adds "
        "the four reports not retrieved. `prisma_full_text_flow.json` contains the PRISMA "
        "counts, exclusion reasons, DOI audit, provenance counts, and arithmetic checks.\n\n"
        "The 101 eligible reports advance to causal evidence extraction. They are not yet "
        "final synthesis inclusions. The overall review PRISMA flow remains provisional "
        "until upstream title/abstract work is resolved.\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("routing_ledger", type=Path)
    parser.add_argument("human_adjudications", type=Path)
    parser.add_argument("retrieval_manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    summary = finalize(
        args.routing_ledger,
        args.human_adjudications,
        args.retrieval_manifest,
        args.output_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
