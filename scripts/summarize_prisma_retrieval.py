#!/usr/bin/env python3
"""Build the PRISMA-aligned retrieval subflow for the frozen priority queue."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


RETRIEVED_STATUSES = {"downloaded_pdf", "downloaded_html", "downloaded_xml"}
VALID_DISPOSITIONS = {
    "excluded_before_report_retrieval",
    "report_not_retrieved",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def unique_by_doi(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        doi = str(row.get("doi", "")).strip().casefold()
        if not doi:
            raise ValueError(f"{label} contains a row without DOI")
        if doi in result:
            raise ValueError(f"{label} contains duplicate DOI: {doi}")
        result[doi] = row
    return result


def build_summary(dataset_dir: Path) -> dict[str, Any]:
    targets_path = dataset_dir / "targets.csv"
    manifest_path = dataset_dir / "retrieval_manifest.jsonl"
    retrieval_summary_path = dataset_dir / "summary.json"
    adjudication_path = dataset_dir / "retrieval_adjudication.csv"

    targets = unique_by_doi(read_csv(targets_path), "targets")
    manifest = unique_by_doi(read_jsonl(manifest_path), "manifest")
    adjudications = unique_by_doi(read_csv(adjudication_path), "adjudication")
    retrieval_summary = json.loads(retrieval_summary_path.read_text(encoding="utf-8"))

    if set(targets) != set(manifest):
        raise ValueError("Manifest DOI set does not match the frozen target set")

    retrieved = {
        doi for doi, row in manifest.items() if row.get("target_status") in RETRIEVED_STATUSES
    }
    unresolved = set(manifest) - retrieved
    if set(adjudications) != unresolved:
        missing = sorted(unresolved - set(adjudications))
        unexpected = sorted(set(adjudications) - unresolved)
        raise ValueError(
            f"Adjudication must classify every unresolved DOI exactly once; "
            f"missing={missing}, unexpected={unexpected}"
        )

    invalid_dispositions = sorted(
        {
            str(row.get("prisma_disposition", ""))
            for row in adjudications.values()
            if row.get("prisma_disposition") not in VALID_DISPOSITIONS
        }
    )
    if invalid_dispositions:
        raise ValueError(f"Invalid PRISMA dispositions: {invalid_dispositions}")

    excluded_before_retrieval = {
        doi
        for doi, row in adjudications.items()
        if row["prisma_disposition"] == "excluded_before_report_retrieval"
    }
    reports_not_retrieved = {
        doi
        for doi, row in adjudications.items()
        if row["prisma_disposition"] == "report_not_retrieved"
    }
    reports_sought = len(targets) - len(excluded_before_retrieval)
    if reports_sought != len(retrieved) + len(reports_not_retrieved):
        raise ValueError("PRISMA retrieval arithmetic does not balance")

    status_counts = Counter(str(row["target_status"]) for row in manifest.values())
    reason_counts = Counter(str(row["reason"]) for row in adjudications.values())
    preprints_outside_batch = int(retrieval_summary["excluded_preprints"])
    verification_dates = sorted(
        {str(row["verified_on"]) for row in adjudications.values() if row.get("verified_on")}
    )

    return {
        "schema_version": "1.0.0",
        "protocol_version": "1.1.2",
        "status": "priority_subset_retrieval_complete_full_text_assessment_pending",
        "scope": {
            "queue": str(retrieval_summary["queue"]),
            "is_final_review_prisma_denominator": False,
            "interpretation": (
                "Interim PRISMA-aligned retrieval subflow for the frozen priority-1 "
                "manual queue; records outside this queue remain unresolved upstream."
            ),
        },
        "flow": {
            "priority_queue_records": len(targets) + preprints_outside_batch,
            "preprints_outside_this_retrieval_batch": preprints_outside_batch,
            "nonpreprint_candidate_records_audited": len(targets),
            "records_excluded_before_report_retrieval": len(excluded_before_retrieval),
            "records_excluded_before_report_retrieval_reasons": {
                "abstract_only_report": reason_counts["abstract_only_report"]
            },
            "reports_sought_for_retrieval": reports_sought,
            "reports_not_retrieved": len(reports_not_retrieved),
            "reports_not_retrieved_reasons": {
                "publisher_access_controls": reason_counts["publisher_access_controls"]
            },
            "reports_retrieved_and_available_for_assessment": len(retrieved),
            "reports_assessed_for_eligibility": None,
            "full_text_assessment_status": "pending",
        },
        "retrieved_format_counts": {
            "pdf": status_counts["downloaded_pdf"],
            "html": status_counts["downloaded_html"],
            "xml": status_counts["downloaded_xml"],
        },
        "verification": {
            "publisher_access_audit_dates": verification_dates,
            "unresolved_records_classified": len(adjudications),
            "unclassified_unresolved_records": 0,
            "arithmetic_valid": True,
        },
        "source_artifacts": {
            "targets": str(targets_path),
            "retrieval_manifest": str(manifest_path),
            "retrieval_adjudication": str(adjudication_path),
            "targets_sha256": sha256_file(targets_path),
            "retrieval_manifest_sha256": sha256_file(manifest_path),
            "retrieval_adjudication_sha256": sha256_file(adjudication_path),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a validated PRISMA retrieval summary from frozen artifacts."
    )
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    output_path = args.output or args.dataset_dir / "prisma_retrieval.json"
    summary = build_summary(args.dataset_dir)
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary["flow"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
