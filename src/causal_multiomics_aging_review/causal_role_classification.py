from __future__ import annotations

import copy
from typing import Any

from causal_multiomics_aging_review.causal_analysis_inventory import (
    derive_causal_level,
)

ELIGIBILITY_FIELDS = (
    "current_report_attribution",
    "empirical_result",
    "aging_relevance",
    "named_causal_basis",
    "multiomics_workflow",
    "distinct_design_unit",
)

ROLE_FIELDS = {
    "eligibility": ELIGIBILITY_FIELDS,
    "design_identity": ("causal_basis", "design_family", "variation_source"),
    "review_context": ("aging_role", "multiomics_role"),
    "effect_appraisal": (
        "contrast_status",
        "assumptions_reviewability",
        "result_status",
    ),
    "validation": ("validation_strength",),
}

FAILED_CONDITION = {
    "current_report_attribution": "not_current_report",
    "empirical_result": "no_empirical_result",
    "aging_relevance": "no_aging_relevance",
    "named_causal_basis": "no_named_causal_basis",
    "multiomics_workflow": "not_multiomics_workflow",
    "distinct_design_unit": "not_distinct_design_unit",
}


def derive_eligibility(criteria: dict[str, str]) -> tuple[str, str]:
    for field in ELIGIBILITY_FIELDS:
        if criteria[field] == "no":
            return "exclude", FAILED_CONDITION[field]
    if any(criteria[field] == "unclear" for field in ELIGIBILITY_FIELDS):
        return "unclear", "insufficient_evidence"
    return "include", "none"


def filter_candidate_report(
    candidate_report: dict[str, Any], candidate_ids: list[str]
) -> dict[str, Any]:
    selected = set(candidate_ids)
    value = copy.deepcopy(candidate_report)
    value["candidates"] = [
        candidate
        for candidate in value["candidates"]
        if candidate["candidate_id"] in selected
    ]
    observed = {candidate["candidate_id"] for candidate in value["candidates"]}
    if observed != selected:
        raise ValueError(
            f"Unknown candidate IDs: {sorted(selected - observed)}"
        )
    return value


def validate_role_response(
    response: dict[str, Any],
    *,
    expected_report_id: str,
    candidate_report: dict[str, Any],
    role_id: str,
) -> list[str]:
    errors: list[str] = []
    if response.get("report_id") != expected_report_id:
        errors.append("report_id does not match the supplied report")
    expected_ids = [item["candidate_id"] for item in candidate_report["candidates"]]
    returned_ids = [item.get("candidate_id") for item in response.get("candidates", [])]
    if len(returned_ids) != len(set(returned_ids)):
        errors.append("candidate_id values must be unique")
    if set(returned_ids) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(returned_ids))
        extra = sorted(set(returned_ids) - set(expected_ids))
        errors.append(f"candidate coverage mismatch; missing={missing}, extra={extra}")
    expected_fields = {"candidate_id", *ROLE_FIELDS[role_id]}
    for index, candidate in enumerate(response.get("candidates", [])):
        if set(candidate) != expected_fields:
            errors.append(
                f"candidates[{index}] fields mismatch; "
                f"expected={sorted(expected_fields)}, observed={sorted(candidate)}"
            )
    return errors


def normalize_role_response(
    response: dict[str, Any],
    *,
    candidate_report: dict[str, Any],
    role_id: str,
) -> dict[str, Any]:
    value = copy.deepcopy(response)
    scaffold = {
        candidate["candidate_id"]: candidate
        for candidate in candidate_report["candidates"]
    }
    order = {
        candidate["candidate_id"]: index
        for index, candidate in enumerate(candidate_report["candidates"])
    }
    for candidate in value["candidates"]:
        candidate["candidate_evidence_atom_ids"] = scaffold[
            candidate["candidate_id"]
        ]["candidate_evidence_atom_ids"]
        if role_id == "eligibility":
            qualification, failed = derive_eligibility(candidate)
            candidate["python_qualification"] = qualification
            candidate["python_first_failed_condition"] = failed
    value["candidates"].sort(key=lambda item: order[item["candidate_id"]])
    return value


def combine_role_outputs(
    role_outputs: dict[str, dict[str, Any]],
    *,
    all_candidate_report: dict[str, Any],
    eligible_candidate_ids: list[str],
) -> dict[str, Any]:
    report_ids = {output["report_id"] for output in role_outputs.values()}
    if len(report_ids) != 1:
        raise ValueError(f"Role report IDs disagree: {sorted(report_ids)}")
    maps = {
        role_id: {
            candidate["candidate_id"]: candidate
            for candidate in output["candidates"]
        }
        for role_id, output in role_outputs.items()
    }
    selected = set(eligible_candidate_ids)
    combined = []
    for scaffold in all_candidate_report["candidates"]:
        candidate_id = scaffold["candidate_id"]
        eligibility = maps["eligibility"][candidate_id]
        record = {
            "candidate_id": candidate_id,
            "candidate_evidence_atom_ids": scaffold[
                "candidate_evidence_atom_ids"
            ],
            **{field: eligibility[field] for field in ELIGIBILITY_FIELDS},
            "python_qualification": eligibility["python_qualification"],
            "python_first_failed_condition": eligibility[
                "python_first_failed_condition"
            ],
        }
        if candidate_id in selected:
            for role_id in (
                "design_identity",
                "review_context",
                "effect_appraisal",
                "validation",
            ):
                for field in ROLE_FIELDS[role_id]:
                    record[field] = maps[role_id][candidate_id][field]
            record["python_derived_level"] = (
                derive_causal_level(record)
                if record["python_qualification"] == "include"
                else None
            )
        combined.append(record)
    return {"report_id": report_ids.pop(), "candidates": combined}
