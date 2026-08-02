#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCOPE_FIELDS = (
    "report_type",
    "bio_health_scope",
    "aging_process_relevance",
    "multiomics_evidence",
    "current_report_layer_use",
)
CAUSAL_FIELDS = (
    "current_report_application",
    "causal_basis",
    "design_families",
    "causal_information_sufficiency",
)
POSITIVE_BASES = {
    "named_causal_effect_design",
    "formal_directed_hypothesis",
    "causal_analysis_method_unspecified",
}
NEGATIVE_BASES = {
    "association_or_prediction_only",
    "causal_wording_only",
    "none",
}
OUTPUT_FIELDS = (
    "record_id",
    "doi",
    "title",
    "proposed_design_family",
    "ai_empirical_primary",
    "ai_bio_health_scope",
    "ai_aging_eligible",
    "ai_multiomics_eligible",
    "ai_causal_method_eligible",
    "ai_preliminary_status",
    "ai_first_failed_criterion",
    "model_route",
    "model_exclusion_code",
    "report_type_consensus",
    "aging_relevance_consensus",
    "multiomics_evidence_consensus",
    "current_layer_use_consensus",
    "layer_candidates_consensus",
    "causal_basis_consensus",
    "design_families_consensus",
    "causal_information_sufficiency_consensus",
    "scope_all_tracked_5_of_5",
    "causal_all_tracked_5_of_5",
    "all_assessed_fields_5_of_5",
    "evidence_spans_json",
    "human_expert_status",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def stable_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def consensus(runs: list[dict[str, Any]] | None, field: str) -> Any:
    if not runs:
        return "not_assessed"
    values = [run.get(field) for run in runs]
    return values[0] if len({stable_key(value) for value in values}) == 1 else "disagreement"


def exact(runs: list[dict[str, Any]] | None, fields: tuple[str, ...]) -> bool | None:
    if not runs:
        return None
    return all(consensus(runs, field) != "disagreement" for field in fields)


def yes_no_unclear(value: Any) -> str:
    return value if value in {"yes", "no"} else "unclear"


def criterion_values(
    scope_runs: list[dict[str, Any]],
    causal_runs: list[dict[str, Any]] | None,
) -> dict[str, str]:
    report = consensus(scope_runs, "report_type")
    empirical = (
        "yes"
        if report == "empirical_primary"
        else "no"
        if report == "nonempirical"
        else "unclear"
    )
    bio = yes_no_unclear(consensus(scope_runs, "bio_health_scope"))
    aging = yes_no_unclear(consensus(scope_runs, "aging_process_relevance"))
    multiomics = consensus(scope_runs, "multiomics_evidence")
    layer_use = consensus(scope_runs, "current_report_layer_use")
    if multiomics in {"explicit_multiomics", "two_or_more_layers"} and layer_use == "yes":
        multiomics_eligible = "yes"
    elif multiomics == "single_or_no_layer" or layer_use == "no":
        multiomics_eligible = "no"
    else:
        multiomics_eligible = "unclear"

    basis = consensus(causal_runs, "causal_basis")
    application = consensus(causal_runs, "current_report_application")
    sufficiency = consensus(causal_runs, "causal_information_sufficiency")
    if basis in POSITIVE_BASES and application == "yes":
        causal = "yes"
    elif basis in NEGATIVE_BASES and sufficiency == "sufficient":
        causal = "no"
    else:
        causal = "unclear"
    return {
        "EC1": empirical,
        "EC2": bio,
        "EC3": aging,
        "EC4": multiomics_eligible,
        "EC5": causal,
    }


def display(value: Any) -> str:
    if isinstance(value, list):
        return ";".join(str(item) for item in value)
    return str(value)


def load_results(runs_dir: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    results = []
    attempt_counts: Counter[str] = Counter()
    for path in sorted(runs_dir.glob("shard_*/screening_results.jsonl")):
        with path.open(encoding="utf-8") as handle:
            results.extend(json.loads(line) for line in handle if line.strip())
    for path in sorted(runs_dir.glob("shard_*/raw_provider_responses.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                attempt_counts[f"attempt_{row.get('status', 'unknown')}"] += 1
                if int(row.get("attempt", 1)) > 1:
                    attempt_counts["retry_attempts"] += 1
    return results, dict(attempt_counts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize repeated-run AI annotations without creating gold labels"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("runs_dir", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("output_summary", type=Path)
    parser.add_argument("--allow-superseded", action="store_true")
    args = parser.parse_args()

    inputs = {row["record_id"]: row for row in read_csv(args.input)}
    results, attempt_counts = load_results(args.runs_dir)
    results_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        results_by_id[result["record_id"]].append(result)
    duplicate_result_ids = sorted(
        record_id for record_id, items in results_by_id.items() if len(items) > 1
    )
    preferred_results = {
        record_id: max(
            items,
            key=lambda row: (
                row.get("role_runs") is not None,
                row.get("final_decision") != "manual_review",
            ),
        )
        for record_id, items in results_by_id.items()
    }
    missing = sorted(set(inputs) - set(preferred_results))
    unexpected = sorted(set(preferred_results) - set(inputs))
    if missing or (unexpected and not args.allow_superseded):
        raise SystemExit(
            f"Result coverage mismatch: missing={len(missing)} unexpected={len(unexpected)}"
        )
    results = [
        row for record_id, row in preferred_results.items() if record_id in inputs
    ]

    output_rows = []
    field_stability = {
        "scope_reviewer": {
            field: {"assessed": 0, "exact_5_of_5": 0} for field in SCOPE_FIELDS
        },
        "causal_method_reviewer": {
            field: {"assessed": 0, "exact_5_of_5": 0} for field in CAUSAL_FIELDS
        },
    }
    for result in sorted(results, key=lambda row: row["record_id"]):
        source = inputs[result["record_id"]]
        role_runs = result.get("role_runs") or {}
        scope_runs = role_runs.get("scope_reviewer") or []
        causal_runs = role_runs.get("causal_method_reviewer")
        for role, runs, fields in (
            ("scope_reviewer", scope_runs, SCOPE_FIELDS),
            ("causal_method_reviewer", causal_runs, CAUSAL_FIELDS),
        ):
            if not runs:
                continue
            for field in fields:
                field_stability[role][field]["assessed"] += 1
                field_stability[role][field]["exact_5_of_5"] += (
                    consensus(runs, field) != "disagreement"
                )
        criteria = criterion_values(scope_runs, causal_runs)
        first_failed = next(
            (
                criterion
                for criterion in ("EC1", "EC2", "EC3", "EC4", "EC5")
                if criteria[criterion] == "no"
            ),
            "none",
        )
        status = (
            "preliminary_exclude"
            if first_failed != "none"
            else "preliminary_include"
            if all(value == "yes" for value in criteria.values())
            else "preliminary_unclear"
        )
        scope_exact = exact(scope_runs, SCOPE_FIELDS)
        causal_exact = exact(causal_runs, CAUSAL_FIELDS)
        assessed_exact = scope_exact is True and causal_exact in {True, None}
        selected = result.get("selected_criteria") or {}
        output_rows.append(
            {
                "record_id": result["record_id"],
                "doi": source.get("doi", ""),
                "title": source.get("title", ""),
                "proposed_design_family": source.get("proposed_design_family", ""),
                "ai_empirical_primary": criteria["EC1"],
                "ai_bio_health_scope": criteria["EC2"],
                "ai_aging_eligible": criteria["EC3"],
                "ai_multiomics_eligible": criteria["EC4"],
                "ai_causal_method_eligible": criteria["EC5"],
                "ai_preliminary_status": status,
                "ai_first_failed_criterion": first_failed,
                "model_route": result.get("final_decision", ""),
                "model_exclusion_code": result.get("final_exclusion_code", ""),
                "report_type_consensus": display(consensus(scope_runs, "report_type")),
                "aging_relevance_consensus": display(
                    consensus(scope_runs, "aging_process_relevance")
                ),
                "multiomics_evidence_consensus": display(
                    consensus(scope_runs, "multiomics_evidence")
                ),
                "current_layer_use_consensus": display(
                    consensus(scope_runs, "current_report_layer_use")
                ),
                "layer_candidates_consensus": display(
                    consensus(scope_runs, "layer_candidates")
                ),
                "causal_basis_consensus": display(consensus(causal_runs, "causal_basis")),
                "design_families_consensus": display(
                    consensus(causal_runs, "design_families")
                ),
                "causal_information_sufficiency_consensus": display(
                    consensus(causal_runs, "causal_information_sufficiency")
                ),
                "scope_all_tracked_5_of_5": str(scope_exact).lower(),
                "causal_all_tracked_5_of_5": (
                    "not_assessed" if causal_exact is None else str(causal_exact).lower()
                ),
                "all_assessed_fields_5_of_5": str(assessed_exact).lower(),
                "evidence_spans_json": json.dumps(
                    selected.get("evidence_spans", []), ensure_ascii=False
                ),
                "human_expert_status": "pending",
            }
        )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)

    status_counts = Counter(row["ai_preliminary_status"] for row in output_rows)
    exclusion_counts = Counter(
        row["ai_first_failed_criterion"]
        for row in output_rows
        if row["ai_first_failed_criterion"] != "none"
    )
    family_status: dict[str, Counter[str]] = defaultdict(Counter)
    for row in output_rows:
        family_status[row["proposed_design_family"]][row["ai_preliminary_status"]] += 1
    stable_count = sum(
        row["all_assessed_fields_5_of_5"] == "true" for row in output_rows
    )
    for role in field_stability.values():
        for values in role.values():
            assessed = values["assessed"]
            values["rate"] = values["exact_5_of_5"] / assessed if assessed else None
    summary = {
        "status": "ai_preliminary_annotation_complete_not_gold",
        "model": "gpt-5.6-terra",
        "reasoning_effort": "medium",
        "runs_per_assessed_role": 5,
        "records": len(output_rows),
        "records_with_repeated_screening_attempts": duplicate_result_ids,
        "superseded_screened_record_ids": unexpected,
        "preliminary_status_counts": dict(sorted(status_counts.items())),
        "first_failed_criterion_counts": dict(sorted(exclusion_counts.items())),
        "proposed_family_by_status": {
            family: dict(sorted(counts.items()))
            for family, counts in sorted(family_status.items())
        },
        "all_assessed_fields_5_of_5_count": stable_count,
        "all_assessed_fields_5_of_5_rate": stable_count / len(output_rows),
        "field_stability": field_stability,
        "provider_attempts": attempt_counts,
        "input": {"path": str(args.input), "sha256": sha256(args.input)},
        "output": {"path": str(args.output_csv), "sha256": sha256(args.output_csv)},
        "raw_run_artifacts": [
            {
                "path": str(path),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(args.runs_dir.glob("shard_*/*.json*"))
        ],
        "gold_standard": False,
        "human_expert_status": "pending",
        "interpretation": (
            "Preliminary labels are repeated model judgments for prioritization. "
            "They are not independent expert labels and cannot satisfy the query-"
            "freeze gold-standard requirement."
        ),
    }
    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"records={len(output_rows)} statuses={dict(status_counts)} "
        f"stable={stable_count}"
    )


if __name__ == "__main__":
    main()
