#!/usr/bin/env python3
"""Create a deterministic candidate-triage audit from existing title/abstract logs.

This utility never invokes a model or changes raw model outputs. It applies the
criterion-path routing rule to saved five-run outputs and creates transparent
textual subsets for manual title/abstract review. These subsets are not
accuracy labels and must not be used to exclude records from the review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from causal_multiomics_aging_review.v1 import (
    CAUSAL_DECISION_FIELDS,
    SCOPE_DECISION_FIELDS,
    derive_title_result,
)

AGING_TITLE_ANCHOR = re.compile(
    r"\b(?:age(?:d|ing|ing-related)?|ageing|senescen\w*|longevity|lifespan|"
    r"healthspan|rejuvenat\w*|proger\w*|inflammaging|geroscience)\b",
    re.IGNORECASE,
)
POSITIVE_CAUSAL_BASES = {
    "named_causal_effect_design",
    "formal_directed_hypothesis",
    "causal_analysis_method_unspecified",
}
METADATA_RETAIN_REASONS = {
    "oversized_abstract_metadata",
    "conference_abstract_number_mismatch",
    "conference_abstract_body_fragment",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_fields(runs: list[dict[str, Any]], fields: tuple[str, ...]) -> bool:
    return len(runs) == 5 and all(
        len({json.dumps(run.get(field), sort_keys=True) for run in runs}) == 1
        for field in fields
    )


def primary_anchor(causal_runs: list[dict[str, Any]]) -> str:
    if not causal_runs:
        return "not_assessed"
    families = causal_runs[0].get("design_families") or []
    return str(families[0]) if families else "empty"


def stable_positive_candidate(result: dict[str, Any]) -> bool:
    roles = result.get("role_runs") or {}
    scope_runs = roles.get("scope_reviewer") or []
    causal_runs = roles.get("causal_method_reviewer") or []
    return (
        result.get("decision_reason") == "positive_causal_basis"
        and exact_fields(scope_runs, SCOPE_DECISION_FIELDS)
        and exact_fields(causal_runs, CAUSAL_DECISION_FIELDS)
        and all(run.get("causal_basis") in POSITIVE_CAUSAL_BASES for run in causal_runs)
    )


def textual_queue(result: dict[str, Any], source: dict[str, str]) -> str:
    """Assign a manual-review priority without adding a scientific eligibility rule."""
    if not stable_positive_candidate(result):
        return "retain_for_manual_title_abstract_adjudication"

    scope = result["role_runs"]["scope_reviewer"][0]
    title_has_aging_anchor = bool(AGING_TITLE_ANCHOR.search(source.get("title", "")))
    explicit_multiomics = scope.get("multiomics_evidence") == "explicit_multiomics"
    if title_has_aging_anchor and explicit_multiomics:
        return "priority_1_textually_focused"
    if title_has_aging_anchor:
        return "priority_2_aging_title"
    if explicit_multiomics:
        return "priority_3_explicit_multiomics"
    return "priority_4_broad_candidate"


def csv_row(
    result: dict[str, Any], source: dict[str, str], recomputed: dict[str, Any]
) -> dict[str, str]:
    roles = result.get("role_runs") or {}
    scope_runs = roles.get("scope_reviewer") or []
    causal_runs = roles.get("causal_method_reviewer") or []
    scope = scope_runs[0] if scope_runs else {}
    return {
        "record_id": str(result["record_id"]),
        "doi": source.get("doi", ""),
        "title": source.get("title", ""),
        "source": source.get("source", ""),
        "year": source.get("year", ""),
        "original_route": str(result.get("final_decision", "")),
        "original_reason": str(result.get("decision_reason", "")),
        "original_exclusion_code": str(result.get("final_exclusion_code", "none")),
        "criterion_path_route": str(recomputed.get("final_decision", "manual_review")),
        "criterion_path_reason": str(recomputed.get("decision_reason", "role_contract_failure")),
        "criterion_path_exclusion_code": str(
            recomputed.get("final_exclusion_code", "none")
        ),
        "manual_triage_queue": textual_queue(result, source),
        "design_anchor": primary_anchor(causal_runs),
        "multiomics_evidence": str(scope.get("multiomics_evidence", "not_assessed")),
        "aging_title_anchor": str(
            bool(AGING_TITLE_ANCHOR.search(source.get("title", "")))
        ).lower(),
        "scope_all_tracked_5_of_5": str(
            exact_fields(scope_runs, SCOPE_DECISION_FIELDS)
        ).lower(),
        "causal_all_tracked_5_of_5": str(
            exact_fields(causal_runs, CAUSAL_DECISION_FIELDS)
        ).lower(),
        "abstract": source.get("abstract", ""),
    }


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields = list(rows[0]) if rows else ["record_id"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("runs_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--reference-doi", default="10.1038/s41467-023-37729-w")
    args = parser.parse_args()

    inputs = {row["record_id"]: row for row in read_csv(args.input)}
    results: list[dict[str, Any]] = []
    for shard in sorted(args.runs_dir.glob("shard_*")):
        results.extend(read_jsonl(shard / "screening_results.jsonl"))

    rerouted: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for result in results:
        roles = result.get("role_runs") or {}
        scope_runs = roles.get("scope_reviewer") or []
        causal_runs = roles.get("causal_method_reviewer") or []
        recomputed = (
            {
                "final_decision": "seek_full_text",
                "decision_reason": result["decision_reason"],
            }
            if result.get("decision_reason") in METADATA_RETAIN_REASONS
            else
            derive_title_result(scope_runs, causal_runs or None)
            if scope_runs
            else {
                "final_decision": "manual_review",
                "decision_reason": result.get("manual_review_reason", "role_contract_failure"),
            }
        )
        rerouted.append((result, recomputed))

    rows = [
        csv_row(result, inputs[result["record_id"]], recomputed)
        for result, recomputed in rerouted
    ]
    candidates = [
        row
        for row in rows
        if row["original_reason"] == "positive_causal_basis"
        and row["criterion_path_route"] == "seek_full_text"
    ]
    queue_counts = Counter(row["manual_triage_queue"] for row in candidates)
    design_counts = Counter(
        row["design_anchor"]
        for row in candidates
        if row["manual_triage_queue"] == "priority_1_textually_focused"
    )
    original_routes = Counter(row["original_route"] for row in rows)
    criterion_routes = Counter(row["criterion_path_route"] for row in rows)
    criterion_exclusions = Counter(row["criterion_path_exclusion_code"] for row in rows)
    changed_route_rows = [
        row for row in rows if row["original_route"] != row["criterion_path_route"]
    ]
    changed_reasons = Counter(row["original_reason"] for row in changed_route_rows)
    reference = next(
        (row for row in rows if row["doi"].casefold() == args.reference_doi.casefold()),
        None,
    )

    report = {
        "status": "posthoc_log_localization_complete",
        "model_calls": 0,
        "interpretation": (
            "This is deterministic post-hoc routing and manual-triage support from "
            "saved outputs. It does not validate model accuracy, alter raw provider "
            "responses, or justify automatic exclusion from any priority subset."
        ),
        "routing_rule": {
            "name": "unanimous_first_failed_criterion",
            "description": (
                "Automatic exclusion requires five identical criterion-level exclusion "
                "paths; unrelated field drift does not override that path."
            ),
        },
        "records": {
            "input_results": len(rows),
            "original_route_counts": dict(sorted(original_routes.items())),
            "criterion_path_route_counts": dict(sorted(criterion_routes.items())),
            "criterion_path_exclusion_code_counts": dict(sorted(criterion_exclusions.items())),
            "records_changed_by_criterion_path_rerouting": len(changed_route_rows),
            "changed_route_original_reason_counts": dict(sorted(changed_reasons.items())),
        },
        "positive_causal_candidates": {
            "all_original_positive_routes": sum(
                row["original_reason"] == "positive_causal_basis" for row in rows
            ),
            "criterion_path_retained": len(candidates),
            "manual_triage_queue_counts": dict(sorted(queue_counts.items())),
            "priority_1_design_anchor_counts": dict(sorted(design_counts.items())),
        },
        "reference_record": reference,
        "artifacts": {
            "input": {"path": str(args.input), "sha256": sha256(args.input)},
            "runs_dir": str(args.runs_dir),
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "candidate_triage.csv", candidates)
    write_csv(args.output_dir / "criterion_path_route_changes.csv", changed_route_rows)
    (args.output_dir / "localization.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    queues = report["positive_causal_candidates"]["manual_triage_queue_counts"]
    route_counts = report["records"]["criterion_path_route_counts"]
    (args.output_dir / "README.md").write_text(
        "# Existing-Log Candidate Localization\n\n"
        "## What was done\n\n"
        "No model calls were made. This audit reuses the saved title/abstract text, "
        "five-run outputs, and evidence spans from the 2026-08-02 Terra run. Raw "
        "provider responses remain unchanged.\n\n"
        "## Deterministic routing correction\n\n"
        "The protocol requires five identical first-failed criterion paths for an "
        "automatic exclusion. The historic runner additionally required agreement on "
        "unrelated fields, retaining records whose decisive exclusion path was already "
        "unanimous. Applying the criterion-path rule changed "
        f"{len(changed_route_rows)} routes: the technical `seek_full_text` count falls "
        f"from {original_routes['seek_full_text']} to {route_counts['seek_full_text']}. "
        "Metadata-protection routes were preserved.\n\n"
        "## Manual triage, not a new eligibility rule\n\n"
        f"There are {len(candidates)} original positive-causal routes. The first manual "
        f"title/abstract queue has {queues['priority_1_textually_focused']} records: "
        "five-of-five stable fields, an aging-process anchor in the title, and an "
        "explicit current-report multi-omics label. The remaining queues are retained "
        "for later review and are not excluded: "
        f"priority 2={queues['priority_2_aging_title']}, priority 3="
        f"{queues['priority_3_explicit_multiomics']}, priority 4="
        f"{queues['priority_4_broad_candidate']}, and unstable-positive="
        f"{queues['retain_for_manual_title_abstract_adjudication']}.\n\n"
        "`candidate_triage.csv` contains the abstract and exact audit fields for manual "
        "title/abstract review. `criterion_path_route_changes.csv` contains the 330 "
        "routing corrections. The priority labels organize workload only; they neither "
        "validate accuracy nor justify automatic exclusion.\n",
        encoding="utf-8",
    )
    print(json.dumps(report["records"], sort_keys=True))
    print(json.dumps(report["positive_causal_candidates"], sort_keys=True))


if __name__ == "__main__":
    main()
